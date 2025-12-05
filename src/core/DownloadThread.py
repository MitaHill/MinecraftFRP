from PySide6.QtCore import QThread, Signal
import requests
from src.utils.LogManager import get_logger

logger = get_logger()

class DownloadThread(QThread):
    """
    在后台线程下载文件，并报告进度。
    """
    download_progress = Signal(int, int)  # (bytes_received, total_bytes)
    download_finished = Signal(str)       # (filepath)
    error_occurred = Signal(str)          # (error_message)

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.is_running = True

    def run(self):
        """
        在后台执行文件下载。
        """
        logger.info(f"下载线程启动，URL: {self.url}, 保存路径: {self.save_path}")
        try:
            with requests.get(self.url, stream=True, timeout=30) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                bytes_downloaded = 0
                
                with open(self.save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if not self.is_running:
                            logger.info("下载被用户取消。")
                            self.error_occurred.emit("下载已取消。")
                            return
                        
                        f.write(chunk)
                        bytes_downloaded += len(chunk)
                        if total_size > 0:
                            self.download_progress.emit(bytes_downloaded, total_size)
            
            if self.is_running:
                logger.info(f"文件下载成功: {self.save_path}")
                self.download_finished.emit(self.save_path)

        except requests.exceptions.RequestException as e:
            error_message = f"下载更新时发生网络错误: {e}"
            logger.error(error_message)
            self.error_occurred.emit(error_message)
        except Exception as e:
            error_message = f"下载更新时发生未知错误: {e}"
            logger.error(error_message)
            self.error_occurred.emit(error_message)

    def stop(self):
        self.is_running = False
