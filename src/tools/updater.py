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
import psutil

class WorkerThread(threading.Thread):
    def __init__(self, message_queue, args):
        super().__init__()
        self.queue = message_queue
        self.args = args

    def run(self):
        pid_str, old_exe, new_exe, log_dir = self.args
        pid = int(pid_str)
        self.log_and_put("Updater worker thread started.")
        self.log_and_put(f"Waiting for process PID: {pid}")
        self.log_and_put(f"Old executable: {old_exe}")
        self.log_and_put(f"New executable: {new_exe}")

        if not self._wait_for_process_exit(pid, old_exe):
            return

        if not self._replace_files(old_exe, new_exe):
            return

        self._relaunch_app(old_exe)
        
        self.put_status("Update complete! This window will close in 3 seconds.")
        self.log_and_put("Update process finished.")
        self.queue.put(("CLOSE", ""))

    def _wait_for_process_exit(self, pid, old_exe):
        self.put_status(f"Waiting for the main application (PID: {pid}) to close...")
        self.put_progress(10)
        wait_time = 30
        wait_start = time.time()

        while psutil.pid_exists(pid):
            if time.time() - wait_start > wait_time:
                self.log_and_put(f"Timeout waiting for process {pid} to exit!", level="error")
                self.put_status("Error: Main application timed out while closing!")
                return False
            self.log_and_put(f"Waiting for main application (PID: {pid}) to exit completely...")
            time.sleep(1)
            self.put_progress(10 + int(20 * (time.time() - wait_start) / wait_time))

        self.log_and_put(f"Process {pid} has exited. Confirming file lock release...")

        wait_start = time.time()
        while time.time() - wait_start < wait_time:
            try:
                with open(old_exe, "a+"):
                    pass
                self.log_and_put("File lock has been released.")
                self.put_progress(40)
                return True
            except IOError:
                self.log_and_put("Waiting for file lock to be released...")
                time.sleep(1)
            except FileNotFoundError:
                self.log_and_put("Old file not found, proceeding directly.")
                self.put_progress(40)
                return True

        self.log_and_put("Timeout waiting for file lock release!", level="error")
        self.put_status("Error: File lock timeout!")
        return False
        
    def _replace_files(self, old_exe, new_exe):
        self.put_status("Replacing files...")
        self.log_and_put("Starting file replacement process...")
        self.put_progress(50)

        bak_exe = old_exe + ".bak"

        if os.path.exists(old_exe):
            self.log_and_put(f"Backing up {old_exe} -> {bak_exe}")
            try:
                shutil.move(old_exe, bak_exe)
            except Exception as e:
                self.log_and_put(f"Backup failed: {e}", level="error")
                self.put_status("Error: Failed to back up the old version!")
                return False
        
        self.put_progress(65)

        self.log_and_put(f"Moving {new_exe} -> {old_exe}")
        try:
            shutil.move(new_exe, old_exe)
            self.log_and_put("File replacement successful.")
            self.put_progress(80)
        except Exception as e:
            self.log_and_put(f"File replacement failed: {e}", level="error")
            self.put_status("Error: Could not replace with the new version!")
            if os.path.exists(bak_exe):
                self.log_and_put("Attempting to roll back...")
                try:
                    shutil.move(bak_exe, old_exe)
                    self.log_and_put("Rollback successful.")
                    self.put_status("Error: Rolled back to the old version.")
                except Exception as rollback_e:
                    self.log_and_put(f"Rollback failed: {rollback_e}", level="error")
                    self.put_status("Fatal Error: Could not restore the old version!")
            return False

        if os.path.exists(bak_exe):
            self.log_and_put(f"Cleaning up backup file {bak_exe}")
            try:
                os.remove(bak_exe)
            except Exception as e:
                self.log_and_put(f"Could not delete backup file (ignorable): {e}", level="warn")
        
        return True

    def _relaunch_app(self, old_exe):
        self.put_status("Relaunching the new version...")
        self.log_and_put("Relaunching application...")
        self.put_progress(90)
        try:
            DETACHED_PROCESS = 0x00000008
            subprocess.Popen([old_exe], creationflags=DETACHED_PROCESS, close_fds=True)
            self.log_and_put("New version launched successfully.")
            self.put_progress(100)
        except Exception as e:
            self.log_and_put(f"Relaunch failed: {e}", level="error")
            self.put_status("Error: Auto-relaunch failed! Please start it manually.")
            self.queue.put(("SHOW_RESTART_BTN", old_exe))

    def log_and_put(self, msg, level="info"):
        if level == "info": logging.info(msg)
        elif level == "warn": logging.warning(msg)
        else: logging.error(msg)
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

        self.root.title("MinecraftFRP Updater")
        self.root.geometry("450x300")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.style = ttk.Style(self.root)
        self.style.theme_use('vista')

        self.status_label = ttk.Label(self.root, text="Preparing to update...", font=("Segoe UI", 12))
        self.status_label.pack(pady=(10, 5))

        self.log_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled', font=("Segoe UI", 9), height=10)
        self.log_area.pack(pady=5, padx=10, expand=True, fill='both')

        self.progress = ttk.Progressbar(self.root, orient='horizontal', mode='determinate', length=280)
        self.progress.pack(pady=(5, 10))
        
        self.manual_restart_btn = ttk.Button(self.root, text="Manual Restart", command=self.manual_restart)
        self.restart_path = ""

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
                    self.progress.pack_forget()
                elif msg_type == "CLOSE":
                    self.root.after(3000, self.on_close)
                    return
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

    def on_close(self):
        self.root.destroy()

def setup_logging(log_path):
    handler = logging.handlers.RotatingFileHandler(log_path, maxBytes=1024 * 1024, backupCount=2, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

def main():
    try:
        if len(sys.argv) != 5:
            root = tk.Tk()
            root.withdraw()
            tk.messagebox.showerror("Updater Error", f"Insufficient arguments!\nUsage: updater.py <pid> <old_exe> <new_exe> <log_dir>")
            return

        log_dir = sys.argv[4]
        try:
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "updater.log")
            setup_logging(log_file)
        except Exception as e:
            root = tk.Tk()
            root.withdraw()
            tk.messagebox.showerror("Updater Logging Error", f"Could not set up log file at: {log_dir}\nError: {e}")

        root = tk.Tk()
        gui = UpdaterGui(root, sys.argv[1:])
        gui.start_update()
        root.mainloop()
    except Exception as e:
        log_path = os.path.join(sys.argv[4] if len(sys.argv) == 5 else '.', 'updater_crash.log')
        logging.basicConfig(filename=log_path, level=logging.ERROR, filemode='w', encoding='utf-8')
        logging.exception("Updater encountered a fatal error!")
        try:
            root = tk.Tk()
            root.withdraw()
            tk.messagebox.showerror("Updater Fatal Error", f"A fatal error occurred in the updater: {e}\nPlease check the updater_crash.log file.")
        except:
            pass

if __name__ == "__main__":
    import logging.handlers
    main()
