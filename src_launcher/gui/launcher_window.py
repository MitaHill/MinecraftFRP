"""
启动器主窗口
"""
import logging
import subprocess
import sys
from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel, 
                               QPushButton, QProgressBar, QMessageBox)
from PySide6.QtCore import Qt, QTimer, QThread
from PySide6.QtGui import QFont

# 兼容打包和开发环境的导入
try:
    from core.update_checker import UpdateChecker
    from core.downloader import Downloader
except ImportError:
    from src_launcher.core.update_checker import UpdateChecker
    from src_launcher.core.downloader import Downloader

try:
    from src._version import __version__
except ImportError:
    __version__ = "0.5.32"

logger = logging.getLogger("Launcher")


class LauncherWindow(QMainWindow):
    """启动器主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MinecraftFRP 启动器")
        self.setFixedSize(500, 300)
        
        self.update_checker = UpdateChecker()
        self.downloader = None
        self.download_thread = None
        self.installer_path = None
        
        self._init_ui()
        
        # 延迟启动检查
        QTimer.singleShot(500, self._start_check)
    
    def _init_ui(self):
        """初始化UI"""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # 标题
        title = QLabel("MinecraftFRP 启动器")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        # 版本信息
        self.version_label = QLabel(f"当前版本: {__version__}")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.version_label)
        
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
        self.launch_button.clicked.connect(self._launch_app)
        layout.addWidget(self.launch_button)
        
        layout.addStretch()
    
    def _start_check(self):
        """开始检查更新"""
        logger.info("Starting update check...")
        has_update, latest_version, download_url = self.update_checker.check_update()
        
        if has_update:
            self.status_label.setText(f"发现新版本: {latest_version}")
            self._show_update_dialog(latest_version, download_url)
        else:
            self.status_label.setText("已是最新版本")
            self.launch_button.setEnabled(True)
            # 自动启动
            QTimer.singleShot(1000, self._launch_app)
    
    def _show_update_dialog(self, latest_version, download_url):
        """显示更新对话框"""
        # 读取安装信息
        install_info = self._read_install_info()
        
        if install_info:
            # 已安装，询问是否更新
            reply = QMessageBox.question(
                self,
                "发现新版本",
                f"发现新版本 {latest_version}\n当前版本 {__version__}\n\n是否开始安装？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self._start_download(download_url)
            else:
                self.launch_button.setEnabled(True)
        else:
            # 未安装，直接下载
            self._start_download(download_url)
    
    def _read_install_info(self):
        """读取安装信息"""
        try:
            data_file = Path.home() / "Documents" / "MitaHillFRP" / "install.info"
            if data_file.exists():
                return data_file.read_text(encoding='utf-8')
        except:
            pass
        return None
    
    def _start_download(self, url):
        """开始下载安装包"""
        logger.info("Starting installer download...")
        self.status_label.setText("正在下载更新...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 下载路径
        download_dir = Path.home() / "Downloads" / "MinecraftFRP"
        download_dir.mkdir(parents=True, exist_ok=True)
        save_path = download_dir / "Minecraft_FRP_Installer.exe"
        
        # 创建下载线程
        self.download_thread = QThread()
        self.downloader = Downloader()
        self.downloader.moveToThread(self.download_thread)
        
        # 连接信号
        self.downloader.progress.connect(self._on_download_progress)
        self.downloader.finished.connect(self._on_download_finished)
        self.downloader.error.connect(self._on_download_error)
        self.download_thread.started.connect(lambda: self.downloader.download(url, save_path))
        
        self.download_thread.start()
    
    def _on_download_progress(self, downloaded, total):
        """下载进度"""
        if total > 0:
            progress = int((downloaded / total) * 100)
            self.progress_bar.setValue(progress)
            
            # 显示MB
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            self.status_label.setText(f"正在下载: {downloaded_mb:.1f} MB / {total_mb:.1f} MB")
    
    def _on_download_finished(self, file_path):
        """下载完成"""
        logger.info(f"Download finished: {file_path}")
        self.download_thread.quit()
        self.download_thread.wait()
        
        self.installer_path = file_path
        self.status_label.setText("下载完成，准备安装...")
        self.progress_bar.setVisible(False)
        
        # 启动安装程序
        QTimer.singleShot(1000, self._launch_installer)
    
    def _on_download_error(self, error_msg):
        """下载错误"""
        logger.error(f"Download error: {error_msg}")
        self.download_thread.quit()
        self.download_thread.wait()
        
        QMessageBox.critical(self, "下载失败", f"下载失败: {error_msg}")
        self.status_label.setText("下载失败")
        self.launch_button.setEnabled(True)
    
    def _launch_installer(self):
        """启动安装程序"""
        if self.installer_path and Path(self.installer_path).exists():
            logger.info(f"Launching installer: {self.installer_path}")
            try:
                subprocess.Popen([self.installer_path], shell=True)
                # 关闭启动器
                QTimer.singleShot(500, self.close)
            except Exception as e:
                logger.error(f"Failed to launch installer: {e}")
                QMessageBox.critical(self, "启动失败", f"启动安装程序失败: {e}")
    
    def _launch_app(self):
        """启动主程序"""
        # 查找主程序
        app_path = self._find_app_exe()
        
        if app_path and app_path.exists():
            logger.info(f"Launching app: {app_path}")
            try:
                subprocess.Popen([str(app_path)], shell=True)
                # 关闭启动器
                QTimer.singleShot(500, self.close)
            except Exception as e:
                logger.error(f"Failed to launch app: {e}")
                QMessageBox.critical(self, "启动失败", f"启动主程序失败: {e}")
        else:
            QMessageBox.warning(self, "未找到程序", "未找到主程序，请重新安装")
    
    def _find_app_exe(self):
        """查找主程序路径"""
        # 从安装信息读取
        install_info = self._read_install_info()
        if install_info:
            install_path = Path(install_info.strip())
            app_exe = install_path / "MinecraftFRP.exe"
            if app_exe.exists():
                return app_exe
        
        # 默认路径
        default_path = Path.home() / "AppData" / "Local" / "MinecraftFRP" / "MinecraftFRP.exe"
        if default_path.exists():
            return default_path
        
        return None
