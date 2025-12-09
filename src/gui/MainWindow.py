import tempfile
import os
import sys
import subprocess
from PySide6.QtCore import QMutex, QTimer, Qt
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtGui import QCloseEvent

# Core Imports
from src.core.ServerManager import ServerManager
from src.core.DownloadThread import DownloadThread
from src.core.UpdateCheckThread import UpdateCheckThread
from src._version import __version__ as APP_VERSION
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
from src.gui.main_window.Actions import open_help_browser, open_server_management_dialog
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
        self.ad_thread = None
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
        self.app_config = {"settings": {}}
        
        setup_main_window_ui(self, self.SERVERS)
        QTimer.singleShot(50, self.deferred_initialization)

    def deferred_initialization(self):
        """Deferred initialization: executes heavy tasks after the window is shown."""
        logger.info("Performing deferred initialization...")

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
        
        # Setup and start update check thread
        self.update_checker_thread = UpdateCheckThread(current_version=APP_VERSION)
        self.update_checker_thread.update_info_fetched.connect(self.show_update_dialog)
        self.update_checker_thread.error_occurred.connect(self.show_update_error)
        self.update_checker_thread.up_to_date.connect(self.show_up_to_date_message)
        self.update_checker_thread.start()

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
        if not self.is_closing and popup_ads:
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
            from PySide6.QtCore import QUrl
            promo_tab = QWidget()
            v = QVBoxLayout(promo_tab)
            v.setContentsMargins(8, 8, 8, 8)
            v.setSpacing(6)
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignCenter)
            # 固定显示区域，避免触发布局扩张
            lbl.setFixedSize(480, 270)
            lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            lbl.setScaledContents(False)
            v.addWidget(lbl)
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
            from PySide6.QtWidgets import QProgressBar
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(0)
            v.addWidget(progress)
            # 轮播显示，每条广告使用其duration
            from PySide6.QtCore import QTimer
            self._promo_ads = popup_ads
            self._promo_idx = 0
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
                    self._promo_progress_timer.timeout.disconnect()
                except Exception:
                    pass
                progress.setValue(0)
                if self._promo_idx >= len(self._promo_ads):
                    # 结束：移除推广标签，解锁并跳转到“映射”
                    idx = self.tab_widget.indexOf(promo_tab)
                    if idx >= 0:
                        self.tab_widget.removeTab(idx)
                    for i in range(self.tab_widget.count()):
                        self.tab_widget.setTabEnabled(i, True)
                    self.tab_widget.setCurrentWidget(self.mapping_tab)
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
                # 显示图片（仅缩小不放大）
                if pix:
                    try:
                        from PySide6.QtGui import QPixmap
                        max_w, max_h = 480, 270
                        target_w = min(max_w, pix.width())
                        target_h = min(max_h, pix.height())
                        scaled = pix.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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
                def tick():
                    elapsed["v"] += 100
                    pct = min(100, int(elapsed["v"] * 100 / dur_ms))
                    progress.setValue(pct)
                self._promo_progress_timer.timeout.connect(tick)
                self._promo_progress_timer.start()
                QTimer.singleShot(dur_ms, show_next)
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
        self.th = None
    def onLANPollerTerminated(self): self.lan_poller = None
    def on_servers_updated(self, new_servers):
        self.log("服务器列表已从网络更新。")
        self.SERVERS = new_servers
        self.mapping_tab.update_server_list(self.SERVERS)
        self.load_ping_values()
        
    def show_update_dialog(self, version_info):
        """Shows the update dialog when a new version is found."""
        try:
            server_version = version_info.get("version", "0.0.0")
            self.log(f"检测到新版本: {server_version}, 当前版本: {APP_VERSION}。即将提示用户...")
            release_notes = version_info.get("release_notes", "无更新说明。")
            msg_box = QMessageBox(self); msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("发现新版本"); msg_box.setText(f"发现新版本 {server_version}！")
            msg_box.setInformativeText(f"<b>更新日志:</b><br><pre>{release_notes}</pre><br>是否立即下载并更新？")
            update_button = msg_box.addButton("立即更新", QMessageBox.AcceptRole)
            later_button = msg_box.addButton("稍后提醒", QMessageBox.RejectRole)
            msg_box.exec()
            if msg_box.clickedButton() == update_button:
                self.start_download(version_info)
            else:
                self.log("用户选择稍后更新。")
        except Exception as e:
            logger.error(f"处理更新信息时出错: {e}")

    def show_up_to_date_message(self):
        """Handles the signal for when the application is already up to date."""
        self.log("当前已是最新版本。", "green")

    def show_update_error(self, error_message):
        """Handles the signal for when an error occurs during update check."""
        self.log(f"检查更新失败: {error_message}", "orange")

    def start_download(self, version_info):
        """Starts downloading the update file."""
        self.log("开始下载更新...")
        self.current_update_info = version_info
        download_url = version_info.get("download_url")
        if not download_url:
            self.log("错误：更新信息中未找到下载地址。", "red"); return

        dialog = UpdateDownloadDialog(self)
        save_path = os.path.join(tempfile.gettempdir(), f"MinecraftFRP_Update_{version_info['version']}.exe")
        self.download_thread = DownloadThread(download_url, save_path)
        dialog.download_thread = self.download_thread
        
        self.download_thread.download_progress.connect(dialog.update_progress)
        self.download_thread.download_finished.connect(self.on_download_finished)
        self.download_thread.error_occurred.connect(self.on_download_error)
        
        self.download_thread.start()
        dialog.exec()

    def on_download_finished(self, saved_path):
        """Callback after download is complete, performs validation."""
        self.log(f"更新下载完成: {saved_path}", "green")
        
        try:
            expected_hash = self.current_update_info.get("sha256")
            if not expected_hash:
                self.log("警告: 版本信息中未提供SHA256哈希值，跳过文件校验。", "orange")
                self.execute_update(saved_path)
                return

            self.log("正在校验文件完整性...")
            actual_hash = calculate_sha256(saved_path)
            
            if actual_hash.lower() == expected_hash.lower():
                self.log("文件校验成功！", "green")
                self.execute_update(saved_path)
            else:
                logger.error(f"文件校验失败！预期哈希: {expected_hash}, 实际哈希: {actual_hash}")
                self.on_download_error("文件校验失败！文件可能已损坏或被篡改。")
                os.remove(saved_path)
                
        except Exception as e:
            self.on_download_error(f"文件校验过程中发生错误: {e}")

    def execute_update(self, downloaded_path):
        """Releases and executes the updater."""
        self.log("准备执行更新...", "cyan")
        try:
            updater_path_in_exe = get_resource_path("updater.exe")
            
            updater_temp_path = os.path.join(tempfile.gettempdir(), "mcfrp_updater.exe")
            with open(updater_path_in_exe, "rb") as f_in:
                with open(updater_temp_path, "wb") as f_out:
                    f_out.write(f_in.read())
            
            os.chmod(updater_temp_path, 0o755)

            pid = str(os.getpid())
            current_exe_path = os.path.abspath(sys.argv[0])
            log_dir_path = os.path.join(os.path.dirname(current_exe_path), "logs")

            self.log("启动更新进程，本程序即将退出。")
            DETACHED_PROCESS = 0x00000008
            
            args = [updater_temp_path, pid, current_exe_path, downloaded_path, log_dir_path]
            logger.info(f"启动更新器，参数: {args}")

            subprocess.Popen(
                args,
                creationflags=DETACHED_PROCESS,
                close_fds=True
            )
            
            self.close()

        except Exception as e:
            logger.error(f"启动更新程序时发生致命错误: {e}")
            self.on_download_error(f"执行更新时出错: {e}")

    def on_download_error(self, error_message):
        """Callback for download failure."""
        self.log(f"下载失败: {error_message}", "red")
        QMessageBox.critical(self, "下载失败", error_message)

    def update_ad(self):
        ad = self.ad_manager.get_next_ad()
        color = "cyan" if self.theme == "dark" else "blue"
        text = f'<a href="{ad["url"]}" style="color:{color}">{ad["show"]}</a>' if ad else "无广告"
        self.mapping_tab.ad_label.setText(text)

    # --- Proxy methods for signal/event connections ---
    def set_port(self, port): set_port(self, port)
    def start_map(self): start_map(self)
    def copy_link(self): copy_link(self)
    def update_server_combo(self, results): update_server_combo(self, results)
    def on_auto_mapping_changed(self, state): on_auto_mapping_changed(self, state)
    def on_dark_mode_changed(self, state): on_dark_mode_changed(self, state)
    def on_server_changed(self, text): on_server_changed(self, text)
    def open_server_management(self): open_server_management_dialog(self)
    def start_web_browser(self): open_help_browser(self)
    def load_ping_values(self): load_ping_values(self)
    def log(self, message, color=None): log_message(self, message, color)
