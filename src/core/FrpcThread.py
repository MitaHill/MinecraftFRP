from PySide6.QtCore import QThread, Signal
from src.core.ProcessManager import ProcessManager
from src.utils.LogManager import get_logger
import threading
import os
import time

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
        self._config_deleted = False

    def _delayed_delete_config(self):
        """延迟删除配置文件的回调函数"""
        if self._config_deleted:
            return
            
        try:
            if isinstance(self.ini_path, (str, os.PathLike)) and os.path.exists(self.ini_path):
                # 尝试安全删除
                try:
                    os.chmod(self.ini_path, 0o600)
                except Exception:
                    pass
                os.remove(self.ini_path)
                self._config_deleted = True
                logger.info(f"配置文件已安全清除 (Timer): {os.path.basename(str(self.ini_path))}")
        except Exception as e:
            logger.warning(f"延迟删除配置文件失败: {e}")

    def run(self):
        try:
            self._config_deleted = False
            
            # 启动独立线程定时器，确保无论是否有输出，3秒后都会尝试删除配置
            # 这是为了防止 frpc 启动后静默导致配置残留
            cleanup_timer = threading.Timer(3.0, self._delayed_delete_config)
            cleanup_timer.daemon = True
            cleanup_timer.start()
            
            # 迭代 ProcessManager 生成的输出流
            # 注意：如果 frpc 没有任何输出，这里会阻塞直到进程结束
            for line in self.manager.run_frpc(self.ini_path):
                self.out.emit(line)

                if "start proxy success" in line:
                    self.success.emit()
                elif "port already used" in line or "bind port error" in line: # 扩展匹配规则
                    self.warn.emit("端口已被占用，尝试重新分配端口...")
                elif "login to server failed" in line:
                    self.warn.emit("登录服务器失败，请检查网络或Token...")
                    
        except FileNotFoundError as e:
            self.error.emit(f"文件未找到: {str(e)}")
        except Exception as e:
            self.error.emit(f"运行frpc时出错: {str(e)}")
        finally:
            # 确保定时器已触发或取消（虽然 start 后 cancel 也没用，但是个好习惯）
            if 'cleanup_timer' in locals():
                cleanup_timer.cancel()
                
            # 最后一道防线：确保配置被删除
            self._delayed_delete_config()
            
            # 确保进程清理
            self.manager.stop()
            self.terminated.emit()

    def stop(self):
        """停止线程和子进程"""
        # 调用管理器的 stop 方法，这会设置标志位并尝试终止子进程
        self.manager.stop()
        # 等待线程结束
        self.wait()
