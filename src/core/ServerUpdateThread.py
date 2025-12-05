from PySide6.QtCore import QThread, Signal
from src.core.ServerManager import ServerManager
from src.utils.LogManager import get_logger

logger = get_logger()

class ServerUpdateThread(QThread):
    """
    GUI 线程适配器：在后台线程从网络更新服务器列表。
    """
    servers_updated = Signal(dict)

    def __init__(self):
        super().__init__()

    def run(self):
        """
        在后台执行网络请求，获取最新的服务器列表。
        成功后，通过信号发送新的服务器数据。
        """
        logger.info("后台服务器列表更新线程已启动。")
        # 注意：这里我们创建一个新的 ServerManager 实例来执行网络操作，
        # 以避免与主线程中可能存在的实例发生冲突，确保线程安全。
        manager = ServerManager()
        new_servers = manager.update_servers_from_network()
        
        if new_servers:
            self.servers_updated.emit(new_servers)
            logger.info("服务器列表已在后台更新，并已发送信号。")
        else:
            logger.warning("后台更新服务器列表失败，未发送信号。")
