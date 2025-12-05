# updater.py
import sys
import os
import time
import subprocess
import logging
import shutil
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue

class WorkerThread(threading.Thread):
    def __init__(self, message_queue, args):
        super().__init__()
        self.queue = message_queue
        self.args = args

    def run(self):
        pid, old_exe, new_exe, log_dir = self.args
        self.log_and_put(f"更新工作线程已启动。")
        self.log_and_put(f"等待进程 PID: {pid}")
        self.log_and_put(f"旧执行文件: {old_exe}")
        self.log_and_put(f"新执行文件: {new_exe}")

        if not self._wait_for_process_exit(pid):
            return # Stop on failure

        if not self._replace_files(old_exe, new_exe):
            return # Stop on failure

        self._relaunch_app(old_exe)
        
        self.put_status("更新完成！本窗口将在3秒后关闭。")
        self.log_and_put("更新流程结束。")
        self.queue.put(("CLOSE", ""))

    def _is_pid_running(self, pid):
        """Check if a process with the given PID is running on Windows."""
        try:
            # Use tasklist command to check for the PID
            command = f'tasklist /FI "PID eq {pid}"'
            output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.DEVNULL)
            # If the output contains the pid, the process is running.
            return pid in output
        except (subprocess.CalledProcessError, FileNotFoundError):
            # If command fails or not found, assume process is not running or we can't check.
            return False

    def _wait_for_process_exit(self, pid):
        self.put_status(f"正在等待主程序 (PID: {pid}) 关闭...")
        self.put_progress(10)
        wait_time = 30  # 30 seconds timeout
        wait_start = time.time()

        # First, wait for the PID to disappear
        while self._is_pid_running(pid):
            if time.time() - wait_start > wait_time:
                self.log_and_put(f"等待进程 {pid} 关闭超时！", level="error")
                self.put_status("错误：主程序关闭超时！")
                return False
            self.log_and_put(f"等待主程序(PID: {pid})完全退出...")
            time.sleep(1)
            self.put_progress(10 + int(20 * (time.time() - wait_start) / wait_time))

        self.log_and_put(f"进程 {pid} 已退出。确认文件锁已释放...")

        # Then, confirm the file lock is released
        wait_start = time.time() # Reset timer for file lock
        while time.time() - wait_start < wait_time:
            try:
                # Try to open for writing to check the lock
                with open(old_exe, "a+"):
                    pass
                self.log_and_put("文件锁已释放。")
                self.put_progress(40)
                return True
            except IOError:
                self.log_and_put("等待文件锁释放...")
                time.sleep(1)
            except FileNotFoundError:
                self.log_and_put("旧文件未找到，直接继续。")
                self.put_progress(40)
                return True

        self.log_and_put("等待文件锁释放超时！", level="error")
        self.put_status("错误：文件锁超时！")
        return False
        
    def _replace_files(self, old_exe, new_exe):
        self.put_status("正在替换文件...")
        self.log_and_put(f"开始文件替换流程...")
        self.put_progress(50)

        bak_exe = old_exe + ".bak"

        # 1. Backup old file
        if os.path.exists(old_exe):
            self.log_and_put(f"备份 {old_exe} -> {bak_exe}")
            try:
                shutil.move(old_exe, bak_exe)
            except Exception as e:
                self.log_and_put(f"备份失败: {e}", level="error")
                self.put_status("错误：备份旧版本失败！")
                return False
        
        self.put_progress(65)

        # 2. Move new file
        self.log_and_put(f"移动 {new_exe} -> {old_exe}")
        try:
            shutil.move(new_exe, old_exe)
            self.log_and_put("文件替换成功。")
            self.put_progress(80)
        except Exception as e:
            self.log_and_put(f"文件替换失败: {e}", level="error")
            self.put_status("错误：无法替换为新版本！")
            # Attempt to rollback
            if os.path.exists(bak_exe):
                self.log_and_put("正在尝试回滚...")
                try:
                    shutil.move(bak_exe, old_exe)
                    self.log_and_put("回滚成功。")
                    self.put_status("错误：已回滚至旧版本。")
                except Exception as rollback_e:
                    self.log_and_put(f"回滚失败: {rollback_e}", level="error")
                    self.put_status("致命错误：无法恢复旧版本！")
            return False

        # 3. Clean up backup
        if os.path.exists(bak_exe):
            self.log_and_put(f"清理备份文件 {bak_exe}")
            try:
                os.remove(bak_exe)
            except Exception as e:
                self.log_and_put(f"无法删除备份文件 (可忽略): {e}", level="warn")
        
        return True

    def _relaunch_app(self, old_exe):
        self.put_status("正在重启新版本...")
        self.log_and_put("重启应用程序...")
        self.put_progress(90)
        try:
            DETACHED_PROCESS = 0x00000008
            subprocess.Popen([old_exe], creationflags=DETACHED_PROCESS, close_fds=True)
            self.log_and_put("新版本已成功启动。")
            self.put_progress(100)
        except Exception as e:
            self.log_and_put(f"重启失败: {e}", level="error")
            self.put_status("错误：自动重启失败！请手动启动。")
            self.queue.put(("SHOW_RESTART_BTN", old_exe))

    def log_and_put(self, msg, level="info"):
        if level == "info":
            logging.info(msg)
        elif level == "warn":
            logging.warning(msg)
        else:
            logging.error(msg)
        self.queue.put(("LOG", msg))
    
    def put_status(self, msg):
        self.queue.put(("STATUS", msg))
    
    def put_progress(self, value):
        self.queue.put(("PROGRESS", value))


class UpdaterGui:
    def __init__(self, root, args):
        self.root = root
        self.args = args
        self.queue = queue.Queue()

        self.root.title("MinecraftFRP 更新程序")
        self.root.geometry("450x300")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Style
        self.style = ttk.Style(self.root)
        self.style.theme_use('vista')

        # Widgets
        self.status_label = ttk.Label(self.root, text="正在准备更新...", font=("Segoe UI", 12))
        self.status_label.pack(pady=(10, 5))

        self.log_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled', font=("Segoe UI", 9), height=10)
        self.log_area.pack(pady=5, padx=10, expand=True, fill='both')

        self.progress = ttk.Progressbar(self.root, orient='horizontal', mode='determinate', length=280)
        self.progress.pack(pady=(5, 10))
        
        self.manual_restart_btn = ttk.Button(self.root, text="手动启动", command=self.manual_restart)
        self.restart_path = ""
        # The button is hidden by default and will be shown on failure using pack()

    def manual_restart(self):
        if self.restart_path and os.path.exists(self.restart_path):
            DETACHED_PROCESS = 0x00000008
            subprocess.Popen([self.restart_path], creationflags=DETACHED_PROCESS, close_fds=True)
            self.root.after(1000, self.on_close)

    def start_update(self):
        self.worker = WorkerThread(self.queue, self.args)
        self.worker.start()
        self.root.after(100, self.process_queue)

    def process_queue(self):
        try:
            while True:
                msg_type, msg_text = self.queue.get_nowait()
                if msg_type == "LOG":
                    self.log_area.configure(state='normal')
                    self.log_area.insert(tk.END, str(msg_text) + '\n')
                    self.log_area.configure(state='disabled')
                    self.log_area.see(tk.END)
                elif msg_type == "STATUS":
                    self.status_label.config(text=str(msg_text))
                elif msg_type == "PROGRESS":
                    self.progress['value'] = msg_text
                elif msg_type == "SHOW_RESTART_BTN":
                    self.restart_path = msg_text
                    self.manual_restart_btn.pack(pady=5)
                    self.progress.pack_forget() # Hide progress bar
                elif msg_type == "CLOSE":
                    self.root.after(3000, self.on_close) # Wait 3s before closing
                    return
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

    def on_close(self):
        self.root.destroy()

def setup_logging(log_path):
    # Use a rotating file handler to keep log sizes in check
    handler = logging.handlers.RotatingFileHandler(log_path, maxBytes=1024 * 1024, backupCount=2) # 1MB per file, 2 backups
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

def main():
    if len(sys.argv) != 5:
        # For GUI display, it's better to show error in a dialog
        root = tk.Tk()
        root.withdraw() # Hide main window
        tk.messagebox.showerror("Updater Error", f"启动参数不足！\n用法: updater.py <pid> <old_exe> <new_exe> <log_dir>")
        return

    # Setup file logging
    log_dir = sys.argv[4]
    try:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "updater.log")
        setup_logging(log_file)
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        tk.messagebox.showerror("Updater Logging Error", f"无法设置日志文件于: {log_dir}\n错误: {e}")
        # Continue without file logging if it fails

    # Setup and run GUI
    root = tk.Tk()
    gui = UpdaterGui(root, sys.argv[1:])
    gui.start_update()
    root.mainloop()

if __name__ == "__main__":
    # Add RotatingFileHandler to the imports
    import logging.handlers
    main()
