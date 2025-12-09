import sys, os, time, shutil, subprocess, logging, psutil
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit, QProgressBar, QPushButton
from PySide6.QtCore import QThread, Signal

class UpdateWorker(QThread):
    log = Signal(str)
    status = Signal(str)
    progress = Signal(int)
    show_restart = Signal(str)
    done = Signal()

    def __init__(self, pid_str, old_exe, new_exe, log_dir):
        super().__init__()
        self.pid = int(pid_str)
        self.old_exe = old_exe
        self.new_exe = new_exe
        self.log_dir = log_dir

    def run(self):
        try:
            ok = self._wait_for_exit_and_unlock()
            if not ok:
                return
            if not self._replace_files():
                return
            self._relaunch()
            self.done.emit()
        except Exception as e:
            self.log.emit(f"Fatal updater error: {e}")
            self.status.emit("更新器发生致命错误")

    def _wait_for_exit_and_unlock(self):
        self.status.emit(f"等待主程序退出 (PID: {self.pid})...")
        self.progress.emit(10)
        start = time.time(); timeout = 15
        log_interval = 2  # 每2秒记录一次日志
        last_log = 0
        
        while psutil.pid_exists(self.pid):
            elapsed = time.time() - start
            if elapsed > timeout:
                self.log.emit(f"超时 {timeout}s，强制终止进程 {self.pid}")
                try:
                    p = psutil.Process(self.pid)
                    # 先终止所有子进程
                    for c in p.children(recursive=True):
                        try:
                            c.kill()
                        except:
                            pass
                    # 强制终止主进程
                    p.kill()
                    p.wait(timeout=3)  # 等待进程真正结束
                    self.log.emit("进程已强制终止")
                except psutil.NoSuchProcess:
                    self.log.emit("进程已不存在")
                except Exception as e:
                    self.log.emit(f"强制终止失败: {e}")
                break
            
            # 控制日志频率
            if elapsed - last_log >= log_interval:
                self.log.emit(f"等待主程序退出... ({int(elapsed)}s/{timeout}s)")
                last_log = elapsed
            
            time.sleep(0.5)
            self.progress.emit(10 + int(20 * elapsed / timeout))
        self.log.emit("进程已退出，检查文件锁...")
        start = time.time(); lock_timeout = 20
        while time.time() - start < lock_timeout:
            try:
                with open(self.old_exe, 'a+'):
                    pass
                self.log.emit("文件锁已释放")
                self.progress.emit(40)
                return True
            except IOError:
                # 在50秒窗口内仅记录一次“等待文件锁释放...”以保持界面简洁
                now = time.time()
                if not hasattr(self, "_last_lock_log") or (now - getattr(self, "_last_lock_log", 0)) > 50:
                    self.log.emit("等待文件锁释放...")
                    self._last_lock_log = now
                time.sleep(0.5)
            except FileNotFoundError:
                self.log.emit("旧文件不存在，继续")
                self.progress.emit(40)
                return True
        self.log.emit("等待文件锁超时"); self.status.emit("文件锁超时")
        return False

    def _replace_files(self):
        self.status.emit("替换文件..."); self.progress.emit(50)
        bak = self.old_exe + ".bak"
        try:
            if os.path.exists(self.old_exe):
                shutil.move(self.old_exe, bak)
                self.log.emit(f"已备份到 {bak}")
            self.progress.emit(65)
            shutil.move(self.new_exe, self.old_exe)
            self.log.emit("替换成功"); self.progress.emit(80)
            if os.path.exists(bak): os.remove(bak)
            return True
        except Exception as e:
            self.log.emit(f"替换失败: {e}"); self.status.emit("替换失败，尝试回滚")
            try:
                if os.path.exists(bak): shutil.move(bak, self.old_exe)
                self.log.emit("回滚成功")
            except Exception as re:
                self.log.emit(f"回滚失败: {re}")
            return False

    def _relaunch(self):
        self.status.emit("重新启动新版本...")
        try:
            DETACHED_PROCESS = 0x00000008
            subprocess.Popen([self.old_exe], creationflags=DETACHED_PROCESS, close_fds=True)
            self.log.emit("启动成功"); self.progress.emit(100)
        except Exception as e:
            self.log.emit(f"自动重启失败: {e}"); self.show_restart.emit(self.old_exe)

class UpdaterWindow(QWidget):
    def __init__(self, args):
        super().__init__()
        self.setWindowTitle("MinecraftFRP Updater")
        self.resize(520, 360)
        layout = QVBoxLayout(self)
        self.status = QLabel("准备更新..."); layout.addWidget(self.status)
        self.log = QTextEdit(); self.log.setReadOnly(True); layout.addWidget(self.log)
        self.progress = QProgressBar(); layout.addWidget(self.progress)
        self.restart_btn = QPushButton("手动重启"); self.restart_btn.hide(); self.restart_btn.clicked.connect(self.manual_restart)
        layout.addWidget(self.restart_btn)
        pid, old_exe, new_exe, log_dir = args
        os.makedirs(log_dir, exist_ok=True)
        self.worker = UpdateWorker(pid, old_exe, new_exe, log_dir)
        self.worker.log.connect(self.append_log)
        self.worker.status.connect(self.status.setText)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.show_restart.connect(self.enable_restart)
        self.worker.done.connect(self.finish)
        self.worker.start()
        
    def append_log(self, m):
        self.log.append(m)
        # 自动裁剪日志，最大100K字符，超过则删除最旧内容
        max_chars = 100_000
        cur = len(self.log.toPlainText())
        if cur > max_chars:
            # 删除前部超出的字符
            excess = cur - max_chars
            doc = self.log.document()
            cursor = self.log.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.movePosition(cursor.Right, cursor.KeepAnchor, excess)
            cursor.removeSelectedText()
    def enable_restart(self, path):
        self.restart_path = path; self.restart_btn.show(); self.progress.hide()
    def manual_restart(self):
        try:
            DETACHED_PROCESS = 0x00000008
            subprocess.Popen([self.restart_path], creationflags=DETACHED_PROCESS, close_fds=True)
            self.close()
        except Exception as e:
            self.append_log(f"手动重启失败: {e}")
    def finish(self):
        self.status.setText("更新完成，窗口将关闭..."); QThread.msleep(500); self.close()

def main():
    if len(sys.argv) != 5:
        print("Usage: updater <pid> <old_exe> <new_exe> <log_dir>")
        sys.exit(2)
    app = QApplication(sys.argv)
    w = UpdaterWindow(sys.argv[1:])
    w.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
