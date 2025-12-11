import tempfile
import os
import sys
import subprocess
from pathlib import Path
from PySide6.QtCore import QMutex, QTimer, Qt, QThread, Signal
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtGui import QCloseEvent

# Core Imports
from src.core.ServerManager import ServerManager
from src.core.DownloadThread import DownloadThread
from src.core.UpdateCheckThread import UpdateCheckThread
from src.version import VERSION as APP_VERSION
from src.utils.Crypto import calculate_sha256
from src.utils.PathUtils import get_resource_path
from src.gui.main_window.Initialization import pre_ui_initialize, post_ui_initialize
from src.gui.main_window.UiSetup import setup_main_window_ui
from src.gui.main_window.Lifecycle import handle_close_event
from src.gui.dialogs.UpdateDialogs import UpdateDownloadDialog
from src.gui.dialogs.AdDialog import AdDialog
from src.gui.dialogs.AdThread import AdThread

# Feature/Action Imports
from src.gui.main_window.Threads import (start_lan_poller, load_ping_values, update_server_combo,
                                       start_server_list_update)
from src.gui.main_window.Handlers import (set_port, start_map, copy_link, log_message,
                                          on_auto_mapping_changed, on_dark_mode_changed, on_server_changed)
from src.gui.main_window.Actions import open_help_browser
from src.utils.LogManager import get_logger

logger = get_logger()

class SecurityCheckThread(QThread):
    check_finished = Signal(bool, str)
    def run(self):
        from src.core.SecurityService import SecurityService
        passed, reason = SecurityService.perform_startup_check()
        self.check_finished.emit(passed, reason)

class PortMappingApp(QWidget):
    inst = None
    link = ""

    def __init__(self, servers={}):
        super().__init__()
        PortMappingApp.inst = self
        
        # --- Attribute Initialization ---
        self.SERVERS = servers
        self.th = None
        self.lan_poller = None
        self.server_update_thread = None
        self.update_checker_thread = None
        self.download_thread = None
        self.log_trimmer = None
        self.ping_thread = None
        self.ad_thread = None
        self.security_check_thread = None
        self.app_mutex = QMutex()
        self.is_closing = False
        self.current_update_info = None
        
        # Scrolling Ad Attributes
        self.scrolling_ads = []
        self.current_scrolling_ad_index = 0
        self.scrolling_ad_timer = QTimer(self)
        
        self.auto_mapping_enabled = False
        self.dark_mode_override = False
        self.force_dark_mode = False
        # 配置文件路径迁移到用户文档目录
        self.docs_dir = Path.home() / "Documents" / "MitaHillFRP"
        self.app_config_path = self.docs_dir / "Config" / "app_config.yaml"
        self.app_config = self._load_app_config()

        
        setup_main_window_ui(self, self.SERVERS)
        # 延迟记录初始窗口尺寸，等待UI完全构建
        def record_initial_size():
            self._initial_size = self.size()
            self._initial_geometry = self.geometry()
        QTimer.singleShot(100, record_initial_size)
        QTimer.singleShot(50, self.deferred_initialization)

    def deferred_initialization(self):
        """Deferred initialization: executes heavy tasks after the window is shown."""
        logger.info("Performing deferred initialization...")
        
        # Start Security Check
        self.security_check_thread = SecurityCheckThread()
        self.security_check_thread.check_finished.connect(self.on_security_check_finished)
        self.security_check_thread.start()
        
    def on_security_check_finished(self, passed, reason):
        if not passed:
             QMessageBox.critical(self, "安全警告", reason)
             self.close()
             return
             
        self.continue_initialization()

    def continue_initialization(self):
        # Log version information
        from src.version import get_version_string, VERSION, GIT_HASH
        import json
        
        channel = "unknown"
        try:
            install_info_path = self.docs_dir / "install_info.json"
            if install_info_path.exists():
                with open(install_info_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    channel = data.get('channel', 'unknown')
        except Exception:
            pass

        version_str = get_version_string()
        logger.info(f"Application started: {version_str}, Channel: {channel}")
        logger.info(f"Version: {VERSION}, Git Hash: {GIT_HASH}")

        pre_ui_initialize(self)

        self.server_manager = ServerManager()
        self.SERVERS = self.server_manager.get_servers()

        self.mapping_tab.update_server_list(self.SERVERS)

        post_ui_initialize(self)

        start_lan_poller(self)

        # 立即启动后台网络任务（取消2秒延迟）
        self._start_background_tasks()
        
        logger.info("Deferred initialization complete.")

    def _start_background_tasks(self):
        """启动后台网络任务"""
        start_server_list_update(self)
        
        # 主程序不再负责更新检查，交由 Launcher 处理
        # self.update_checker_thread = UpdateCheckThread(current_version=APP_VERSION)
        # ...

        # Setup and start unified ad thread
        self.ad_thread = AdThread()
        self.ad_thread.finished.connect(self._on_ads_ready)
        self.ad_thread.start()

    def _on_ads_ready(self, ad_data):
        """
        Handles the unified ad data once it's fetched and processed by the AdThread.
        """
        # 改为在“推广”标签页推送，锁定其他标签，轮播结束后跳转到“映射”并隐藏“推广”。
        popup_ads = ad_data.get('popup_ads', [])
        # 检查今日是否已展示推广
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        last_promo_date = self.app_config.get("promo_last_shown_date", "")
        if not self.is_closing and popup_ads and last_promo_date != today:
            # 记录今日已展示推广
            self.app_config["promo_last_shown_date"] = today
            self._save_app_config()

            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
            from PySide6.QtCore import QUrl, Qt as QtCore
            # 在显示推广前，先锁定主窗口尺寸
            if hasattr(self, '_initial_geometry'):
                self.setFixedSize(self._initial_geometry.size())
            promo_tab = QWidget()
            v = QVBoxLayout(promo_tab)
            v.setContentsMargins(8, 8, 8, 8)
            v.setSpacing(6)
            # 图片容器：不固定QLabel尺寸，让图片自由缩放
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setMaximumSize(480, 270)
            lbl.setScaledContents(False)
            v.addWidget(lbl, 0, Qt.AlignCenter)
            # 备注文字（不作为跳转控件）
            remark_lbl = QLabel()
            remark_lbl.setAlignment(Qt.AlignCenter)
            v.addWidget(remark_lbl)
            # 插入“推广”标签页并切换过去
            self.promo_tab = promo_tab
            self.tab_widget.addTab(promo_tab, "推广")
            self.tab_widget.setCurrentWidget(promo_tab)
            # 锁定其他标签，但保留“线上公告”可用
            for i in range(self.tab_widget.count()):
                w = self.tab_widget.widget(i)
                keep_enabled = (w is promo_tab) or (w is self.browser_tab)
                self.tab_widget.setTabEnabled(i, keep_enabled)
            # 进度条显示当前图片停留时间
            from PySide6.QtWidgets import QProgressBar, QPushButton, QHBoxLayout
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(0)
            # 加速按钮
            speedup_btn = QPushButton("⏩ 加速")
            speedup_btn.setMaximumWidth(80)
            speedup_btn.setToolTip("点击获取随机的加速效果")
            # 底部布局：进度条+加速按钮
            bottom_layout = QHBoxLayout()
            bottom_layout.addWidget(progress)
            bottom_layout.addWidget(speedup_btn)
            v.addLayout(bottom_layout)
            # 轮播显示，每条广告使用其duration
            from PySide6.QtCore import QTimer
            self._promo_ads = popup_ads
            self._promo_idx = 0
            # 为每次广告创建独立定时器，避免断开连接警告
            self._promo_progress_timer = QTimer()
            self._promo_progress_timer.setInterval(100)
            def open_in_browser(url):
                try:
                    self.tab_widget.setCurrentWidget(self.browser_tab)
                    if getattr(self.browser_tab, 'view', None):
                        self.browser_tab.view.setUrl(QUrl(url))
                except Exception:
                    pass
            def show_next():
                # 停止并断开上一轮进度条连接，重置进度
                try:
                    self._promo_progress_timer.stop()
                except Exception:
                    pass
                # 重建新的定时器而非断开旧信号，避免 RuntimeWarning
                self._promo_progress_timer = QTimer()
                self._promo_progress_timer.setInterval(100)
                progress.setValue(0)
                # 重置加速冷却时间
                if hasattr(self, '_promo_last_speedup_time'):
                    delattr(self, '_promo_last_speedup_time')
                if self._promo_idx >= len(self._promo_ads):
                    # 结束：移除推广标签，解锁并跳转到“映射”
                    idx = self.tab_widget.indexOf(promo_tab)
                    if idx >= 0:
                        self.tab_widget.removeTab(idx)
                    for i in range(self.tab_widget.count()):
                        self.tab_widget.setTabEnabled(i, True)
                    self.tab_widget.setCurrentWidget(self.mapping_tab)
                    # 解除窗口尺寸锁定并恢复到初始尺寸
                    try:
                        self.setMinimumSize(0, 0)
                        self.setMaximumSize(16777215, 16777215)
                        if hasattr(self, '_initial_geometry'):
                            self.setGeometry(self._initial_geometry)
                        elif hasattr(self, '_initial_size'):
                            self.resize(self._initial_size)
                    except Exception:
                        pass
                    return
                ad = self._promo_ads[self._promo_idx]
                self._promo_idx += 1
                pix = ad.get('pixmap')
                url = ad.get('url', '#')
                remark = ad.get('remark', '推广')
                # 点击图片跳转到“线上公告”加载动态URL
                def on_image_click(ev):
                    try:
                        open_in_browser(url)
                    except Exception:
                        pass
                lbl.mousePressEvent = on_image_click
                # 显示图片（仅缩小不放大，等比例缩放到适合区域）
                if pix:
                    try:
                        from PySide6.QtGui import QPixmap
                        # 固定容器480x270，图片按KeepAspectRatio缩放适配
                        scaled = pix.scaled(480, 270, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        lbl.setPixmap(scaled)
                    except Exception:
                        lbl.setText('')
                else:
                    lbl.setText('')
                # 设置备注样式（颜色与字号随主题变化）
                color = "#1a73e8" if self.theme == "light" else "#66ccff"
                remark_lbl.setText(f"<span style='color:{color}; font-size:14px;'>{remark}</span>")
                # 启动新的进度条动画
                dur_ms = max(1000, int(ad.get('duration', 5)) * 1000)
                elapsed = {"v": 0}
                skip_triggered = {"flag": False}
                def tick():
                    if skip_triggered["flag"]:
                        return
                    elapsed["v"] += 100
                    pct = min(100, int(elapsed["v"] * 100 / dur_ms))
                    progress.setValue(pct)
                self._promo_progress_timer.timeout.connect(tick)
                self._promo_progress_timer.start()
                # 加速按钮：3秒冷却，每次随机前进5%-60%，98%处停止加速效果
                def on_speedup():
                    import time, random
                    now = time.time()
                    if hasattr(self, '_promo_last_speedup_time'):
                        if now - self._promo_last_speedup_time < 3.0:
                            return  # 冷却中
                    # 检查当前进度，98%后禁止加速
                    current_pct = elapsed["v"] / dur_ms
                    if current_pct >= 0.98:
                        return  # 已达98%，停止加速
                    self._promo_last_speedup_time = now
                    # 随机前进5%-60%
                    speedup_pct = random.uniform(0.05, 0.60)
                    elapsed["v"] += dur_ms * speedup_pct
                    # 溢出检测：不超过98%
                    if elapsed["v"] >= dur_ms * 0.98:
                        elapsed["v"] = dur_ms * 0.98
                speedup_btn.clicked.connect(on_speedup)
                
                def on_timeout():
                    if not skip_triggered["flag"]:
                        skip_triggered["flag"] = True
                        show_next()
                QTimer.singleShot(dur_ms, on_timeout)
            show_next()
        # 滚动广告仍显示在映射标签
        self.scrolling_ads = ad_data.get('scrolling_ads', [])
        if not self.is_closing and self.scrolling_ads:
            logger.info("滚动广告资源已就绪，启动定时器。")
            self.scrolling_ad_timer.timeout.connect(self._update_scrolling_ad)
            self.scrolling_ad_timer.start(10000)
            self._update_scrolling_ad()

    def _update_scrolling_ad(self):
        """Cycles through the scrolling ads and updates the ad label."""
        if not self.scrolling_ads:
            self.mapping_tab.ad_label.setText("无广告")
            return
            
        ad = self.scrolling_ads[self.current_scrolling_ad_index]
        self.current_scrolling_ad_index = (self.current_scrolling_ad_index + 1) % len(self.scrolling_ads)
        
        color = "cyan" if self.theme == "dark" else "blue"
        text = ad.get('text', '...')
        url = ad.get('url', '#')
        
        formatted_text = f'<a href="{url}" style="color:{color}">{text}</a>'
        self.mapping_tab.ad_label.setText(formatted_text)

    def _load_app_config(self):
        """从YAML文件加载app_config，兼容旧版本"""
        try:
            import yaml
            if self.app_config_path.exists():
                with open(self.app_config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    # 兼容旧版本：如果加载的不是字典，返回默认值
                    if isinstance(config, dict):
                        return config
        except Exception as e:
            logger.warning(f"加载app_config失败: {e}")
        return {"settings": {}}

    def _save_app_config(self):
        """保存app_config到YAML文件"""
        try:
            import yaml
            self.app_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.app_config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(self.app_config, f, allow_unicode=True, sort_keys=False)
        except Exception as e:
            logger.warning(f"保存app_config失败: {e}")

    # --- Lifecycle and Callbacks ---
    def closeEvent(self, event: QCloseEvent):
        self.scrolling_ad_timer.stop() # Stop the timer on close
        handle_close_event(self, event)
        
    def onFrpcTerminated(self):
        # 停止心跳（如有）并清理线程引用
        try:
            if hasattr(self, "heartbeat_manager"):
                self.heartbeat_manager.stop_room_heartbeat()
        except Exception:
            pass
        try:
            if hasattr(self, "lobby_heartbeat_manager"):
                self.lobby_heartbeat_manager.stop_room_heartbeat()
        except Exception:
            pass
        self.th = None
    def onLANPollerTerminated(self): self.lan_poller = None
    def on_servers_updated(self, new_servers):
        self.log("服务器列表已从网络更新。")
        self.SERVERS = new_servers
        self.mapping_tab.update_server_list(self.SERVERS)
        self.load_ping_values()
        
    def update_ad(self):
        self._update_scrolling_ad()

    # --- Proxy methods for signal/event connections ---
    def set_port(self, port): set_port(self, port)
    def start_map(self): start_map(self)
    def copy_link(self): copy_link(self)
    def update_server_combo(self, results): update_server_combo(self, results)
    def on_auto_mapping_changed(self, state): on_auto_mapping_changed(self, state)
    def on_dark_mode_changed(self, state): on_dark_mode_changed(self, state)
    def on_server_changed(self, text): on_server_changed(self, text)
    def start_web_browser(self): open_help_browser(self)
    def load_ping_values(self): load_ping_values(self)
    def log(self, message, color=None): log_message(self, message, color)
