import os
import sys
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox

from src.utils.ad_manager import AdManager
from src.core.config_manager import ConfigManager
from src.core.yaml_config import YamlConfigManager, DEFAULT_APP_CONFIG
from src.utils.path_utils import get_resource_path
from src.network.minecraft_lan import poll_minecraft_lan_once
from src.gui.handlers import log_message

def initialize_app(window):
    """主窗口和应用程序的全面初始化"""
    initialize_managers(window)
    load_configuration(window)
    
    if not os.path.exists(get_resource_path("frpc.exe")):
        QMessageBox.critical(window, "错误", "frpc.exe 未找到，程序即将退出。")
        sys.exit(1)
        
    initialize_timers(window)
    perform_initial_port_query(window)

def initialize_managers(window):
    """初始化核心管理器"""
    window.config_manager = ConfigManager()
    window.ad_manager = AdManager()
    window.yaml_config = YamlConfigManager()

def load_configuration(window):
    """加载YAML配置"""
    window.app_config = window.yaml_config.load_config("app_config.yaml", DEFAULT_APP_CONFIG)
    settings = window.app_config.get("settings", {})
    window.auto_mapping_enabled = settings.get("auto_mapping", False)
    window.dark_mode_override = settings.get("dark_mode_override", False)
    window.force_dark_mode = settings.get("force_dark_mode", False)

def initialize_timers(window):
    """初始化所有定时器"""
    window.ad_timer = QTimer(window)
    window.ad_timer.timeout.connect(window.update_ad)
    window.ad_timer.start(3000)
    
    window.ping_timer = QTimer(window)
    window.ping_timer.timeout.connect(lambda: window.load_ping_values())
    window.ping_timer.start(3000)

def perform_initial_port_query(window):
    """执行初始的Minecraft端口查询"""
    port = poll_minecraft_lan_once()
    if port:
        window.mapping_tab.port_edit.setText(port)
        log_message(window, f"检测到Minecraft游戏端口: {port}", "green")
    else:
        log_message(window, "未检测到Minecraft游戏端口", "orange")
