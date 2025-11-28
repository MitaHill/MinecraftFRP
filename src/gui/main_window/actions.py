import webbrowser
from PySide6.QtWidgets import QMessageBox
from src.gui.dialogs.ServerManagementDialog import ServerManagementDialog

def open_help_browser(window):
    """打开帮助文档网页"""
    try:
        url = "https://b.clash.ink/#/memo/8"
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
