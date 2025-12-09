import socket, ssl, http.client, time
from threading import Thread, Event
from typing import Callable

class WebGuard:
    """Detects HTTP/HTTPS services on a local port and triggers a callback to stop mapping."""
    def __init__(self, port_getter: Callable[[], int], stop_callback: Callable[[str], None], interval_sec: int = 30):
        self.port_getter = port_getter
        self.stop_callback = stop_callback
        self.interval = max(10, interval_sec)
        self._th = None
        self._stop = Event()

    def start(self):
        if self._th and self._th.is_alive():
            return
        self._stop.clear()
        self._th = Thread(target=self._loop, daemon=True)
        self._th.start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        # immediate check, then periodic
        while not self._stop.is_set():
            port = self.port_getter() or 0
            if port and self._is_web_service(port):
                self.stop_callback(f"检测到本地端口 {port} 运行HTTP/HTTPS服务，已终止映射以防建站。")
                break
            for _ in range(self.interval):
                if self._stop.is_set():
                    return
                time.sleep(1)

    def _is_web_service(self, port: int) -> bool:
        # quick deny for common web ports
        if port in (80, 443, 8080, 8000, 8888):
            return True
        # HTTP HEAD
        try:
            conn = http.client.HTTPConnection('127.0.0.1', port, timeout=2)
            conn.request('HEAD', '/')
            resp = conn.getresponse()
            if resp.status in (200, 301, 302, 403, 404):
                return True
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass
        # HTTPS TLS + HEAD
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection(('127.0.0.1', port), timeout=2) as sock:
                with ctx.wrap_socket(sock, server_hostname='localhost') as ssock:
                    conn = http.client.HTTPSConnection('127.0.0.1', port, timeout=2, context=ctx)
                    conn.request('HEAD', '/')
                    resp = conn.getresponse()
                    if resp.status in (200, 301, 302, 403, 404):
                        return True
        except Exception:
            pass
        return False
