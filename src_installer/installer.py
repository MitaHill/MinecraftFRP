"""
Minecraft FRP 安装程序主入口
负责安装、升级、卸载管理
"""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# 使用相对导入以支持Nuitka打包
try:
    # 尝试相对导入（打包后）
    from gui.installer_window import InstallerWindow
    from core.install_manager import InstallManager
    from utils.logger import setup_logger
except ImportError:
    # 回退到完整路径（开发时）
    from src_installer.gui.installer_window import InstallerWindow
    from src_installer.core.install_manager import InstallManager
    from src_installer.utils.logger import setup_logger

def main():
    setup_logger()
    
    app = QApplication(sys.argv)
    app.setApplicationName("Minecraft FRP Installer")
    app.setApplicationVersion("1.0.0")
    
    # 启用高DPI支持
    app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
    install_manager = InstallManager()
    window = InstallerWindow(install_manager)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
