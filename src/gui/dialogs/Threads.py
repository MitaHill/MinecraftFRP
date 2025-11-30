from PySide6.QtCore import QThread, Signal

class ServerListDownloadThread(QThread):
    """服务器列表下载线程"""
    finished = Signal(bool, str)
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        
    def run(self):
        try:
            success, message = self.config_manager.download_server_list()
            self.finished.emit(success, message)
        except Exception as e:
            self.finished.emit(False, f"下载线程异常: {e}")

class ServerListUploadThread(QThread):
    """服务器列表上传线程"""
    finished = Signal(bool, str)
    
    def __init__(self, config_manager, file_path):
        super().__init__()
        self.config_manager = config_manager
        self.file_path = file_path
        
    def run(self):
        try:
            success, message = self.config_manager.upload_server_list(self.file_path)
            self.finished.emit(success, message)
        except Exception as e:
            self.finished.emit(False, f"上传线程异常: {e}")
