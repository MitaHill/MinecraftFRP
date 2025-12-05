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
        self.log_and_put(f"Updater worker thread started.")
        self.log_and_put(f"PID to wait for: {pid}")
        self.log_and_put(f"Old executable: {old_exe}")
        self.log_and_put(f"New executable: {new_exe}")

        # 1. Wait for main app to close
        self.put_status("正在等待主程序关闭...")
        wait_time = 30
        wait_start = time.time()
        delete_success = False
        while time.time() - wait_start < wait_time:
            try:
                os.remove(old_exe)
                delete_success = True
                self.log_and_put("主程序已关闭，旧文件已移除。")
                break
            except PermissionError:
                self.log_and_put("等待主程序释放文件锁...")
                time.sleep(1)
            except FileNotFoundError:
                delete_success = True
                self.log_and_put("旧文件未找到，直接继续。")
                break
            except Exception as e:
                self.log_and_put(f"移除旧文件时发生错误: {e}", level="error")
                self.put_status("错误！请查看日志。")
                return

        if not delete_success:
            self.log_and_put("等待主程序关闭超时！", level="error")
            self.put_status("错误！请查看日志。")
            return

        # 2. Move new executable
        self.put_status("正在替换文件...")
        self.log_and_put(f"移动 {new_exe} -> {old_exe}")
        try:
            shutil.move(new_exe, old_exe)
            self.log_and_put("文件替换成功。")
        except Exception as e:
            self.log_and_put(f"文件替换失败: {e}", level="error")
            self.put_status("错误！请查看日志。")
            return

        # 3. Relaunch application
        self.put_status("正在重启新版本...")
        self.log_and_put("重启应用程序...")
        try:
            DETACHED_PROCESS = 0x00000008
            subprocess.Popen([old_exe], creationflags=DETACHED_PROCESS, close_fds=True)
            self.log_and_put("新版本已成功启动。")
        except Exception as e:
            self.log_and_put(f"重启失败: {e}", level="error")
            self.put_status("错误！请查看日志。")
            return
        
        self.put_status("更新完成！本窗口即将关闭。")
        self.log_and_put("更新流程结束。")
        self.queue.put(("CLOSE", ""))

    def log_and_put(self, msg, level="info"):
        if level == "info":
            logging.info(msg)
        else:
            logging.error(msg)
        self.queue.put(("LOG", msg))
    
    def put_status(self, msg):
        self.queue.put(("STATUS", msg))


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

        self.log_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled', font=("Segoe UI", 9))
        self.log_area.pack(pady=5, padx=10, expand=True, fill='both')

        self.progress = ttk.Progressbar(self.root, orient='horizontal', mode='indeterminate', length=280)
        self.progress.pack(pady=(5, 10))
        self.progress.start(10)

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
                    self.log_area.insert(tk.END, msg_text + '\n')
                    self.log_area.configure(state='disabled')
                    self.log_area.see(tk.END)
                elif msg_type == "STATUS":
                    self.status_label.config(text=msg_text)
                elif msg_type == "CLOSE":
                    self.root.after(3000, self.on_close) # Wait 3s before closing
                    return
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

    def on_close(self):
        self.root.destroy()

def setup_logging(log_path):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=log_path, filemode='w')

def main():
    if len(sys.argv) != 5:
        sys.stderr.write(f"Usage: updater.py <pid> <old_exe> <new_exe> <log_dir>\n")
        return

    # Setup file logging
    log_dir = sys.argv[4]
    try:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "updater.log")
        setup_logging(log_file)
    except Exception as e:
        sys.stderr.write(f"FATAL: Could not set up logging at {log_dir}: {e}\n")
        # Continue without file logging if it fails

    # Setup and run GUI
    root = tk.Tk()
    gui = UpdaterGui(root, sys.argv[1:])
    gui.start_update()
    root.mainloop()

if __name__ == "__main__":
    main()
