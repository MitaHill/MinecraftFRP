"""
安装程序主窗口
提供用户协议、安装路径选择、进度显示等功能
"""
import logging
from PySide6.QtWidgets import (QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QLineEdit, QFileDialog,
                               QTextBrowser, QProgressBar, QCheckBox, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from pathlib import Path

logger = logging.getLogger(__name__)

class InstallThread(QThread):
    """安装线程"""
    progress = Signal(int, int, str)  # current, total, message
    finished = Signal(bool, str)  # success, error_message
    
    def __init__(self, install_manager, install_path, zip_path):
        super().__init__()
        self.install_manager = install_manager
        self.install_path = install_path
        self.zip_path = zip_path
    
    def run(self):
        success, error = self.install_manager.install(
            self.install_path,
            self.zip_path,
            progress_callback=self._on_progress
        )
        self.finished.emit(success, error)
    
    def _on_progress(self, current, total, message):
        self.progress.emit(current, total, message)


class WelcomePage(QWizardPage):
    """欢迎页"""
    def __init__(self):
        super().__init__()
        self.setTitle("欢迎使用 Minecraft FRP 联机工具")
        
        layout = QVBoxLayout()
        
        welcome_text = QLabel(
            "<h2>欢迎!</h2>"
            "<p>本向导将帮助您安装 Minecraft FRP 联机工具。</p>"
            "<p>这是一款用于 Minecraft 多人联机的内网穿透工具，"
            "帮助您轻松开启联机世界。</p>"
            "<br>"
            "<p><b>特别提示：</b>本工具使用 FRP 客户端（frpc.exe），"
            "部分杀毒软件可能将其误报为病毒。这是正常现象，请放心使用并添加信任。</p>"
        )
        welcome_text.setWordWrap(True)
        layout.addWidget(welcome_text)
        
        layout.addStretch()
        self.setLayout(layout)


class LicensePage(QWizardPage):
    """用户协议页"""
    def __init__(self):
        super().__init__()
        self.setTitle("用户协议")
        
        layout = QVBoxLayout()
        
        info_label = QLabel("请仔细阅读以下用户协议：")
        layout.addWidget(info_label)
        
        self.license_browser = QTextBrowser()
        self.license_browser.setMarkdown(self._get_license_text())
        layout.addWidget(self.license_browser)
        
        self.agree_checkbox = QCheckBox("我已阅读并同意用户协议")
        self.agree_checkbox.stateChanged.connect(self._on_agree_changed)
        layout.addWidget(self.agree_checkbox)
        
        self.setLayout(layout)
        
    def _get_license_text(self):
        """获取协议文本"""
        return """
# Minecraft FRP 联机工具用户协议

## 1. 服务说明
本工具提供 Minecraft 内网穿透服务，帮助用户实现局域网游戏的互联网访问。

## 2. 使用须知
- 本工具仅供合法的 Minecraft 联机使用
- 禁止使用本工具进行任何违法活动
- 禁止使用本工具搭建 HTTP/HTTPS 网站服务
- 禁止滥用服务器资源

## 3. 免责声明
- 本工具按"现状"提供，不提供任何明示或暗示的保证
- 使用本工具产生的任何后果由用户自行承担
- 开发者不对使用本工具造成的任何损失负责

## 4. 隐私保护
- 本工具仅收集必要的连接信息用于服务运行
- 不会收集、存储或传输用户的个人隐私数据
- 联机大厅功能会公开房间信息（房间名、游戏版本等）

## 5. 安全提示
**重要：** 本工具使用的 FRP 客户端（frpc.exe）可能被部分杀毒软件误报为病毒。
这是因为内网穿透工具的工作原理与某些恶意软件相似。请放心，本工具完全安全，
您可以将其添加到杀毒软件的信任列表中。

## 6. 其他条款
- 开发者保留随时修改本协议的权利
- 继续使用本工具即表示您接受修改后的协议

---

如有疑问，请访问：https://b.clash.ink
"""
    
    def _on_agree_changed(self):
        self.completeChanged.emit()
    
    def isComplete(self):
        return self.agree_checkbox.isChecked()


class InstallPathPage(QWizardPage):
    """安装路径选择页"""
    def __init__(self, install_manager):
        super().__init__()
        self.install_manager = install_manager
        self.setTitle("选择安装位置")
        
        layout = QVBoxLayout()
        
        # 提示信息
        if install_manager.is_upgrade():
            info_text = (
                f"<b>检测到已有安装：</b><br>"
                f"{install_manager.get_previous_path()}<br><br>"
                f"将进行覆盖安装并保留您的配置文件。"
            )
        else:
            info_text = "请选择安装位置："
        
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 路径选择
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        default_path = install_manager.get_previous_path() or install_manager.get_default_install_path()
        self.path_edit.setText(default_path)
        self.path_edit.textChanged.connect(self._on_path_changed)
        path_layout.addWidget(self.path_edit)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_path)
        path_layout.addWidget(browse_btn)
        
        layout.addLayout(path_layout)
        
        # 错误提示
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def _browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择安装目录")
        if path:
            self.path_edit.setText(path)
    
    def _on_path_changed(self):
        self.error_label.setText("")
        self.completeChanged.emit()
    
    def isComplete(self):
        path = self.path_edit.text()
        valid, error = self.install_manager.validate_install_path(path)
        if not valid:
            self.error_label.setText(error)
        return valid
    
    def get_install_path(self):
        return self.path_edit.text()


class InstallProgressPage(QWizardPage):
    """安装进度页"""
    def __init__(self):
        super().__init__()
        self.setTitle("正在安装")
        self.install_success = False
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel("准备安装...")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        self.detail_label = QLabel("")
        self.detail_label.setWordWrap(True)
        layout.addWidget(self.detail_label)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def start_install(self, install_manager, install_path, zip_path):
        """开始安装"""
        self.install_thread = InstallThread(install_manager, install_path, zip_path)
        self.install_thread.progress.connect(self._on_progress)
        self.install_thread.finished.connect(self._on_finished)
        self.install_thread.start()
    
    def _on_progress(self, current, total, message):
        self.progress_bar.setValue(current)
        self.progress_bar.setMaximum(total)
        self.detail_label.setText(message)
    
    def _on_finished(self, success, error):
        self.install_success = success
        if success:
            self.status_label.setText("✅ 安装完成！")
            self.detail_label.setText("Minecraft FRP 联机工具已成功安装。")
        else:
            self.status_label.setText("❌ 安装失败")
            self.detail_label.setText(f"错误：{error}")
        
        self.completeChanged.emit()
    
    def isComplete(self):
        return self.install_success


class FinishPage(QWizardPage):
    """完成页"""
    def __init__(self):
        super().__init__()
        self.setTitle("安装完成")
        
        layout = QVBoxLayout()
        
        finish_label = QLabel(
            "<h2>安装成功！</h2>"
            "<p>Minecraft FRP 联机工具已成功安装到您的计算机。</p>"
            "<p>您可以通过桌面快捷方式或开始菜单启动程序。</p>"
            "<br>"
            "<p>祝您游戏愉快！</p>"
        )
        finish_label.setWordWrap(True)
        layout.addWidget(finish_label)
        
        self.launch_checkbox = QCheckBox("完成后立即启动")
        self.launch_checkbox.setChecked(True)
        layout.addWidget(self.launch_checkbox)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def should_launch(self):
        return self.launch_checkbox.isChecked()


class InstallerWindow(QWizard):
    """安装程序主窗口"""
    def __init__(self, install_manager, zip_path=None):
        super().__init__()
        self.install_manager = install_manager
        self.zip_path = zip_path or self._find_bundled_zip()
        
        self.setWindowTitle("Minecraft FRP 安装向导")
        self.setWizardStyle(QWizard.ModernStyle)
        self.setFixedSize(600, 450)
        
        # 添加页面
        self.welcome_page = WelcomePage()
        self.license_page = LicensePage()
        self.path_page = InstallPathPage(install_manager)
        self.progress_page = InstallProgressPage()
        self.finish_page = FinishPage()
        
        self.addPage(self.welcome_page)
        self.addPage(self.license_page)
        self.addPage(self.path_page)
        self.addPage(self.progress_page)
        self.addPage(self.finish_page)
        
        self.currentIdChanged.connect(self._on_page_changed)
        self.finished.connect(self._on_wizard_finished)
    
    def _find_bundled_zip(self):
        """查找内嵌的安装包"""
        # TODO: 实现查找逻辑
        return "MinecraftFRP.zip"
    
    def _on_page_changed(self, page_id):
        """页面切换事件"""
        if self.currentPage() == self.progress_page:
            # 到达安装进度页，开始安装
            install_path = self.path_page.get_install_path()
            self.progress_page.start_install(
                self.install_manager,
                install_path,
                self.zip_path
            )
    
    def _on_wizard_finished(self, result):
        """向导完成事件"""
        if result == QWizard.Accepted and self.finish_page.should_launch():
            # TODO: 启动程序
            logger.info("Launching application...")
