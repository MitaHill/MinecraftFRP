from PySide6.QtCore import QThread, Signal
from src.core.ProcessManager import ProcessManager
from src.utils.LogManager import get_logger

logger = get_logger()

class FrpcThread(QThread):
    """
    GUI 线程适配器：管理 FRP 进程并将输出转换为 Qt 信号。
    """
    out = Signal(str)
    warn = Signal(str)
    success = Signal()
    error = Signal(str)
    terminated = Signal()

    def __init__(self, ini_path):
        super().__init__()
        self.ini_path = ini_path
        self.manager = ProcessManager()

    def run(self):
        try:
            # 迭代 ProcessManager 生成的输出流
            for line in self.manager.run_frpc(self.ini_path):
                self.out.emit(line)

                if "start proxy success" in line:
                    self.success.emit()
                elif "already" in line:
                    self.warn.emit("端口已被占用，尝试重新分配端口...")
                    
        except FileNotFoundError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"运行frpc时出错: {str(e)}")
        finally:
            # 确保进程清理
            self.manager.stop()
            self.terminated.emit()

    def stop(self):
        """停止线程和子进程"""
        # 调用管理器的 stop 方法，这会设置标志位并尝试终止子进程
        self.manager.stop()
