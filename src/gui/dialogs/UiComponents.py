from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLabel, QLineEdit, QTableWidget, QHeaderView)

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
        
        self.setup_buttons(layout)
        self.password_input.setFocus()
    
    def setup_buttons(self, layout):
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def get_password(self):
        return self.password_input.text()

def setup_server_management_ui(dialog):
    """设置服务器管理对话框的UI"""
    layout = QVBoxLayout(dialog)
    
    info_label = QLabel("服务器管理配置 - 管理员专用功能")
    info_label.setStyleSheet("font-weight: bold; color: #4CAF50; margin-bottom: 10px;")
    layout.addWidget(info_label)
    
    setup_action_buttons(dialog, layout)
    setup_table(dialog, layout)
    setup_table_buttons(dialog, layout)

def setup_action_buttons(dialog, layout):
    button_layout = QHBoxLayout()
    dialog.read_button = QPushButton("读取")
    dialog.read_button.clicked.connect(dialog.on_read_clicked)
    button_layout.addWidget(dialog.read_button)
    
    dialog.save_button = QPushButton("保存")
    dialog.save_button.clicked.connect(dialog.on_save_clicked)
    dialog.save_button.setEnabled(False)
    button_layout.addWidget(dialog.save_button)
    
    button_layout.addStretch()
    layout.addLayout(button_layout)

def setup_table(dialog, layout):
    dialog.server_table = QTableWidget()
    dialog.server_table.setColumnCount(4)
    dialog.server_table.setHorizontalHeaderLabels(["名称", "密钥", "地址", "端口"])
    
    header = dialog.server_table.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
    header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
    header.setSectionResizeMode(2, QHeaderView.Stretch)
    header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
    
    layout.addWidget(dialog.server_table)

def setup_table_buttons(dialog, layout):
    table_button_layout = QHBoxLayout()
    dialog.add_button = QPushButton("添加服务器")
    dialog.add_button.clicked.connect(dialog.add_server_row)
    table_button_layout.addWidget(dialog.add_button)
    
    dialog.delete_button = QPushButton("删除选中")
    dialog.delete_button.clicked.connect(dialog.delete_selected_row)
    table_button_layout.addWidget(dialog.delete_button)
    
    table_button_layout.addStretch()
    layout.addLayout(table_button_layout)
