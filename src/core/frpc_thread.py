import subprocess
import os
import time
from PySide6.QtCore import QThread, Signal, QMutex, QMutexLocker

class FrpcThread(QThread):
    out = Signal(str)
    warn = Signal(str)
    success = Signal()
    error = Signal(str)
    terminated = Signal()

    def __init__(self, ini_path):
        super().__init__()
        self.ini_path = ini_path
        self.p = None
        self.mutex = QMutex()
        self._stop_requested = False

    def run(self):
        si, fb = subprocess.STARTUPINFO(), subprocess.CREATE_NO_WINDOW
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            if not os.path.exists("frpc.exe"):
                self.error.emit("frpc.exe 未找到，请确保文件存在")
                return

            self.p = subprocess.Popen(
                ["frpc.exe", "-c", self.ini_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                startupinfo=si,
                creationflags=fb
            )

            for line in self.p.stdout:
                if self._stop_requested:
                    break

                line_stripped = line.strip()
                self.out.emit(line_stripped)

                if "start proxy success" in line_stripped:
                    self.success.emit()
                elif "already" in line_stripped:
                    self.warn.emit("端口已被占用，尝试重新分配端口...")

        except Exception as e:
            self.error.emit(f"运行frpc时出错: {str(e)}")
        finally:
            self._cleanup()
            self.terminated.emit()

    def stop(self):
        with QMutexLocker(self.mutex):
            self._stop_requested = True
            if self.p:
                try:
                    self.p.terminate()
                    deadline = time.time() + 1
                    while time.time() < deadline and self.p.poll() is None:
                        time.sleep(0.1)
                    if self.p.poll() is None:
                        self.p.kill()
                except Exception as e:
                    print(f"停止frpc进程时出错: {e}")
                finally:
                    self.p = None

    def _cleanup(self):
        with QMutexLocker(self.mutex):
            if self.p:
                try:
                    if self.p.poll() is None:
                        self.p.terminate()
                        deadline = time.time() + 1
                        while time.time() < deadline and self.p.poll() is None:
                            time.sleep(0.1)
                        if self.p.poll() is None:
                            self.p.kill()
                except:
                    pass
                finally:
                    self.p = None