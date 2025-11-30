import subprocess
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QMessageBox
from PySide6.QtCore import QTimer
from src.tools.PingManager import PingManager

class NetworkInfoDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("网络适配器信息")
        self.setMinimumSize(600, 400)
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)

    def set_info(self, html):
        self.text_area.setHtml(html)
        QTimer.singleShot(0, self.adjust_size)

    def adjust_size(self):
        doc = self.text_area.document()
        ideal_width = doc.idealWidth()
        new_width = min(ideal_width * 1.2, 800)
        current_height = 400
        self.resize(new_width, current_height)

class PingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ping 测试")
        self.setGeometry(200, 200, 400, 300)
        layout = QVBoxLayout(self)
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("输入要 Ping 的地址")
        layout.addWidget(self.address_input)
        self.ping_button = QPushButton("开始 Ping")
        self.ping_button.clicked.connect(self.start_ping)
        layout.addWidget(self.ping_button)
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)
        self.ping_manager = PingManager()

    def start_ping(self):
        address = self.address_input.text().strip()
        if not address:
            QMessageBox.warning(self, "错误", "请输入要 Ping 的地址")
            return
        result = self.ping_manager.ping(address)
        self.result_text.setPlainText(result)