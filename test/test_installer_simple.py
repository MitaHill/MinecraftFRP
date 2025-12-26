"""
简化版installer测试 - 用于验证基本功能
"""
import sys
from PySide6.QtWidgets import QApplication, QMessageBox, QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt

class SimpleInstaller(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('MinecraftFRP Installer v0.5.32')
        self.setGeometry(300, 300, 500, 300)
        
        layout = QVBoxLayout()
        
        title = QLabel('Minecraft FRP 安装程序')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        info = QLabel('这是一个简化的测试版本\n用于验证installer能否正常启动')
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("margin: 20px;")
        layout.addWidget(info)
        
        btn = QPushButton('点击测试')
        btn.clicked.connect(self.test_click)
        layout.addWidget(btn)
        
        self.setLayout(layout)
    
    def test_click(self):
        QMessageBox.information(self, '成功', 'Installer窗口可以正常工作！')

def main():
    app = QApplication(sys.argv)
    window = SimpleInstaller()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
