import json
import urllib.request
from PySide6.QtCore import QThread, Signal, QTimer, QObject
from src.utils.HttpManager import fetch_url_content
from src.utils.LogManager import get_logger

logger = get_logger()

class LobbyService:
    """联机大厅服务类，负责与后端API交互"""
    API_BASE = "https://mapi.clash.ink/api/lobby"
    API_URL = f"{API_BASE}/rooms"
    HEARTBEAT_URL = f"{API_BASE}/heartbeat"
    ONLINE_URL = f"{API_BASE}/online"

    @staticmethod
    def get_rooms():
        """
        从服务器获取房间列表
        Returns:
            list: 房间字典列表，如果失败则返回空列表
        """
        try:
            content = fetch_url_content(LobbyService.API_URL)
            if not content:
                logger.error("Empty response from Lobby API")
                return []
            
            data = json.loads(content)
            if data.get("success"):
                return data.get("rooms", [])
            else:
                logger.warning(f"Lobby API returned failure: {data.get('message')}")
                return []
        except Exception as e:
            logger.error(f"Failed to fetch lobby rooms: {e}")
            return []

    @staticmethod
    def send_heartbeat():
        """发送用户在线心跳"""
        try:
            req = urllib.request.Request(
                LobbyService.HEARTBEAT_URL, 
                method="POST",
                headers={"Content-Type": "application/json", "User-Agent": "LMFP/1.3.1"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    @staticmethod
    def get_online_count():
        """获取在线用户数量"""
        try:
            content = fetch_url_content(LobbyService.ONLINE_URL)
            if content:
                data = json.loads(content)
                if data.get("success"):
                    return data.get("online_count", 0)
        except Exception:
            pass
        return 0

class LobbyWorker(QThread):
    """
    后台拉取房间列表的线程
    Signals:
        rooms_loaded (list): 拉取成功，携带房间列表
        error_occurred (str): 拉取失败，携带错误信息
    """
    rooms_loaded = Signal(list)
    error_occurred = Signal(str)

    def run(self):
        try:
            rooms = LobbyService.get_rooms()
            self.rooms_loaded.emit(rooms)
        except Exception as e:
            self.error_occurred.emit(str(e))

class OnlineCountWorker(QThread):
    """后台获取在线人数的线程"""
    online_count_updated = Signal(int)
    
    def run(self):
        try:
            count = LobbyService.get_online_count()
            self.online_count_updated.emit(count)
        except Exception:
            self.online_count_updated.emit(0)

class UserHeartbeatManager(QObject):
    """用户心跳管理器，每10秒发送一次心跳"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._send_heartbeat)
        self._worker = None
    
    def start(self):
        """启动心跳"""
        # 立即发送一次
        self._send_heartbeat()
        # 每10秒发送一次
        self._timer.start(10000)
    
    def stop(self):
        """停止心跳"""
        self._timer.stop()
        if self._worker and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait()
    
    def _send_heartbeat(self):
        """在后台线程发送心跳"""
        # 防止重入：如果上一次心跳还没完成，跳过本次
        if self._worker:
            try:
                if self._worker.isRunning():
                    return
            except RuntimeError:
                self._worker = None

        self._worker = HeartbeatWorker(self)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

class HeartbeatWorker(QThread):
    """后台发送心跳的线程"""
    def run(self):
        LobbyService.send_heartbeat()
