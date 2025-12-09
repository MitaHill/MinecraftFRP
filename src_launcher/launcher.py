"""
MinecraftFRP Launcher
启动器负责：
1. 检查更新
2. 下载新版本安装包
3. 启动安装程序（如果需要更新）
4. 启动主程序（如果已是最新版本）
"""

import sys
import os
import json
import requests
import subprocess
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                               QPushButton, QProgressBar, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

# 硬编码配置
INSTALLER_DOWNLOAD_URL = "https://z.clash.ink/chfs/shared/MinecraftFRP/lastet/Minecraft_FRP_Installer.exe"
VERSION_JSON_URL = "https://z.clash.ink/chfs/shared/MinecraftFRP/Data/version.json"

# 路径配置
DOCUMENTS_PATH = Path.home() / "Documents" / "MitaHillFRP"
CONFIG_FILE = DOCUMENTS_PATH / "install_info.json"
DOWNLOADS_PATH = DOCUMENTS_PATH / "downloads"


class UpdateChecker(QThread):
    """更新检查线程"""
    update_available = Signal(str, str)  # (new_version, current_version)
    no_update = Signal()
    error = Signal(str)
    
    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version
    
    def run(self):
        try:
            resp = requests.get(VERSION_JSON_URL, timeout=10)
            resp.raise_for_status()
            version_data = resp.json()
            remote_version = version_data.get("version", "0.0.0")
            
            if self._compare_version(remote_version, self.current_version) > 0:
                self.update_available.emit(remote_version, self.current_version)
            else:
                self.no_update.emit()
        except Exception as e:
            self.error.emit(str(e))
    
    def _compare_version(self, v1, v2):
        """比较版本号，v1 > v2 返回1，v1 < v2 返回-1，相等返回0"""
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        
        for i in range(max(len(parts1), len(parts2))):
            p1 = parts1[i] if i < len(parts1) else 0
            p2 = parts2[i] if i < len(parts2) else 0
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1
        return 0


class DownloadThread(QThread):
    """下载线程"""
    progress = Signal(int, int)  # (downloaded, total)
    finished = Signal(str)  # installer_path
    error = Signal(str)
    
    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path
    
    def run(self):
        try:
            self.save_path.parent.mkdir(parents=True, exist_ok=True)
            
            resp = requests.get(self.url, stream=True, timeout=30)
            resp.raise_for_status()
            
            total_size = int(resp.headers.get('content-length', 0))
            downloaded = 0
            
            with open(self.save_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.progress.emit(downloaded, total_size)
            
            self.finished.emit(str(self.save_path))
        except Exception as e:
            self.error.emit(str(e))


class LauncherWindow(QWidget):
    """启动器主窗口"""
    
    def __init__(self):
        super().__init__()
        self.install_info = self._load_install_info()
        self.current_version = self._get_current_version()
        self.init_ui()
        self.check_update()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("MinecraftFRP 启动器")
        self.setFixedSize(500, 300)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # 标题
        title = QLabel("MinecraftFRP 联机工具")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 状态标签
        self.status_label = QLabel("正在检查更新...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 启动按钮
        self.launch_button = QPushButton("启动程序")
        self.launch_button.setEnabled(False)
        self.launch_button.clicked.connect(self.launch_app)
        layout.addWidget(self.launch_button)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def _get_current_version(self):
        """获取当前安装的版本"""
        if self.install_info and "version" in self.install_info:
            return self.install_info["version"]
        return "0.0.0"
    
    def _load_install_info(self):
        """加载安装信息"""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def check_update(self):
        """检查更新"""
        self.checker = UpdateChecker(self.current_version)
        self.checker.update_available.connect(self.on_update_available)
        self.checker.no_update.connect(self.on_no_update)
        self.checker.error.connect(self.on_check_error)
        self.checker.start()
    
    def on_update_available(self, new_version, current_version):
        """发现新版本"""
        self.status_label.setText(f"发现新版本：{new_version} (当前：{current_version})")
        
        reply = QMessageBox.question(
            self, "更新可用", 
            f"发现新版本 {new_version}，是否立即下载更新？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.download_update(new_version)
        else:
            self.launch_button.setEnabled(True)
    
    def on_no_update(self):
        """已是最新版本"""
        self.status_label.setText(f"当前版本：{self.current_version}（已是最新）")
        self.launch_button.setEnabled(True)
    
    def on_check_error(self, error_msg):
        """检查更新失败"""
        self.status_label.setText(f"检查更新失败：{error_msg}")
        self.launch_button.setEnabled(True)
    
    def download_update(self, version):
        """下载更新"""
        self.status_label.setText("正在下载更新...")
        self.progress_bar.setVisible(True)
        
        save_path = DOWNLOADS_PATH / f"Minecraft_FRP_Installer_{version}.exe"
        
        self.downloader = DownloadThread(INSTALLER_DOWNLOAD_URL, save_path)
        self.downloader.progress.connect(self.on_download_progress)
        self.downloader.finished.connect(self.on_download_finished)
        self.downloader.error.connect(self.on_download_error)
        self.downloader.start()
    
    def on_download_progress(self, downloaded, total):
        """下载进度更新"""
        if total > 0:
            percent = int(downloaded * 100 / total)
            self.progress_bar.setValue(percent)
            size_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            self.status_label.setText(f"正在下载：{size_mb:.1f}MB / {total_mb:.1f}MB")
    
    def on_download_finished(self, installer_path):
        """下载完成，启动安装程序"""
        self.status_label.setText("下载完成，启动安装程序...")
        self.progress_bar.setVisible(False)
        
        try:
            subprocess.Popen([installer_path])
            QApplication.quit()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动安装程序失败：{e}")
    
    def on_download_error(self, error_msg):
        """下载失败"""
        self.status_label.setText(f"下载失败：{error_msg}")
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "错误", f"下载更新失败：{error_msg}")
        self.launch_button.setEnabled(True)
    
    def launch_app(self):
        """启动主程序"""
        if not self.install_info or "install_path" not in self.install_info:
            QMessageBox.warning(self, "警告", "未找到安装信息，请先安装程序。")
            return
        
        app_path = Path(self.install_info["install_path"]) / "MinecraftFRP.exe"
        
        if not app_path.exists():
            QMessageBox.critical(self, "错误", f"主程序不存在：{app_path}")
            return
        
        try:
            subprocess.Popen([str(app_path)])
            QApplication.quit()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动主程序失败：{e}")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = LauncherWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
