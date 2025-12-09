import os
import sys
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox

from src.utils.PathUtils import get_resource_path
from src.core.ConfigManager import ConfigManager
from src.core.YamlConfig import YamlConfigManager, DEFAULT_APP_CONFIG
from src.network.MinecraftLan import poll_minecraft_lan_once
from src.gui.main_window.Handlers import log_message
from src.tools.LogTrimmer import LogTrimmer

def pre_ui_initialize(window):
    """在UI设置之前进行初始化"""
    initialize_managers(window)
    load_configuration(window)
    
    if not os.path.exists(get_resource_path("base\\frpc.exe")):
        QMessageBox.critical(window, "错误", "frpc.exe 未找到，程序即将退出。")
        sys.exit(1)

def post_ui_initialize(window):
    """在UI设置之后进行初始化"""
    initialize_timers(window)
    # 移除同步的端口查询，完全依赖后台异步轮询
    # perform_initial_port_query(window) 
    start_log_trimmer(window)

def initialize_managers(window):
    """初始化核心管理器"""
    window.config_manager = ConfigManager()
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
    window.ping_timer = QTimer(window)
    window.ping_timer.timeout.connect(lambda: window.load_ping_values())
    window.ping_timer.start(3000)

def start_log_trimmer(window):
    """启动日志裁剪线程"""
    try:
        logs_size = window.app_config.get("app", {}).get("logs_size", "1MB")
        log_path = os.path.join("logs", "app.log")
        window.log_trimmer = LogTrimmer(log_path, logs_size)
        window.log_trimmer.start()
    except Exception as e:
        print(f"Error starting LogTrimmer: {e}")

def perform_initial_port_query(window):
    """执行初始的Minecraft端口查询"""
    port = poll_minecraft_lan_once()
    if port:
        window.mapping_tab.port_edit.setText(port)
        log_message(window, f"检测到Minecraft游戏端口: {port}", "green")
    else:
        log_message(window, "未检测到Minecraft游戏端口", "orange")
