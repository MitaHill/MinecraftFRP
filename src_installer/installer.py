"""
Minecraft FRP 安装程序主入口
负责安装、升级、卸载管理
"""
import sys
import os
from pathlib import Path

# 确保可以导入src_installer包
current_dir = Path(__file__).parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# 现在使用标准导入
from src_installer.gui.installer_window import InstallerWindow
from src_installer.core.install_manager import InstallManager
from src_installer.utils.logger import setup_logger

def main():
    try:
        setup_logger()
    except Exception as e:
        print(f"设置日志失败: {e}")
    
    app = QApplication(sys.argv)
    app.setApplicationName("Minecraft FRP Installer")
    app.setApplicationVersion("1.0.0")
    
    # 启用高DPI支持
    try:
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        # PySide6旧版本可能没有ApplicationAttribute枚举
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    try:
        install_manager = InstallManager()
        window = InstallerWindow(install_manager)
        window.show()
    except Exception as e:
        print(f"创建窗口失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
