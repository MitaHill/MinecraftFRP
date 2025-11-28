from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLabel, QComboBox, QLineEdit, QTextEdit)
from src.network.ping_utils import load_ping_data

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
        self.add_action_buttons(layout)
        self.add_log_area(layout)

    def add_server_selection(self, layout):
        server_layout = QHBoxLayout()
        help_button = QPushButton("帮助")
        help_button.setMaximumWidth(60)
        help_button.clicked.connect(self.parent_window.start_web_browser)
        server_layout.addWidget(help_button)

        server_layout.addWidget(QLabel("选择线路:"))
        self.server_combo = QComboBox()
        self.populate_server_combo()
        server_layout.addWidget(self.server_combo)
        layout.addLayout(server_layout)

    def populate_server_combo(self):
        saved_pings = load_ping_data() or {}
        for name in self.servers.keys():
            item_text = saved_pings.get(name, f"{name}    未测试")
            self.server_combo.addItem(item_text)

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
