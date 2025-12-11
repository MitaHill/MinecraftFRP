import logging
from PySide6.QtCore import QObject, Signal

class QtSignalHandler(logging.Handler, QObject):
    """
    Custom logging handler that emits a signal for each log record.
    Used to display logs in a GUI widget.
    """
    log_record = Signal(str)

    def __init__(self, parent=None):
        logging.Handler.__init__(self)
        QObject.__init__(self, parent)

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_record.emit(msg)
        except Exception:
            self.handleError(record)
