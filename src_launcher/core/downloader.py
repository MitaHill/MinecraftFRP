"""
下载器模块
"""
import logging
import requests
from pathlib import Path
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger("Launcher")


class Downloader(QObject):
    """下载器"""
    
    progress = Signal(int, int)  # 当前字节数, 总字节数
    finished = Signal(str)  # 下载完成的文件路径
    error = Signal(str)  # 错误信息
    
    def __init__(self):
        super().__init__()
        self.download_path = None
    
    def download(self, url, save_path):
        """
        下载文件
        url: 下载地址
        save_path: 保存路径
        """
        try:
            logger.info(f"Starting download from {url}")
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.progress.emit(downloaded, total_size)
            
            logger.info(f"Download completed: {save_path}")
            self.download_path = str(save_path)
            self.finished.emit(str(save_path))
            
        except Exception as e:
            error_msg = f"Download failed: {e}"
            logger.error(error_msg)
            self.error.emit(error_msg)
