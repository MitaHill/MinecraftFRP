from PySide6.QtCore import QMutex, QTimer
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QCloseEvent

# Core Imports
from src.core.ServerManager import ServerManager
from src.gui.main_window.Initialization import pre_ui_initialize, post_ui_initialize
from src.gui.main_window.UiSetup import setup_main_window_ui
from src.gui.main_window.Lifecycle import handle_close_event

# Feature/Action Imports
from src.gui.main_window.Threads import start_lan_poller, load_ping_values, update_server_combo, start_server_list_update
from src.gui.main_window.Handlers import (set_port, start_map, copy_link, log_message,
                                          on_auto_mapping_changed, on_dark_mode_changed, on_server_changed)
from src.gui.main_window.Actions import open_help_browser, open_server_management_dialog
from src.utils.LogManager import get_logger

logger = get_logger()

class PortMappingApp(QWidget):
    inst = None
    link = ""

    def __init__(self, servers={}):
        super().__init__()
        PortMappingApp.inst = self
        
        # --- 极简属性初始化，确保UI骨架能建立 ---
        self.SERVERS = servers  # 初始为空
        self.th = None
        self.lan_poller = None
        self.server_update_thread = None
        self.log_trimmer = None
        self.ping_thread = None
        self.app_mutex = QMutex()
        self.is_closing = False
        
        # 为UI设置提供临时的假数据
        self.auto_mapping_enabled = False
        self.dark_mode_override = False
        self.force_dark_mode = False
        self.app_config = {"settings": {}}
        
        # --- 仅创建UI骨架 ---
        setup_main_window_ui(self, self.SERVERS)
        
        # --- 延迟执行所有耗时操作 ---
        QTimer.singleShot(50, self.deferred_initialization)

    def deferred_initialization(self):
        """延迟初始化：在窗口显示后执行所有耗时操作"""
        logger.info("执行延迟初始化...")
        
        # 1. 加载配置 (同步IO)
        pre_ui_initialize(self)
        
        # 2. 加载本地服务器列表 (同步IO)
        self.server_manager = ServerManager()
        self.SERVERS = self.server_manager.get_servers()
        
        # 3. 用初始数据填充UI
        self.mapping_tab.update_server_list(self.SERVERS)
        
        # 4. 执行UI创建后的其他初始化 (同步IO)
        post_ui_initialize(self)
        
        # 5. 启动所有后台更新线程 (异步)
        start_lan_poller(self)
        start_server_list_update(self)
        logger.info("延迟初始化完成。")

    # --- 生命周期事件 ---
    def closeEvent(self, event: QCloseEvent):
        handle_close_event(self, event)

    # --- 线程/异步回调 ---
    def onFrpcTerminated(self):
        self.th = None

    def onLANPollerTerminated(self):
        self.lan_poller = None

    def on_servers_updated(self, new_servers):
        """后台线程更新服务器列表后的回调"""
        self.log("服务器列表已从网络更新。")
        self.SERVERS = new_servers
        self.mapping_tab.update_server_list(new_servers)
        self.load_ping_values()  # 用新的列表进行测速

    def update_ad(self):
        ad = self.ad_manager.get_next_ad()
        color = "cyan" if self.theme == "dark" else "blue"
        text = f'<a href="{ad["url"]}" style="color:{color}">{ad["show"]}</a>' if ad else "无广告"
        self.mapping_tab.ad_label.setText(text)

    # --- 信号/事件连接的代理方法 ---
    def set_port(self, port):
        set_port(self, port)

    def start_map(self):
        start_map(self)

    def copy_link(self):
        copy_link(self)
        
    def update_server_combo(self, results):
        update_server_combo(self, results)

    def on_auto_mapping_changed(self, state):
        on_auto_mapping_changed(self, state)

    def on_dark_mode_changed(self, state):
        on_dark_mode_changed(self, state)
        
    def on_server_changed(self, text):
        on_server_changed(self, text)
        
    def open_server_management(self):
        open_server_management_dialog(self)

    def start_web_browser(self):
        open_help_browser(self)
        
    def load_ping_values(self):
        load_ping_values(self)
        
    def log(self, message, color=None):
        log_message(self, message, color)
