"""
MinecraftFRP 安装程序 - 图形界面
v2.0 架构 - 轻量化安装器
"""
import os
import sys
import shutil
import zipfile
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QFileDialog, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont


class InstallThread(QThread):
    """安装线程，执行文件复制操作"""
    progress = Signal(int, str)  # 进度, 消息
    finished = Signal(bool, str)  # 成功/失败, 消息
    
    def __init__(self, source_dir, target_dir):
        super().__init__()
        self.source_dir = source_dir
        self.target_dir = target_dir
        
    def run(self):
        try:
            os.makedirs(self.target_dir, exist_ok=True)
            self.progress.emit(10, "创建安装目录...")
            
            self.progress.emit(20, "正在复制程序文件...")
            
            if os.path.isfile(self.source_dir) and self.source_dir.endswith('.zip'):
                with zipfile.ZipFile(self.source_dir, 'r') as zip_ref:
                    files = zip_ref.namelist()
                    total = len(files)
                    for i, file in enumerate(files):
                        zip_ref.extract(file, self.target_dir)
                        progress_pct = 20 + int((i / total) * 60)
                        self.progress.emit(progress_pct, f"解压文件 {i+1}/{total}")
            else:
                total_files = sum([len(files) for _, _, files in os.walk(self.source_dir)])
                copied = 0
                
                for root, dirs, files in os.walk(self.source_dir):
                    rel_path = os.path.relpath(root, self.source_dir)
                    target_path = os.path.join(self.target_dir, rel_path)
                    os.makedirs(target_path, exist_ok=True)
                    
                    for file in files:
                        src_file = os.path.join(root, file)
                        dst_file = os.path.join(target_path, file)
                        shutil.copy2(src_file, dst_file)
                        copied += 1
                        progress_pct = 20 + int((copied / total_files) * 60)
                        self.progress.emit(progress_pct, f"复制文件 {copied}/{total_files}")
            
            self.progress.emit(85, "创建桌面快捷方式...")
            self._create_shortcut()
            
            self.progress.emit(95, "完成安装...")
            self.finished.emit(True, "安装成功！")
            
        except Exception as e:
            self.finished.emit(False, f"安装失败：{str(e)}")
    
    def _create_shortcut(self):
        """创建桌面快捷方式"""
        try:
            import win32com.client
            desktop = Path.home() / "Desktop"
            shortcut_path = desktop / "MinecraftFRP.lnk"
            target_exe = os.path.join(self.target_dir, "Updater.exe")
            
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(str(shortcut_path))
            shortcut.TargetPath = target_exe
            shortcut.WorkingDirectory = self.target_dir
            shortcut.IconLocation = target_exe
            shortcut.Description = "MinecraftFRP 内网穿透工具"
            shortcut.save()
        except:
            pass


class InstallerWindow(QWidget):
    """安装程序主窗口"""
    
    def __init__(self, embedded_data_path=None):
        super().__init__()
        self.embedded_data_path = embedded_data_path or self._detect_embedded_data()
        self.install_thread = None
        self.init_ui()
        
    def _detect_embedded_data(self):
        """检测内嵌的安装数据"""
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
            data_path = os.path.join(base_dir, "install_data.zip")
            if os.path.exists(data_path):
                return data_path
        
        dev_data = os.path.join(os.getcwd(), "dist", "MinecraftFRP_package")
        if os.path.exists(dev_data):
            return dev_data
        
        return None
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("MinecraftFRP 安装向导")
        self.setFixedSize(500, 350)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        title = QLabel("欢迎安装 MinecraftFRP")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        desc = QLabel("MinecraftFRP 是一个专为 Minecraft 玩家设计的内网穿透工具\n"
                     "提供图形化界面，一键开启联机游戏")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: gray;")
        layout.addWidget(desc)
        
        layout.addSpacing(20)
        
        path_label = QLabel("安装位置：")
        layout.addWidget(path_label)
        
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        default_path = os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'MinecraftFRP')
        self.path_input.setText(default_path)
        path_layout.addWidget(self.path_input)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_path)
        browse_btn.setFixedWidth(80)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)
        
        layout.addSpacing(10)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.install_btn = QPushButton("安装")
        self.install_btn.setFixedSize(100, 35)
        self.install_btn.clicked.connect(self.start_install)
        btn_layout.addWidget(self.install_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedSize(100, 35)
        self.cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        if not self.embedded_data_path:
            QMessageBox.critical(self, "错误", "未找到安装数据！")
            self.install_btn.setEnabled(False)
    
    def browse_path(self):
        """浏览安装路径"""
        path = QFileDialog.getExistingDirectory(self, "选择安装位置", self.path_input.text())
        if path:
            full_path = os.path.join(path, "MinecraftFRP")
            self.path_input.setText(full_path)
    
    def start_install(self):
        """开始安装"""
        install_path = self.path_input.text().strip()
        
        if not install_path:
            QMessageBox.warning(self, "警告", "请选择安装位置")
            return
        
        if os.path.exists(install_path):
            reply = QMessageBox.question(
                self, "确认", 
                f"目录已存在：{install_path}\n是否覆盖安装？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        self.install_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.path_input.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        
        self.install_thread = InstallThread(self.embedded_data_path, install_path)
        self.install_thread.progress.connect(self.on_progress)
        self.install_thread.finished.connect(self.on_finished)
        self.install_thread.start()
    
    def on_progress(self, value, message):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def on_finished(self, success, message):
        """安装完成"""
        self.progress_bar.setValue(100)
        
        if success:
            QMessageBox.information(self, "成功", f"{message}\n\n程序已安装到：\n{self.path_input.text()}")
            self.close()
        else:
            QMessageBox.critical(self, "失败", message)
            self.install_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
            self.path_input.setEnabled(True)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = InstallerWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
