from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLabel, QScrollArea, QFrame, QApplication, QMessageBox)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCursor
from src.network.LobbyService import LobbyWorker, OnlineCountWorker, UserHeartbeatManager
from src.utils.LogManager import get_logger

logger = get_logger()

class RoomCard(QFrame):
    """单个房间展示卡片"""
    def __init__(self, room_data):
        super().__init__()
        self.setObjectName("RoomCard")  # 为QSS样式设置对象名称
        self.room_data = room_data
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)

        # 头部：房间名 + 人数
        header_layout = QHBoxLayout()
        name_label = QLabel(self.room_data.get('room_name', '未知房间'))
        name_label.setObjectName("cardTitle")
        header_layout.addWidget(name_label)
        
        header_layout.addStretch() 
        
        player_count = self.room_data.get('player_count', 0)
        max_players = self.room_data.get('max_players', 20)
        count_label = QLabel(f"{player_count}/{max_players} 人")
        count_label.setObjectName("cardPlayerCount")
        header_layout.addWidget(count_label)
        
        layout.addLayout(header_layout)

        # 详情：房主、版本、来自（IP）纵向堆叠
        version = self.room_data.get('game_version', '未知版本')
        if not version or version in ('未知版本', '1.20.1', ''):
            version = '探测中...'
        host_ip = self.room_data.get('host_ip', '***.***.***')
        host_player = self.room_data.get('host_player', 'Player')

        info_player = QLabel(f"房主: {host_player}")
        info_player.setObjectName("cardInfo")
        layout.addWidget(info_player)

        info_ver = QLabel(f"Ver: {version}")
        info_ver.setObjectName("cardInfo")
        layout.addWidget(info_ver)

        info_ip = QLabel(f"来自: {host_ip}")
        info_ip.setObjectName("cardInfo")
        layout.addWidget(info_ip)

        # 简介
        desc = self.room_data.get('description', '')
        if desc:
            desc_label = QLabel(desc)
            desc_label.setObjectName("cardDescription")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        # 底部：连接按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch() 
        
        join_btn = QPushButton("复制连接地址")
        join_btn.setCursor(QCursor(Qt.PointingHandCursor))
        join_btn.clicked.connect(self.copy_address)
        btn_layout.addWidget(join_btn)
        
        layout.addLayout(btn_layout)

    def copy_address(self):
        addr = self.room_data.get('server_addr')
        port = self.room_data.get('remote_port')
        full_addr = f"{addr}:{port}"
        QApplication.clipboard().setText(full_addr)
        QMessageBox.information(self, "已复制", f"服务器地址已复制到剪贴板：\n{full_addr}")


class LobbyTab(QWidget):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.worker = None
        self.online_worker = None
        self.heartbeat_manager = None
        self.setup_ui()
        # 延迟刷新，避免启动时卡顿
        QTimer.singleShot(1000, self.refresh_list)
        # 启动用户心跳
        QTimer.singleShot(500, self.start_heartbeat)
        # 定时刷新在线人数
        self.online_timer = QTimer(self)
        self.online_timer.timeout.connect(self.refresh_online_count)
        self.online_timer.start(10000)  # 每10秒刷新一次

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 顶部栏
        top_bar = QHBoxLayout()
        title = QLabel("正在联机的房间")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        top_bar.addWidget(title)
        
        top_bar.addStretch() 
        
        self.refresh_btn = QPushButton("🔄 刷新列表")
        self.refresh_btn.clicked.connect(self.refresh_list)
        top_bar.addWidget(self.refresh_btn)
        
        main_layout.addLayout(top_bar)

        # 滚动区域
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setSpacing(10)
        
        self.scroll.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll)

        # 底部栏：状态 + 在线人数
        bottom_bar = QHBoxLayout()
        
        self.status_label = QLabel("准备就绪")
        self.status_label.setStyleSheet("color: #666;")
        bottom_bar.addWidget(self.status_label)
        
        bottom_bar.addStretch()
        
        self.online_label = QLabel("🟢 在线人数: --")
        self.online_label.setStyleSheet("color: #2e7d32; font-weight: bold;")
        bottom_bar.addWidget(self.online_label)
        
        main_layout.addLayout(bottom_bar)

    def start_heartbeat(self):
        """启动用户心跳"""
        self.heartbeat_manager = UserHeartbeatManager(self)
        self.heartbeat_manager.start()
        # 立即获取一次在线人数
        self.refresh_online_count()

    def refresh_online_count(self):
        """刷新在线人数"""
        # 防止重入：如果上一次请求还没完成，跳过本次
        if self.online_worker and self.online_worker.isRunning():
            return

        self.online_worker = OnlineCountWorker(self)
        self.online_worker.online_count_updated.connect(self.on_online_count_updated)
        # 任务完成后自动清理
        self.online_worker.finished.connect(self.online_worker.deleteLater)
        self.online_worker.start()

    def on_online_count_updated(self, count):
        """更新在线人数显示"""
        self.online_label.setText(f"🟢 在线人数: {count}")

    def refresh_list(self):
        # 如果正在加载，直接返回
        if self.worker and self.worker.isRunning():
            return

        self.refresh_btn.setEnabled(False)
        self.status_label.setText("正在加载房间列表...")
        
        # 清空现有列表
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # 启动后台线程
        self.worker = LobbyWorker(self)
        self.worker.rooms_loaded.connect(self.on_rooms_loaded)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.finished.connect(lambda: self.refresh_btn.setEnabled(True))
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def on_rooms_loaded(self, rooms):
        if not rooms:
            self.status_label.setText("当前暂无公开房间")
            return

        for room in rooms:
            card = RoomCard(room)
            self.content_layout.addWidget(card)
        
        self.status_label.setText(f"已加载 {len(rooms)} 个房间")

    def on_error(self, msg):
        self.status_label.setText("加载失败")
        QMessageBox.warning(self, "错误", f"无法获取房间列表：\n{msg}")

    def cleanup(self):
        """清理资源"""
        if self.heartbeat_manager:
            self.heartbeat_manager.stop()
        if self.online_timer:
            self.online_timer.stop()
