import sys
import os
import time
import shutil
import subprocess
import logging
import psutil
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit, QProgressBar, QPushButton
from PySide6.QtCore import QThread, Signal, Qt

class UpdateWorker(QThread):
    log = Signal(str)
    status = Signal(str)
    progress = Signal(int)
    show_restart = Signal(str)
    done = Signal()

    def __init__(self, pid_str, old_exe, new_exe, log_dir):
        super().__init__()
        try:
            self.pid = int(pid_str)
        except (ValueError, TypeError):
            self.pid = None
        
        self.old_exe = str(Path(old_exe).resolve())
        self.new_exe = str(Path(new_exe).resolve())
        self.log_dir = str(Path(log_dir).resolve())
        self._last_lock_log = 0
        
        # 验证文件路径
        if not os.path.exists(self.new_exe):
            raise FileNotFoundError(f"New executable not found: {self.new_exe}")
        
        # 配置文件日志
        try:
            os.makedirs(self.log_dir, exist_ok=True)
        except Exception as e:
            print(f"Failed to create log dir: {e}")
            self.log_dir = os.path.dirname(self.new_exe)
        
        log_file = os.path.join(self.log_dir, 'updater.log')
        self.logger = logging.getLogger('UpdaterWorker')
        self.logger.setLevel(logging.INFO)
        
        # 清空旧的handlers
        self.logger.handlers.clear()
        
        # 文件handler - 自动裁剪到100KB
        try:
            handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
        except Exception as e:
            print(f"Failed to setup file logging: {e}")
            # 添加console handler作为fallback
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
        
        # 裁剪日志文件
        self._trim_log_file(log_file)

    def _trim_log_file(self, log_file):
        """裁剪日志文件到最大100KB"""
        try:
            if os.path.exists(log_file):
                size = os.path.getsize(log_file)
                max_size = 100 * 1024  # 100KB
                if size > max_size:
                    with open(log_file, 'r+', encoding='utf-8', errors='ignore') as f:
                        f.seek(max(0, size - max_size))
                        f.readline()  # 跳到完整行
                        remaining = f.read()
                        f.seek(0)
                        f.truncate()
                        f.write(remaining)
                    self.logger.info(f"Log file trimmed from {size} to {len(remaining)} bytes")
        except Exception as e:
            print(f"Log trim failed: {e}")

    def _log(self, msg, level=logging.INFO):
        """统一日志方法：同时发送到GUI和文件"""
        try:
            self.log.emit(msg)
        except:
            pass
        try:
            self.logger.log(level, msg)
        except:
            print(f"[{level}] {msg}")
    
    def run(self):
        self._log("=== Updater started ===")
        self._log(f"PID: {self.pid}, Old: {self.old_exe}, New: {self.new_exe}")
        try:
            # 验证参数
            if self.pid is None:
                self._log("Invalid PID, skipping wait", logging.WARNING)
            elif not psutil.pid_exists(self.pid):
                self._log(f"Process {self.pid} not running, continuing", logging.INFO)
            else:
                ok = self._wait_for_exit_and_unlock()
                if not ok:
                    return
            
            if not self._replace_files():
                return
            self._relaunch()
            self.done.emit()
        except Exception as e:
            msg = f"Fatal updater error: {e}"
            self._log(msg, logging.ERROR)
            import traceback
            self._log(traceback.format_exc(), logging.ERROR)
            self.status.emit("更新器发生致命错误")

    def _wait_for_exit_and_unlock(self):
        """等待进程退出并释放文件锁"""
        if self.pid is None or not psutil.pid_exists(self.pid):
            self._log("No need to wait for process exit")
            self.progress.emit(40)
            return True
            
        self.status.emit(f"等待主程序退出 (PID: {self.pid})...")
        self._log(f"Waiting for process {self.pid} to exit...")
        self.progress.emit(10)
        
        start = time.time()
        timeout = 15
        log_interval = 2
        last_log = 0
        
        while psutil.pid_exists(self.pid):
            elapsed = time.time() - start
            if elapsed > timeout:
                self._log(f"Timeout {timeout}s, force killing PID {self.pid}", logging.WARNING)
                try:
                    p = psutil.Process(self.pid)
                    # 先尝试优雅终止
                    p.terminate()
                    try:
                        p.wait(timeout=3)
                        self._log("Process terminated gracefully")
                    except psutil.TimeoutExpired:
                        # 强制杀死
                        for c in p.children(recursive=True):
                            try:
                                c.kill()
                            except:
                                pass
                        p.kill()
                        p.wait(timeout=3)
                        self._log("Process force killed")
                except psutil.NoSuchProcess:
                    self._log("Process already gone")
                except Exception as e:
                    self._log(f"Force kill failed: {e}", logging.ERROR)
                break
            
            if elapsed - last_log >= log_interval:
                self._log(f"等待主程序退出... ({int(elapsed)}s/{timeout}s)")
                last_log = elapsed
            
            time.sleep(0.5)
            self.progress.emit(10 + int(20 * min(elapsed / timeout, 1.0)))
        
        # 等待文件锁释放
        self._log("Process exited, checking file lock...")
        self.status.emit("等待文件锁释放...")
        start = time.time()
        lock_timeout = 20
        last_lock_log = 0
        
        while time.time() - start < lock_timeout:
            try:
                # 测试是否能打开文件
                if os.path.exists(self.old_exe):
                    with open(self.old_exe, 'r+b') as f:
                        pass  # 只测试能否打开
                self._log("File lock released")
                self.progress.emit(40)
                time.sleep(0.5)  # 额外等待确保完全释放
                return True
            except (IOError, PermissionError) as e:
                elapsed = time.time() - start
                if elapsed - last_lock_log >= 3:  # 每3秒记录一次
                    self._log(f"等待文件锁释放... ({int(elapsed)}s/{lock_timeout}s)")
                    last_lock_log = elapsed
                time.sleep(0.5)
            except FileNotFoundError:
                self._log("Old file not found, continuing")
                self.progress.emit(40)
                return True
            except Exception as e:
                self._log(f"Unexpected error checking lock: {e}", logging.WARNING)
                time.sleep(0.5)
        
        self._log("File lock timeout", logging.ERROR)
        self.status.emit("文件锁超时，尝试强制替换")
        # 即使超时也继续尝试
        time.sleep(2)
        return True  # 改为继续尝试而不是失败

    def _replace_files(self):
        """替换文件，带重试机制"""
        self.status.emit("替换文件...")
        self._log("Starting file replacement...")
        self.progress.emit(50)
        
        bak = self.old_exe + ".bak"
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # 备份旧文件
                if os.path.exists(self.old_exe):
                    if os.path.exists(bak):
                        try:
                            os.remove(bak)
                        except:
                            pass
                    shutil.move(self.old_exe, bak)
                    self._log(f"Backed up to {bak}")
                
                self.progress.emit(65)
                
                # 移动新文件到目标位置
                shutil.move(self.new_exe, self.old_exe)
                self._log("File replacement successful")
                self.progress.emit(80)
                
                # 验证新文件
                if not os.path.exists(self.old_exe):
                    raise FileNotFoundError("Replacement failed: new file not in place")
                
                # 删除备份
                if os.path.exists(bak):
                    try:
                        os.remove(bak)
                        self._log("Backup removed")
                    except Exception as e:
                        self._log(f"Failed to remove backup: {e}", logging.WARNING)
                
                return True
                
            except Exception as e:
                self._log(f"Replacement attempt {attempt + 1}/{max_retries} failed: {e}", logging.ERROR)
                
                if attempt < max_retries - 1:
                    self._log(f"Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    # 最后一次尝试失败，回滚
                    self.status.emit("替换失败，尝试回滚")
                    try:
                        if os.path.exists(bak) and not os.path.exists(self.old_exe):
                            shutil.move(bak, self.old_exe)
                            self._log("Rollback successful")
                        elif os.path.exists(bak):
                            self._log("Old file exists, backup retained for safety")
                    except Exception as re:
                        self._log(f"Rollback failed: {re}", logging.ERROR)
                    return False
        
        return False

    def _relaunch(self):
        """重新启动应用程序"""
        self.status.emit("重新启动新版本...")
        self._log("Attempting to relaunch application...")
        
        if not os.path.exists(self.old_exe):
            self._log(f"Cannot relaunch: file not found {self.old_exe}", logging.ERROR)
            self.show_restart.emit(self.old_exe)
            return
        
        try:
            # Windows 分离进程标志
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            
            # 启动新进程
            subprocess.Popen(
                [self.old_exe],
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                close_fds=True,
                cwd=os.path.dirname(self.old_exe)
            )
            self._log("Application relaunched successfully")
            self.progress.emit(100)
            time.sleep(1)  # 给新进程一点启动时间
            
        except Exception as e:
            self._log(f"Auto relaunch failed: {e}", logging.ERROR)
            import traceback
            self._log(traceback.format_exc(), logging.ERROR)
            self.show_restart.emit(self.old_exe)

class UpdaterWindow(QWidget):
    def __init__(self, args):
        super().__init__()
        self.setWindowTitle("MinecraftFRP 更新器")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.resize(550, 380)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.status = QLabel("准备更新...")
        self.status.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.status)
        
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("background-color: #f5f5f5; font-family: Consolas, monospace; font-size: 10px;")
        layout.addWidget(self.log)
        
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        layout.addWidget(self.progress)
        
        self.restart_btn = QPushButton("手动重启应用程序")
        self.restart_btn.hide()
        self.restart_btn.clicked.connect(self.manual_restart)
        self.restart_btn.setStyleSheet("padding: 8px; font-size: 12px;")
        layout.addWidget(self.restart_btn)
        
        # 验证参数
        if len(args) != 4:
            self.append_log(f"错误：参数不足 (需要4个，得到{len(args)})")
            self.status.setText("参数错误")
            return
        
        pid, old_exe, new_exe, log_dir = args
        
        # 验证文件存在
        if not os.path.exists(new_exe):
            self.append_log(f"错误：新版本文件不存在: {new_exe}")
            self.status.setText("新版本文件缺失")
            return
        
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception as e:
            self.append_log(f"警告：无法创建日志目录: {e}")
        
        try:
            self.worker = UpdateWorker(pid, old_exe, new_exe, log_dir)
            self.worker.log.connect(self.append_log)
            self.worker.status.connect(self.status.setText)
            self.worker.progress.connect(self.progress.setValue)
            self.worker.show_restart.connect(self.enable_restart)
            self.worker.done.connect(self.finish)
            self.worker.start()
        except Exception as e:
            self.append_log(f"启动更新失败: {e}")
            import traceback
            self.append_log(traceback.format_exc())
            self.status.setText("更新器启动失败")
        
    def append_log(self, m):
        """添加日志并自动裁剪"""
        try:
            self.log.append(m)
            # 自动裁剪日志，最大100K字符
            max_chars = 100_000
            cur = len(self.log.toPlainText())
            if cur > max_chars:
                excess = cur - max_chars
                doc = self.log.document()
                cursor = self.log.textCursor()
                cursor.movePosition(cursor.Start)
                cursor.movePosition(cursor.Right, cursor.KeepAnchor, excess)
                cursor.removeSelectedText()
                # 滚动到底部
                self.log.moveCursor(cursor.End)
        except Exception as e:
            print(f"Log append failed: {e}")
    
    def enable_restart(self, path):
        """显示手动重启按钮"""
        self.restart_path = path
        self.restart_btn.show()
        self.progress.hide()
        self.status.setText("自动启动失败，请手动重启")
    
    def manual_restart(self):
        """手动重启应用"""
        try:
            if not os.path.exists(self.restart_path):
                self.append_log(f"错误：文件不存在 {self.restart_path}")
                return
            
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            subprocess.Popen(
                [self.restart_path],
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                close_fds=True,
                cwd=os.path.dirname(self.restart_path)
            )
            self.append_log("应用已启动")
            time.sleep(0.5)
            self.close()
        except Exception as e:
            self.append_log(f"手动重启失败: {e}")
            import traceback
            self.append_log(traceback.format_exc())
    
    def finish(self):
        """更新完成"""
        self.status.setText("更新完成，窗口将关闭...")
        self.append_log("=== 更新完成 ===")
        QThread.msleep(1000)
        self.close()

def main():
    """更新器入口"""
    if len(sys.argv) != 5:
        print("Usage: updater.exe <pid> <old_exe> <new_exe> <log_dir>")
        print(f"Got {len(sys.argv) - 1} arguments: {sys.argv[1:]}")
        input("Press Enter to exit...")
        sys.exit(2)
    
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("MinecraftFRP Updater")
        
        w = UpdaterWindow(sys.argv[1:])
        w.show()
        
        sys.exit(app.exec())
    except Exception as e:
        print(f"Updater fatal error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == '__main__':
    main()
