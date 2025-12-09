import datetime
from pathlib import Path
from PySide6.QtWidgets import QVBoxLayout, QTabWidget
from PySide6.QtGui import QIcon

from src.gui.styles import STYLE
from src.gui.tabs.MappingTab import MappingTab
from src.gui.tabs.ToolboxTab import ToolboxTab
from src.gui.tabs.SettingsTab import SettingsTab
from src.gui.tabs.BrowserTab import BrowserTab
from src.utils.PathUtils import get_resource_path
from src.utils.LogManager import get_logger

logger = get_logger()

def setup_main_window_ui(window, servers):
    """初始化主窗口UI"""
    window.setWindowTitle("Minecraft 端口映射工具")
    window.setGeometry(100, 100, 400, 550)
    
    setup_window_icon(window)
    setup_theme(window)
    
    main_layout = QVBoxLayout(window)
    window.tab_widget = QTabWidget()
    main_layout.addWidget(window.tab_widget)
    
    setup_tabs(window, servers)

def setup_window_icon(window):
    """设置窗口图标"""
    try:
        icon_path = Path(get_resource_path("base\\logo.ico"))
        if icon_path.exists():
            window.setWindowIcon(QIcon(str(icon_path)))
    except Exception as e:
        logger.warning(f"设置图标出错: {e}")

def setup_theme(window):
    """根据配置或时间设置主题"""
    if window.dark_mode_override:
        window.theme = 'dark' if window.force_dark_mode else 'light'
    else:
        h = datetime.datetime.now().hour
        window.theme = 'light' if 7 <= h < 18 else 'dark'
    window.setStyleSheet(STYLE[window.theme])

def setup_tabs(window, servers):
    """初始化并添加Tabs"""
    window.mapping_tab = MappingTab(window, servers)
    window.toolbox_tab = ToolboxTab(window)
    window.settings_tab = SettingsTab(window)
    window.browser_tab = BrowserTab(window)

    window.tab_widget.addTab(window.mapping_tab, "映射")
    window.tab_widget.addTab(window.toolbox_tab, "工具箱")
    window.tab_widget.addTab(window.settings_tab, "设置")
    window.tab_widget.addTab(window.browser_tab, "线上公告")
