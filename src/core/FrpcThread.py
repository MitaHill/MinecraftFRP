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
            # 标记是否已尝试删除配置文件
            config_deleted = False
            # 记录启动时间，确保进程有足够时间读取配置文件
            import time
            start_time = time.time()
            
            # 迭代 ProcessManager 生成的输出流
            for line in self.manager.run_frpc(self.ini_path):
                # 收到输出说明进程已启动，但需要延迟删除以确保配置已被读取
                # frpc 通常在启动后 2-3 秒内会读取并加载配置文件
                if not config_deleted:
                    elapsed = time.time() - start_time
                    # 至少等待 3 秒，确保 frpc 已完全启动并读取配置
                    if elapsed > 3.0:
                        try:
                            import os
                            if isinstance(self.ini_path, (str, os.PathLike)) and os.path.exists(self.ini_path):
                                os.remove(self.ini_path)
                                config_deleted = True
                                logger.info(f"配置文件已删除: {self.ini_path}")
                        except Exception as e:
                            logger.warning(f"删除配置文件失败: {e}")
                
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
            # 尝试删除临时配置文件，降低泄露风险
            try:
                import os
                if isinstance(self.ini_path, str) and os.path.exists(self.ini_path):
                    try:
                        os.chmod(self.ini_path, 0o600)
                    except Exception:
                        pass
                    os.remove(self.ini_path)
            except Exception:
                pass
            # 确保进程清理
            self.manager.stop()
            self.terminated.emit()

    def stop(self):
        """停止线程和子进程"""
        # 调用管理器的 stop 方法，这会设置标志位并尝试终止子进程
        self.manager.stop()
