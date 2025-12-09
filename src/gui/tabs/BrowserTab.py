from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMenu
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl, Qt

class BrowserTab(QWidget):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.default_url = parent_window.app_config.get("app", {}).get(
            "browser_default_url",
            "https://b.clash.ink/archives/mi-ta-shan-lian-ji-gong-ju",
        )
        self.view = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        # 无地址栏与按钮，仅右键菜单提供控制
        try:
            from PySide6.QtWebEngineWidgets import QWebEngineView
            from PySide6.QtWebEngineCore import QWebEngineSettings
            self.view = QWebEngineView()
            s = self.view.settings()
            for attr in [
                QWebEngineSettings.JavascriptEnabled,
                QWebEngineSettings.AutoLoadImages,
                QWebEngineSettings.PluginsEnabled,
                QWebEngineSettings.FullScreenSupportEnabled,
                QWebEngineSettings.HyperlinkAuditingEnabled,
                QWebEngineSettings.ScrollAnimatorEnabled,
                QWebEngineSettings.TouchIconsEnabled,
                QWebEngineSettings.Accelerated2dCanvasEnabled,
                QWebEngineSettings.WebGLEnabled,
            ]:
                s.setAttribute(attr, True)
            # 右键菜单
            self.view.setContextMenuPolicy(Qt.CustomContextMenu)
            self.view.customContextMenuRequested.connect(self._show_context_menu)
            layout.addWidget(self.view)
            self.view.setUrl(QUrl(self.default_url))
        except Exception:
            layout.addWidget(QLabel("系统默认浏览器将用于打开链接。"))

    def _show_context_menu(self, pos):
        if not self.view:
            return
        menu = QMenu(self)
        back_act = menu.addAction("← 返回", self.view.back)
        fwd_act = menu.addAction("前进 →", self.view.forward)
        reload_act = menu.addAction("刷新", self.view.reload)
        ext_act = menu.addAction("用系统浏览器打开", lambda: QDesktopServices.openUrl(self.view.url()))
        menu.exec(self.view.mapToGlobal(pos))
