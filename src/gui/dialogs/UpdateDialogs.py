from PySide6.QtWidgets import QProgressDialog
from PySide6.QtCore import Qt

class UpdateDownloadDialog(QProgressDialog):
    """
    显示更新下载进度的对话框。
    """
    def __init__(self, parent=None):
        super().__init__("正在下载更新...", "取消", 0, 100, parent)
        self.setWindowTitle("正在下载")
        self.setWindowModality(Qt.WindowModal)
        self.setAutoClose(False)
        self.setAutoReset(False)
        self.setValue(0)
        
        # This will be connected to the download thread's stop method
        self.canceled.connect(self.on_cancel)
        
        self.download_thread = None

    def on_cancel(self):
        """当用户点击取消按钮时调用。"""
        if self.download_thread:
            self.download_thread.stop()
            
    def update_progress(self, bytes_received, total_bytes):
        """更新进度条。"""
        if total_bytes > 0:
            percentage = int((bytes_received / total_bytes) * 100)
            self.setValue(percentage)
        else:
            # 如果没有总大小信息，可以显示一个不确定的进度条
            # 或者只是显示已下载的字节数
            self.setLabelText(f"正在下载更新... ({bytes_received / 1024 / 1024:.2f} MB)")
