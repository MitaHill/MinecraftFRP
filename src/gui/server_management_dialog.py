"""
服务器管理配置对话框
"""

import json
import base64
import os
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                              QMessageBox, QHeaderView, QInputDialog, QProgressDialog)

from src.utils.ssh_manager import ServerManagementConfig
from src.utils.crypto import decrypt_data, encrypt_data

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

class PasswordDialog(QDialog):
    """管理员密码输入对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("管理员验证")
        self.setModal(True)
        self.setFixedSize(300, 120)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("请输入管理员密码:"))
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self.accept)
        layout.addWidget(self.password_input)
        
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.password_input.setFocus()
    
    def get_password(self):
        return self.password_input.text()

class ServerManagementDialog(QDialog):
    """服务器管理配置主对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ServerManagementConfig()
        self.last_click_time = 0
        self.server_data = []
        
        self.setWindowTitle("服务器管理配置")
        self.setModal(True)
        self.resize(600, 400)
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 说明标签
        info_label = QLabel("服务器管理配置 - 管理员专用功能")
        info_label.setStyleSheet("font-weight: bold; color: #4CAF50; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.read_button = QPushButton("读取")
        self.read_button.clicked.connect(self.on_read_clicked)
        self.read_button.setStyleSheet("QPushButton{background:#2196F3;color:#fff;padding:8px 16px;border:none;border-radius:4px;}")
        button_layout.addWidget(self.read_button)
        
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.on_save_clicked)
        self.save_button.setEnabled(False)
        self.save_button.setStyleSheet("QPushButton{background:#4CAF50;color:#fff;padding:8px 16px;border:none;border-radius:4px;}")
        button_layout.addWidget(self.save_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 服务器列表表格
        self.server_table = QTableWidget()
        self.server_table.setColumnCount(4)
        self.server_table.setHorizontalHeaderLabels(["名称", "密钥", "地址", "端口"])
        
        # 设置表格列宽
        header = self.server_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 名称
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 密钥
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # 地址
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 端口
        
        layout.addWidget(self.server_table)
        
        # 添加/删除按钮
        table_button_layout = QHBoxLayout()
        
        add_button = QPushButton("添加服务器")
        add_button.clicked.connect(self.add_server_row)
        table_button_layout.addWidget(add_button)
        
        delete_button = QPushButton("删除选中")
        delete_button.clicked.connect(self.delete_selected_row)
        table_button_layout.addWidget(delete_button)
        
        table_button_layout.addStretch()
        layout.addLayout(table_button_layout)
        
    def on_read_clicked(self):
        """读取按钮点击事件"""
        import time
        current_time = time.time()
        
        # 检查3秒内是否可以点击
        if current_time - self.last_click_time < 3:
            remaining_time = 3 - (current_time - self.last_click_time)
            QMessageBox.warning(self, "操作限制", f"请等待 {remaining_time:.1f} 秒后再试")
            return
        
        # 验证管理员密码
        password_dialog = PasswordDialog(self)
        if password_dialog.exec() != QDialog.Accepted:
            return
            
        password = password_dialog.get_password()
        if not self.config_manager.verify_admin_password(password):
            self.last_click_time = current_time
            QMessageBox.warning(self, "验证失败", "管理员密码错误")
            return
        
        # 开始下载
        self.download_server_list()
        
    def on_save_clicked(self):
        """保存按钮点击事件"""
        import time
        current_time = time.time()
        
        # 检查3秒内是否可以点击
        if current_time - self.last_click_time < 3:
            remaining_time = 3 - (current_time - self.last_click_time)
            QMessageBox.warning(self, "操作限制", f"请等待 {remaining_time:.1f} 秒后再试")
            return
        
        # 验证管理员密码
        password_dialog = PasswordDialog(self)
        if password_dialog.exec() != QDialog.Accepted:
            return
            
        password = password_dialog.get_password()
        if not self.config_manager.verify_admin_password(password):
            self.last_click_time = current_time
            QMessageBox.warning(self, "验证失败", "管理员密码错误")
            return
        
        # 保存并上传
        self.save_and_upload_server_list()
        
    def download_server_list(self):
        """下载服务器列表"""
        # 显示进度对话框
        progress = QProgressDialog("正在下载服务器列表...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        # 创建下载线程
        self.download_thread = ServerListDownloadThread(self.config_manager)
        self.download_thread.finished.connect(lambda success, msg: self.on_download_finished(success, msg, progress))
        self.download_thread.start()
        
    def on_download_finished(self, success, message, progress):
        """下载完成回调"""
        progress.close()
        
        if success:
            # 尝试读取和解密文件
            if self.load_and_decrypt_server_list():
                self.populate_table()
                self.save_button.setEnabled(True)
                QMessageBox.information(self, "成功", "服务器列表下载并解析成功")
            else:
                QMessageBox.warning(self, "错误", "下载成功但解析文件失败")
        else:
            QMessageBox.critical(self, "下载失败", message)
            
    def load_and_decrypt_server_list(self):
        """加载并解密服务器列表文件"""
        try:
            remote_file_path = Path("config/frp-server-list-remote.json")
            if not remote_file_path.exists():
                return False
                
            # 读取加密数据
            with open(remote_file_path, 'r', encoding='utf-8') as f:
                encrypted_data = f.read()
            
            # 解密数据
            decrypted_data = decrypt_data(encrypted_data, self.config_manager.encryption_key)
            if not decrypted_data:
                return False
            
            # 解析JSON
            json_data = json.loads(decrypted_data)
            self.server_data = json_data.get('servers', [])
            return True
            
        except Exception as e:
            print(f"加载解密服务器列表失败: {e}")
            return False
            
    def populate_table(self):
        """填充表格数据"""
        self.server_table.setRowCount(len(self.server_data))
        
        for row, server in enumerate(self.server_data):
            self.server_table.setItem(row, 0, QTableWidgetItem(server.get('name', '')))      # 名称
            self.server_table.setItem(row, 1, QTableWidgetItem(server.get('token', '')))     # 密钥
            self.server_table.setItem(row, 2, QTableWidgetItem(server.get('host', '')))      # 地址
            self.server_table.setItem(row, 3, QTableWidgetItem(str(server.get('port', 7000))))  # 端口
            
    def add_server_row(self):
        """添加服务器行"""
        row = self.server_table.rowCount()
        self.server_table.insertRow(row)
        self.server_table.setItem(row, 0, QTableWidgetItem(""))      # 名称
        self.server_table.setItem(row, 1, QTableWidgetItem(""))      # 密钥
        self.server_table.setItem(row, 2, QTableWidgetItem(""))      # 地址
        self.server_table.setItem(row, 3, QTableWidgetItem("7000"))  # 端口（默认7000）
        
    def delete_selected_row(self):
        """删除选中行"""
        current_row = self.server_table.currentRow()
        if current_row >= 0:
            self.server_table.removeRow(current_row)
            
    def collect_table_data(self):
        """收集表格数据"""
        servers = []
        for row in range(self.server_table.rowCount()):
            name_item = self.server_table.item(row, 0)    # 名称
            token_item = self.server_table.item(row, 1)   # 密钥
            host_item = self.server_table.item(row, 2)    # 地址
            port_item = self.server_table.item(row, 3)    # 端口
            
            if name_item and token_item and host_item and port_item:
                try:
                    port = int(port_item.text().strip()) if port_item.text().strip().isdigit() else 7000
                except (ValueError, AttributeError):
                    port = 7000
                    
                server = {
                    'name': name_item.text().strip(),
                    'token': token_item.text().strip(),
                    'host': host_item.text().strip(),
                    'port': port
                }
                if server['name'] and server['token'] and server['host']:
                    servers.append(server)
                    
        return servers
        
    def save_and_upload_server_list(self):
        """保存并上传服务器列表"""
        try:
            # 收集表格数据
            servers = self.collect_table_data()
            if not servers:
                QMessageBox.warning(self, "错误", "没有有效的服务器数据")
                return
                
            # 构造JSON数据
            json_data = {'servers': servers}
            json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
            
            # 加密数据
            encrypted_data = encrypt_data(json_str, self.config_manager.encryption_key)
            if not encrypted_data:
                QMessageBox.critical(self, "错误", "数据加密失败")
                return
            
            # 保存加密后的数据到临时文件
            temp_file = Path("config/frp-server-list-upload.json")
            temp_file.parent.mkdir(exist_ok=True)
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(encrypted_data)
            
            # 上传文件
            progress = QProgressDialog("正在上传服务器列表...", None, 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            self.upload_thread = ServerListUploadThread(self.config_manager, str(temp_file))
            self.upload_thread.finished.connect(lambda success, msg: self.on_upload_finished(success, msg, progress, temp_file))
            self.upload_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存过程中发生错误: {e}")
            
    def on_upload_finished(self, success, message, progress, temp_file):
        """上传完成回调"""
        progress.close()
        
        # 清理临时文件
        try:
            if temp_file.exists():
                temp_file.unlink()
        except:
            pass
            
        if success:
            QMessageBox.information(self, "成功", "服务器列表保存并上传成功")
            self.accept()
        else:
            QMessageBox.critical(self, "上传失败", message)