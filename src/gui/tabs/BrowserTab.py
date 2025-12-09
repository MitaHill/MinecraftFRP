from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl

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
        url_bar = QHBoxLayout()
        self.url_edit = QLineEdit(self.default_url)
        go_btn = QPushButton("打开")
        go_btn.clicked.connect(self.open_url)
        url_bar.addWidget(QLabel("地址:"))
        url_bar.addWidget(self.url_edit)
        url_bar.addWidget(go_btn)
        layout.addLayout(url_bar)

        # 尝试使用内置小型浏览器（QWebEngine），失败则退回系统浏览器
        try:
            from PySide6.QtWebEngineWidgets import QWebEngineView
            self.view = QWebEngineView()
            layout.addWidget(self.view)
            self.view.setUrl(QUrl(self.default_url))
        except Exception:
            layout.addWidget(QLabel("系统默认浏览器将用于打开链接。"))

    def open_url(self):
        url = self.url_edit.text().strip() or self.default_url
        if self.view:
            self.view.setUrl(QUrl(url))
        else:
            QDesktopServices.openUrl(QUrl(url))
