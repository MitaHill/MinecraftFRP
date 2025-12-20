from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, 
                              QLabel, QCheckBox, QMessageBox)

class SettingsTab(QWidget):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # Auto Mapping
        self.auto_mapping_checkbox = QCheckBox("自动映射")
        self.auto_mapping_checkbox.setChecked(self.parent_window.auto_mapping_enabled)
        self.auto_mapping_checkbox.stateChanged.connect(self.parent_window.on_auto_mapping_changed)
        layout.addWidget(self.auto_mapping_checkbox)
        
        auto_mapping_desc = QLabel("打开此选项后，每次检测到Minecraft端口开放时，自动将端口填入到输入框内，并根据已选择的线路自动开启映射")
        auto_mapping_desc.setWordWrap(True)
        auto_mapping_desc.setStyleSheet("color: gray; font-size: 12px; margin-left: 20px; margin-bottom: 10px;")
        layout.addWidget(auto_mapping_desc)

        # Dark Mode
        self.dark_mode_checkbox = QCheckBox("熄灭灯泡（夜间模式）")
        is_checked = self.parent_window.dark_mode_override and self.parent_window.force_dark_mode
        self.dark_mode_checkbox.setChecked(is_checked)
        self.dark_mode_checkbox.stateChanged.connect(self.parent_window.on_dark_mode_changed)
        layout.addWidget(self.dark_mode_checkbox)
        
        dark_mode_desc = QLabel("打开此选项后，将UI变为黑色（夜间模式），关闭为白色（昼间模式），并暂停自动切换昼夜UI逻辑")
        dark_mode_desc.setWordWrap(True)
        dark_mode_desc.setStyleSheet("color: gray; font-size: 12px; margin-left: 20px; margin-bottom: 10px;")
        layout.addWidget(dark_mode_desc)

        # Server Management (Hidden)
        # server_mgmt_button = QPushButton("服务器管理配置")
        # server_mgmt_button.clicked.connect(self.open_server_management)
        # layout.addWidget(server_mgmt_button)
        # 
        # server_mgmt_desc = QLabel("管理员专用功能：管理FRP服务器列表配置（需要管理员密码）")
        # server_mgmt_desc.setWordWrap(True)
        # server_mgmt_desc.setStyleSheet("color: gray; font-size: 12px; margin-left: 20px; margin-bottom: 10px;")
        # layout.addWidget(server_mgmt_desc)

        layout.addStretch()

    def open_server_management(self):
        """打开服务器管理配置对话框"""
        QMessageBox.information(self, "提示", "此功能已移至独立的管理员工具 (admin_gui.py)。")
