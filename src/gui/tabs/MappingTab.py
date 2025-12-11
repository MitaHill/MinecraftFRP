from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLabel, QComboBox, QLineEdit, QTextEdit, QGroupBox, QSpinBox, QFormLayout)
from src.network.PingUtils import load_ping_data

class MappingTab(QWidget):
    def __init__(self, parent_window, servers):
        super().__init__()
        self.parent_window = parent_window
        self.servers = servers
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        self.add_server_selection(layout)
        self.add_port_input(layout)
        self.add_lobby_settings(layout)
        self.add_action_buttons(layout)
        self.add_log_area(layout)

    def add_lobby_settings(self, layout):
        self.lobby_group = QGroupBox("发布到联机大厅")
        self.lobby_group.setCheckable(True)
        
        # Load Config
        lobby_config = self.parent_window.app_config.get("lobby", {})
        self.lobby_group.setChecked(lobby_config.get("enabled", False))
        
        form_layout = QFormLayout(self.lobby_group)
        
        self.room_name_edit = QLineEdit()
        self.room_name_edit.setPlaceholderText("给房间起个名字")
        self.room_name_edit.setText(lobby_config.get("room_name", "我的Minecraft服务器"))
        
        self.room_desc_edit = QLineEdit()
        self.room_desc_edit.setPlaceholderText("简短的介绍（可选）")
        self.room_desc_edit.setText(lobby_config.get("description", ""))
        
        self.max_players_spin = QSpinBox()
        self.max_players_spin.setRange(1, 100)
        self.max_players_spin.setValue(lobby_config.get("max_players", 10))
        
        form_layout.addRow("房间名称:", self.room_name_edit)
        form_layout.addRow("房间介绍:", self.room_desc_edit)
        form_layout.addRow("最大人数:", self.max_players_spin)
        
        layout.addWidget(self.lobby_group)

    def add_server_selection(self, layout):
        server_layout = QHBoxLayout()
        help_button = QPushButton("帮助")
        help_button.setMaximumWidth(60)
        help_button.clicked.connect(self.parent_window.start_web_browser)
        server_layout.addWidget(help_button)

        server_layout.addWidget(QLabel("选择线路:"))
        self.server_combo = QComboBox()
        self.populate_server_combo()
        self.server_combo.currentTextChanged.connect(self.parent_window.on_server_changed)
        server_layout.addWidget(self.server_combo)
        layout.addLayout(server_layout)

    def populate_server_combo(self):
        saved_pings = load_ping_data() or {}
        last_server = self.parent_window.app_config.get("settings", {}).get("last_server")
        default_index = 0
        
        for i, name in enumerate(self.servers.keys()):
            item_text = saved_pings.get(name, f"{name}    未测试")
            self.server_combo.addItem(item_text)
            
            if last_server and name == last_server:
                default_index = i
        
        self.server_combo.setCurrentIndex(default_index)

    def update_server_list(self, new_servers):
        """用新的服务器列表数据更新下拉框"""
        self.servers = new_servers
        self.server_combo.clear()
        self.populate_server_combo()

    def add_port_input(self, layout):
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("输入本地端口:"))
        self.port_edit = QLineEdit()
        self.port_edit.setPlaceholderText("1-65535")
        port_layout.addWidget(self.port_edit)
        layout.addLayout(port_layout)

    def add_action_buttons(self, layout):
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("启动映射")
        self.start_button.clicked.connect(self.parent_window.start_map)
        button_layout.addWidget(self.start_button)
        
        self.copy_button = QPushButton("复制链接")
        self.copy_button.clicked.connect(self.parent_window.copy_link)
        self.copy_button.setEnabled(False)
        button_layout.addWidget(self.copy_button)
        layout.addLayout(button_layout)

    def add_log_area(self, layout):
        layout.addWidget(QLabel("运行日志:"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        self.link_label = QLabel("映射地址: 无")
        layout.addWidget(self.link_label)
        
        self.ad_label = QLabel("准备就绪")
        self.ad_label.setOpenExternalLinks(True)
        layout.addWidget(self.ad_label)
