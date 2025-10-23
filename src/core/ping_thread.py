from PySide6.QtCore import QThread, Signal
from src.network.ping_utils import ping_host

class PingThread(QThread):
    ping_results = Signal(dict)

    def __init__(self, servers):
        super().__init__()
        self.servers = servers

    def run(self):
        results = {}
        for name, (host, _, _) in self.servers.items():
            ping = ping_host(host)
            item_text = f"{name}    {ping}ms" if ping is not None else f"{name}    timeout"
            results[name] = item_text
        self.ping_results.emit(results)