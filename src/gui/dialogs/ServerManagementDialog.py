import time
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QTableWidgetItem, QMessageBox, QProgressDialog

from src.utils.ssh_manager import ServerManagementConfig
from src.gui.dialogs.ui_components import PasswordDialog, setup_server_management_ui
from src.gui.dialogs.threads import ServerListDownloadThread, ServerListUploadThread
from src.gui.dialogs.data_handler import load_and_decrypt_server_list, save_and_upload_server_list

class ServerManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ServerManagementConfig()
        self.last_click_time = 0
        self.server_data = []
        
        self.setWindowTitle("服务器管理配置")
        self.setModal(True)
        self.resize(600, 400)
        
        setup_server_management_ui(self)

    def on_read_clicked(self):
        if not self.check_click_timeout() or not self.verify_admin_password():
            return
        self.download_server_list()

    def on_save_clicked(self):
        if not self.check_click_timeout() or not self.verify_admin_password():
            return
        
        temp_file = save_and_upload_server_list(self)
        if temp_file:
            self.upload_server_list(temp_file)

    def check_click_timeout(self):
        current_time = time.time()
        if current_time - self.last_click_time < 3:
            QMessageBox.warning(self, "操作限制", f"请等待 {3 - (current_time - self.last_click_time):.1f} 秒")
            return False
        self.last_click_time = current_time
        return True

    def verify_admin_password(self):
        dialog = PasswordDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return False
        if not self.config_manager.verify_admin_password(dialog.get_password()):
            QMessageBox.warning(self, "验证失败", "管理员密码错误")
            return False
        return True

    def download_server_list(self):
        progress = QProgressDialog("正在下载服务器列表...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        self.download_thread = ServerListDownloadThread(self.config_manager)
        self.download_thread.finished.connect(lambda s, m: self.on_download_finished(s, m, progress))
        self.download_thread.start()

    def on_download_finished(self, success, message, progress):
        progress.close()
        if success and load_and_decrypt_server_list(self):
            self.populate_table()
            self.save_button.setEnabled(True)
            QMessageBox.information(self, "成功", "服务器列表下载并解析成功")
        else:
            QMessageBox.critical(self, "失败", message if not success else "下载成功但解析文件失败")

    def upload_server_list(self, temp_file):
        progress = QProgressDialog("正在上传服务器列表...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        self.upload_thread = ServerListUploadThread(self.config_manager, str(temp_file))
        self.upload_thread.finished.connect(lambda s, m: self.on_upload_finished(s, m, progress, temp_file))
        self.upload_thread.start()

    def on_upload_finished(self, success, message, progress, temp_file):
        progress.close()
        if temp_file.exists():
            temp_file.unlink()
        
        if success:
            QMessageBox.information(self, "成功", "服务器列表上传成功")
            self.accept()
        else:
            QMessageBox.critical(self, "上传失败", message)

    def populate_table(self):
        self.server_table.setRowCount(len(self.server_data))
        for row, server in enumerate(self.server_data):
            self.server_table.setItem(row, 0, QTableWidgetItem(server.get('name', '')))
            self.server_table.setItem(row, 1, QTableWidgetItem(server.get('token', '')))
            self.server_table.setItem(row, 2, QTableWidgetItem(server.get('host', '')))
            self.server_table.setItem(row, 3, QTableWidgetItem(str(server.get('port', 7000))))

    def add_server_row(self):
        row = self.server_table.rowCount()
        self.server_table.insertRow(row)
        for col in range(4):
            self.server_table.setItem(row, col, QTableWidgetItem(""))

    def delete_selected_row(self):
        if self.server_table.currentRow() >= 0:
            self.server_table.removeRow(self.server_table.currentRow())
