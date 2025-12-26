from PySide6.QtCore import QObject, Signal, QThread
from src.utils.LogManager import get_logger
from src.core.ServerManager import ServerManager
from src.core.SecurityService import SecurityService
from src.gui.dialogs.AdThread import AdThread
from pathlib import Path
import json

logger = get_logger()

class SecurityCheckWorker(QObject):
    """独立的工作对象，用于执行安全检查"""
    finished = Signal(bool, str)

    def run(self):
        passed, reason = SecurityService.perform_startup_check()
        self.finished.emit(passed, reason)

class AppCore(QObject):
    """
    应用程序核心控制器 (Backend)
    负责协调所有非UI逻辑：安全检查、数据加载、后台任务等。
    """
    # 信号定义 (用于通知前端)
    initialization_progress = Signal(str) # 初始化进度消息
    security_check_passed = Signal()      # 安全检查通过
    security_check_failed = Signal(str)   # 安全检查失败
    server_list_loaded = Signal(dict)     # 服务器列表加载完成
    ads_ready = Signal(dict)              # 广告数据准备就绪
    error_occurred = Signal(str)          # 通用错误信号

    def __init__(self, docs_dir: Path):
        super().__init__()
        self.docs_dir = docs_dir
        self.server_manager = None
        self.ad_thread = None
        self.security_thread = None
        self.security_worker = None

    def start_initialization(self):
        """开始应用程序的初始化流程"""
        logger.info("AppCore: Starting initialization sequence...")
        
        # 1. 加载基础信息
        self._load_version_info()
        
        # 2. 启动安全检查 (在独立线程中)
        self._start_security_check()

    def _load_version_info(self):
        from src.version import get_version_string, VERSION, GIT_HASH
        
        channel = "unknown"
        try:
            install_info_path = self.docs_dir / "install_info.json"
            if install_info_path.exists():
                with open(install_info_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    channel = data.get('channel', 'unknown')
        except Exception:
            pass
        
        self.channel = channel
        version_str = get_version_string()
        logger.info(f"AppCore: Version: {VERSION}, Channel: {channel}")

    def _start_security_check(self):
        logger.info("AppCore: Starting security check...")
        self.security_thread = QThread()
        self.security_worker = SecurityCheckWorker()
        self.security_worker.moveToThread(self.security_thread)
        
        self.security_thread.started.connect(self.security_worker.run)
        self.security_worker.finished.connect(self._on_security_check_finished)
        self.security_worker.finished.connect(self.security_thread.quit)
        self.security_worker.finished.connect(self.security_worker.deleteLater)
        self.security_thread.finished.connect(self.security_thread.deleteLater)
        
        self.security_thread.start()

    def _on_security_check_finished(self, passed, reason):
        if not passed:
            logger.warning(f"AppCore: Security check failed: {reason}")
            self.security_check_failed.emit(reason)
        else:
            logger.info("AppCore: Security check passed.")
            self.security_check_passed.emit()
            # 安全检查通过后，继续后续加载
            self._continue_loading()

    def _continue_loading(self):
        """安全检查通过后继续加载资源"""
        try:
            # 3. 加载服务器列表
            self.server_manager = ServerManager()
            servers = self.server_manager.get_servers()
            self.server_list_loaded.emit(servers)
            
            # 4. 启动广告获取
            self._start_ad_fetching()
            
        except Exception as e:
            logger.error(f"AppCore: Error during resource loading: {e}", exc_info=True)
            self.error_occurred.emit(f"资源加载失败: {str(e)}")

    def _start_ad_fetching(self):
        self.ad_thread = AdThread()
        self.ad_thread.finished.connect(self._on_ads_fetched)
        self.ad_thread.start()

    def _on_ads_fetched(self, ad_data):
        self.ads_ready.emit(ad_data)

    def cleanup(self):
        """清理资源"""
        if self.security_thread and self.security_thread.isRunning():
            self.security_thread.quit()
            self.security_thread.wait()
