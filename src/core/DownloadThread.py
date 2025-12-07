from PySide6.QtCore import QThread, Signal
import urllib.request
import ssl
from src.utils.LogManager import get_logger

logger = get_logger()

class DownloadThread(QThread):
    """
    在后台线程下载文件，并报告进度。
    使用 urllib 以获得更好的兼容性。
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
            # 创建不验证证书的 SSL 上下文
            unverified_context = ssl._create_unverified_context()
            
            with urllib.request.urlopen(self.url, context=unverified_context, timeout=30) as response:
                if response.getcode() != 200:
                    raise urllib.error.URLError(f"服务器返回状态码 {response.getcode()}")

                total_size = int(response.headers.get('content-length', 0))
                bytes_downloaded = 0
                chunk_size = 8192

                with open(self.save_path, 'wb') as f:
                    while self.is_running:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        
                        f.write(chunk)
                        bytes_downloaded += len(chunk)
                        if total_size > 0:
                            self.download_progress.emit(bytes_downloaded, total_size)
            
            if self.is_running:
                logger.info(f"文件下载成功: {self.save_path}")
                self.download_finished.emit(self.save_path)
            else:
                logger.info("下载被用户取消。")
                self.error_occurred.emit("下载已取消。")

        except Exception as e:
            error_message = f"下载更新时发生错误: {e}"
            logger.error(error_message)
            self.error_occurred.emit(error_message)

    def stop(self):
        self.is_running = False
