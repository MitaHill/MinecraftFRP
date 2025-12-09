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
        # 快速拒绝常见Web端口
        if port in (80, 443, 8080, 8000, 8888, 3000, 5000, 9000):
            return True
        # HTTP检测（含响应体特征）
        try:
            conn = http.client.HTTPConnection('127.0.0.1', port, timeout=2)
            conn.request('GET', '/')
            resp = conn.getresponse()
            body = resp.read(4096).decode('utf-8', errors='ignore').lower()
            # 检测HTML特征
            if any(kw in body for kw in ['<html', '<head', '<body', '<!doctype', '<script', 'content-type', 'text/html']):
                return True
            # 任意200-5xx响应视为HTTP服务
            if 200 <= resp.status < 600:
                return True
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass
        # HTTPS TLS检测
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with socket.create_connection(('127.0.0.1', port), timeout=2) as sock:
                with ctx.wrap_socket(sock, server_hostname='localhost') as ssock:
                    # TLS握手成功即视为HTTPS服务
                    return True
        except ssl.SSLError:
            return True
        except Exception:
            pass
        return False
