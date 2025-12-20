import tempfile
import os
import sys
import subprocess
from pathlib import Path
from PySide6.QtCore import QMutex, QTimer, Qt, QThread, Signal, QUrl, QSize
from PySide6.QtWidgets import (QWidget, QMessageBox, QVBoxLayout, QLabel, QProgressBar, 
                               QPushButton, QHBoxLayout, QSizePolicy, QFrame)
from PySide6.QtGui import QCloseEvent, QPixmap, QCursor, QDesktopServices

# Core Imports
from src.core.AppCore import AppCore
from src.core.DownloadThread import DownloadThread
from src.core.UpdateCheckThread import UpdateCheckThread
from src.version import VERSION as APP_VERSION
from src.utils.Crypto import calculate_sha256
from src.utils.PathUtils import get_resource_path
from src.gui.main_window.Initialization import pre_ui_initialize, post_ui_initialize
from src.gui.main_window.UiSetup import setup_main_window_ui
from src.gui.main_window.Lifecycle import handle_close_event
from src.gui.dialogs.UpdateDialogs import UpdateDownloadDialog

# Feature/Action Imports
from src.gui.main_window.Threads import (start_lan_poller, load_ping_values, update_server_combo,
                                       start_server_list_update)
from src.gui.main_window.Handlers import (set_port, start_map, copy_link, log_message,
                                          on_auto_mapping_changed, on_dark_mode_changed, on_server_changed)
from src.gui.main_window.Actions import open_help_browser
from src.utils.LogManager import get_logger

logger = get_logger()

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
        self.app_mutex = QMutex()
        self.is_closing = False
        self.current_update_info = None
        
        # Ad Attributes
        self.scrolling_ads = []
        self.current_scrolling_ad_index = 0
        self.scrolling_ad_timer = QTimer(self)
        self._popup_ad_timer = QTimer(self) # Timer for popup ads
        self._popup_ads_data = []
        self._current_ad_idx = 0
        self._ad_remaining_ms = 0
        
        self.auto_mapping_enabled = False
        self.dark_mode_override = False
        self.force_dark_mode = False
        
        self.docs_dir = Path.home() / "Documents" / "MitaHillFRP"
        self.app_config_path = self.docs_dir / "Config" / "app_config.yaml"
        self.app_config = self._load_app_config()

        # --- UI and Core Setup ---
        setup_main_window_ui(self, self.SERVERS)
        
        # 记录初始窗口尺寸
        QTimer.singleShot(100, self._record_initial_size)
        
        # 启动后端核心
        self.app_core = AppCore(self.docs_dir)
        self._connect_core_signals()
        self.app_core.start_initialization()

    def _record_initial_size(self):
        self._initial_size = self.size()
        self._initial_geometry = self.geometry()

    def _connect_core_signals(self):
        """将 AppCore 的信号连接到 MainWindow 的槽函数"""
        self.app_core.security_check_failed.connect(self.on_security_check_failed)
        self.app_core.security_check_passed.connect(self.on_security_check_passed)
        self.app_core.server_list_loaded.connect(self.on_servers_loaded)
        self.app_core.ads_ready.connect(self._on_ads_ready)
        self.app_core.error_occurred.connect(self.on_core_error)

    # --- Core Signal Handlers ---
    def on_security_check_failed(self, reason):
        """处理安全检查失败"""
        logger.warning(f"Security check failed: {reason}")
        QMessageBox.critical(self, "安全警告", f"安全检查未通过，程序将退出。\n\n原因: {reason}")
        self.close()

    def on_security_check_passed(self):
        """安全检查通过后，初始化UI相关组件"""
        logger.info("Security check passed. Initializing UI components.")
        pre_ui_initialize(self)
        post_ui_initialize(self)
        start_lan_poller(self)
        self._start_background_tasks()
        
        if self.app_core.channel == 'dev':
            from src.utils.EasterEggs import EasterEggs
            self.easter_eggs = EasterEggs(self)
            self.easter_eggs.check_and_run()
        
        logger.info("UI initialization complete.")

    def on_servers_loaded(self, servers):
        """处理从核心加载的服务器列表"""
        self.SERVERS = servers
        self.mapping_tab.update_server_list(self.SERVERS)

    def on_core_error(self, error_message):
        """处理来自核心的通用错误"""
        QMessageBox.critical(self, "核心错误", error_message)

    def _start_background_tasks(self):
        """启动后台网络任务 (由UI触发)"""
        start_server_list_update(self)
        # 注意：广告获取已移至 AppCore

    def _on_ads_ready(self, ad_data):
        """
        处理从 AppCore 获取的广告数据。
        此函数现在只负责UI展示，逻辑更清晰。
        """
        try:
            # 弹窗广告逻辑
            popup_ads = ad_data.get('popup_ads', [])
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            last_promo_date = self.app_config.get("promo_last_shown_date", "")

            # 调试：总是显示广告 (如果需要调试，可以取消下面条件的注释)
            # last_promo_date = "" 

            if not self.is_closing and popup_ads and last_promo_date != today:
                self.app_config["promo_last_shown_date"] = today
                self._save_app_config()
                self._show_popup_ads(popup_ads)
            elif not popup_ads:
                logger.info("没有弹窗广告数据。")
            else:
                logger.info(f"今日已展示过弹窗广告 ({last_promo_date})，跳过。")

            # 滚动广告逻辑
            self.scrolling_ads = ad_data.get('scrolling_ads', [])
            if not self.is_closing and self.scrolling_ads:
                logger.info("滚动广告资源已就绪，启动定时器。")
                self.scrolling_ad_timer.timeout.connect(self._update_scrolling_ad)
                self.scrolling_ad_timer.start(10000)
                self._update_scrolling_ad()

        except Exception as e:
            logger.error("Error processing ad data in _on_ads_ready", exc_info=True)
            # 即使广告处理失败，也要确保UI不会被卡住
            self._recover_ui_from_ad_error()

    def _show_popup_ads(self, popup_ads):
        """
        Displays the popup ads in a new tab.
        """
        try:
            if hasattr(self, '_initial_geometry'):
                self.setFixedSize(self._initial_geometry.size())

            self._popup_ads_data = popup_ads
            self._current_ad_idx = 0
            
            # Create Promotion Tab
            self.promo_tab = QWidget()
            layout = QVBoxLayout(self.promo_tab)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            # 1. Image Area
            self.ad_image_label = QLabel()
            self.ad_image_label.setAlignment(Qt.AlignCenter)
            self.ad_image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.ad_image_label.setCursor(QCursor(Qt.PointingHandCursor))
            self.ad_image_label.mousePressEvent = self._on_ad_clicked
            layout.addWidget(self.ad_image_label)
            
            # 2. Controls Area
            controls_frame = QFrame()
            controls_frame.setStyleSheet("QFrame { background-color: rgba(0,0,0,0.1); }")
            controls_layout = QHBoxLayout(controls_frame)
            controls_layout.setContentsMargins(10, 5, 10, 5)
            
            # Remark Label
            self.ad_remark_label = QLabel()
            self.ad_remark_label.setStyleSheet("font-weight: bold; color: #333;")
            if self.theme == 'dark':
                self.ad_remark_label.setStyleSheet("font-weight: bold; color: #ccc;")
            controls_layout.addWidget(self.ad_remark_label)
            
            controls_layout.addStretch()
            
            # Skip Button
            self.ad_skip_btn = QPushButton("跳过 >")
            self.ad_skip_btn.setCursor(QCursor(Qt.PointingHandCursor))
            self.ad_skip_btn.clicked.connect(self._on_skip_ad)
            self.ad_skip_btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid #999;
                    border-radius: 4px;
                    padding: 4px 12px;
                    background-color: rgba(255,255,255,0.8);
                    color: black;
                }
                QPushButton:hover { background-color: white; }
            """)
            if self.theme == 'dark':
                self.ad_skip_btn.setStyleSheet("""
                    QPushButton {
                        border: 1px solid #555;
                        border-radius: 4px;
                        padding: 4px 12px;
                        background-color: rgba(60,60,60,0.8);
                        color: white;
                    }
                    QPushButton:hover { background-color: #505050; }
                """)
            controls_layout.addWidget(self.ad_skip_btn)
            
            layout.addWidget(controls_frame)
            
            # 3. Progress Bar
            self.ad_progress = QProgressBar()
            self.ad_progress.setTextVisible(False)
            self.ad_progress.setFixedHeight(4)
            self.ad_progress.setStyleSheet("QProgressBar { border: none; background: #ddd; } QProgressBar::chunk { background: #2196F3; }")
            layout.addWidget(self.ad_progress)

            # Add tab and show
            self.tab_widget.addTab(self.promo_tab, "推广")
            self.tab_widget.setCurrentWidget(self.promo_tab)
            
            # Disable other tabs to force view
            for i in range(self.tab_widget.count()):
                if self.tab_widget.widget(i) != self.promo_tab:
                    self.tab_widget.setTabEnabled(i, False)

            # Setup Timer
            self._popup_ad_timer.timeout.connect(self._update_ad_progress)
            
            # Start first ad
            self._load_next_ad()
            
        except Exception as e:
            logger.error(f"Failed to show popup ads: {e}", exc_info=True)
            self._recover_ui_from_ad_error()

    def _load_next_ad(self):
        """Loads the current ad index."""
        if self._current_ad_idx >= len(self._popup_ads_data):
            self._recover_ui_from_ad_error()
            return

        ad = self._popup_ads_data[self._current_ad_idx]
        
        # Set Image
        pixmap = ad.get('pixmap')
        if pixmap and not pixmap.isNull():
            # Scale image to fit label (keeping aspect ratio)
            # Note: We might need to resize event to rescale dynamically, 
            # but for simplicity we scale to current size or fixed size.
            # Using ScaledContents on QLabel is easier but might distort if aspect ratio differs.
            # Let's try scaling properly.
            w, h = self.width(), self.height() - 60 # approx height for controls
            scaled_pixmap = pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.ad_image_label.setPixmap(scaled_pixmap)
        else:
            self.ad_image_label.setText("图片加载失败")

        # Set Text
        self.ad_remark_label.setText(ad.get('remark', ''))
        
        # Setup Duration
        duration = ad.get('duration', 5) # seconds
        self._ad_remaining_ms = duration * 1000
        self.ad_progress.setRange(0, self._ad_remaining_ms)
        self.ad_progress.setValue(0)
        
        # Start/Restart Timer (tick every 100ms)
        self._popup_ad_timer.start(100)

    def _update_ad_progress(self):
        """Timer tick handler."""
        self._ad_remaining_ms -= 100
        elapsed = self.ad_progress.maximum() - self._ad_remaining_ms
        self.ad_progress.setValue(elapsed)
        
        if self._ad_remaining_ms <= 0:
            # Next Ad
            self._current_ad_idx += 1
            self._load_next_ad()

    def _on_ad_clicked(self, event):
        """Handle click on ad image."""
        if self._current_ad_idx < len(self._popup_ads_data):
            ad = self._popup_ads_data[self._current_ad_idx]
            url = ad.get('url')
            if url:
                QDesktopServices.openUrl(QUrl(url))
                # Optional: Skip to next ad on click? Or just let it continue?
                # User usually wants to see the content, so maybe pause?
                # For now, let's keep it running.

    def _on_skip_ad(self):
        """Handle skip button."""
        # Skip current ad
        self._current_ad_idx += 1
        self._load_next_ad()

    def _recover_ui_from_ad_error(self):
        """从广告显示错误中恢复UI状态"""
        try:
            self._popup_ad_timer.stop()
            
            if hasattr(self, 'promo_tab'):
                idx = self.tab_widget.indexOf(self.promo_tab)
                if idx >= 0:
                    self.tab_widget.removeTab(idx)
                # Cleanup to free memory
                self.promo_tab.deleteLater()
                del self.promo_tab
                
            for i in range(self.tab_widget.count()):
                self.tab_widget.setTabEnabled(i, True)
            self.tab_widget.setCurrentWidget(self.mapping_tab)
            self.setMinimumSize(0, 0)
            self.setMaximumSize(16777215, 16777215)
        except Exception as e:
            logger.error(f"Failed to recover UI after ad processing error: {e}")

    def _update_scrolling_ad(self):
        """更新滚动广告标签"""
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
        """加载应用配置"""
        try:
            import yaml
            if self.app_config_path.exists():
                with open(self.app_config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    if isinstance(config, dict):
                        return config
        except Exception as e:
            logger.warning(f"加载app_config失败: {e}")
        return {"settings": {}}

    def _save_app_config(self):
        """保存应用配置"""
        try:
            import yaml
            self.app_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.app_config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(self.app_config, f, allow_unicode=True, sort_keys=False)
        except Exception as e:
            logger.warning(f"保存app_config失败: {e}")

    # --- Lifecycle and Callbacks ---
    def closeEvent(self, event: QCloseEvent):
        self.scrolling_ad_timer.stop()
        self._popup_ad_timer.stop()
        if self.app_core:
            self.app_core.cleanup()
        handle_close_event(self, event)
        
    def onFrpcTerminated(self):
        self.th = None
    def onLANPollerTerminated(self): self.lan_poller = None
    def on_servers_updated(self, new_servers):
        self.log("服务器列表已从网络更新。")
        self.SERVERS = new_servers
        self.mapping_tab.update_server_list(self.SERVERS)
        self.load_ping_values()
    
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
    def update_ad(self): self._update_scrolling_ad()
