import webbrowser
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from src.gui.dialogs.ServerManagementDialog import ServerManagementDialog

def open_help_browser(window):
    """打开帮助文档网页（优先内置浏览器Tab）"""
    try:
        url = window.app_config.get("app", {}).get(
            "browser_default_url",
            "https://b.clash.ink/archives/mi-ta-shan-lian-ji-gong-ju",
        )
        # 优先使用内置BrowserTab的QWebEngineView
        if hasattr(window, "browser_tab") and getattr(window.browser_tab, "view", None):
            window.browser_tab.view.setUrl(QUrl(url))
            window.tab_widget.setCurrentWidget(window.browser_tab)
            return
        # 退回系统默认浏览器
        if not QDesktopServices.openUrl(QUrl(url)):
            if not webbrowser.open(url):
                raise RuntimeError("无法启动默认浏览器")
    except Exception as e:
        QMessageBox.critical(window, "错误", f"打开网址失败: {e}")

def open_server_management_dialog(window):
    """打开服务器管理配置对话框"""
    try:
        dialog = ServerManagementDialog(window)
        dialog.exec()
    except Exception as e:
        QMessageBox.critical(window, "错误", f"打开服务器管理配置失败: {e}")
