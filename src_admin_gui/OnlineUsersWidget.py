from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt, QTimer
from src_admin_gui.AdminClient import AdminClient
from src_admin_gui.LogManager import get_logger
from datetime import datetime

logger = get_logger()

class OnlineUsersWidget(QWidget):
    def __init__(self, mode="tunnels"):
        super().__init__()
        self.mode = mode # 'tunnels' or 'apps'
        self.init_ui()
        # 自动刷新定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(5000) # 每5秒刷新

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        refresh_btn = QPushButton("刷新 (Refresh)")
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn)
        
        self.table = QTableWidget()
        if self.mode == 'tunnels':
            cols = ["用户IP (Client IP)", "服务器地址 (Server)", "端口 (Port)", "最后心跳 (Last Heartbeat)"]
        else:
            cols = ["用户IP (Client IP)", "最后心跳 (Last Heartbeat)"]
            
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        
    def refresh(self):
        try:
            if self.mode == 'tunnels':
                users = AdminClient.get_online_users()
            else:
                users = AdminClient.get_online_app_users()
                
            self.table.setRowCount(0)
            for user in users:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(user.get('client_ip', ''))))
                
                ts = user.get('last_heartbeat', 0)
                time_str = datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                import time
                ago = int(time.time() - ts)
                time_display = f"{time_str} ({ago}s ago)"
                
                if self.mode == 'tunnels':
                    self.table.setItem(row, 1, QTableWidgetItem(str(user.get('server_addr', ''))))
                    self.table.setItem(row, 2, QTableWidgetItem(str(user.get('remote_port', ''))))
                    self.table.setItem(row, 3, QTableWidgetItem(time_display))
                else:
                    self.table.setItem(row, 1, QTableWidgetItem(time_display))
                    
        except Exception as e:
            logger.error(f"Failed to fetch users ({self.mode}): {e}")
