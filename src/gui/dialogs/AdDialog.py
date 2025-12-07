# src/gui/dialogs/AdDialog.py

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy)
from PySide6.QtGui import QPixmap, QDesktopServices, QMouseEvent
from PySide6.QtCore import Qt, Signal, QTimer

class ClickableLabel(QLabel):
    """A QLabel that emits a 'clicked' signal when clicked."""
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class AdDialog(QDialog):
    """
    A dialog to display advertisements with images, remarks, and clickable links.
    Supports manual pagination and automatic slideshow.
    """
    def __init__(self, ad_data, parent=None):
        super().__init__(parent)
        self.ad_data = ad_data
        self.current_index = 0

        self.setWindowTitle("推广 (Promotions)")
        self.setMinimumSize(480, 320)

        self._init_ui()
        self._connect_signals()

        self.slideshow_timer = QTimer(self)
        self.slideshow_timer.setSingleShot(True)
        self.slideshow_timer.timeout.connect(self.show_next_ad)

        if self.ad_data:
            self.update_ad_content()

    def _init_ui(self):
        """Initializes the user interface of the dialog."""
        # Main layout
        layout = QVBoxLayout(self)

        # Image label
        self.image_label = ClickableLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.image_label)

        # Remark label
        self.remark_label = QLabel()
        self.remark_label.setAlignment(Qt.AlignCenter)
        self.remark_label.setWordWrap(True)
        layout.addWidget(self.remark_label)

        # Navigation buttons
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("上一张")
        self.next_button = QPushButton("下一张")
        nav_layout.addStretch()
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        nav_layout.addStretch()
        layout.addLayout(nav_layout)

    def _connect_signals(self):
        """Connects widget signals to corresponding slots."""
        self.prev_button.clicked.connect(self.show_previous_ad)
        self.next_button.clicked.connect(self.show_next_ad)
        self.image_label.clicked.connect(self.open_ad_url)
        
    def update_ad_content(self):
        """Updates the dialog content with the current ad."""
        if not self.ad_data:
            return

        ad = self.ad_data[self.current_index]
        
        # Update image
        pixmap = ad.get('pixmap')
        if pixmap:
            # Scale pixmap to fit the label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)

        # Update remark
        self.remark_label.setText(ad.get('remark', ''))

        # Restart slideshow timer
        self.slideshow_timer.stop()
        duration_ms = ad.get('duration', 5) * 1000  # convert s to ms
        self.slideshow_timer.start(duration_ms)

    def show_next_ad(self):
        """Shows the next advertisement in the list."""
        if not self.ad_data:
            return
        self.current_index = (self.current_index + 1) % len(self.ad_data)
        self.update_ad_content()

    def show_previous_ad(self):
        """Shows the previous advertisement in the list."""
        if not self.ad_data:
            return
        self.current_index = (self.current_index - 1 + len(self.ad_data)) % len(self.ad_data)
        self.update_ad_content()

    def open_ad_url(self):
        """Opens the URL associated with the current ad in a web browser."""
        if not self.ad_data:
            return
        ad = self.ad_data[self.current_index]
        url = ad.get('url')
        if url:
            QDesktopServices.openUrl(url)

    def resizeEvent(self, event):
        """Handle window resize to rescale the image."""
        super().resizeEvent(event)
        self.update_ad_content()

    def closeEvent(self, event):
        """Ensure the timer is stopped when the dialog is closed."""
        self.slideshow_timer.stop()
        super().closeEvent(event)

