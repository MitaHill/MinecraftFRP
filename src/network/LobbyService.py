import json
from PySide6.QtCore import QThread, Signal
from src.utils.HttpManager import fetch_url_content
from src.utils.LogManager import get_logger

logger = get_logger()

class LobbyService:
    """联机大厅服务类，负责与后端API交互"""
    API_URL = "https://mapi.clash.ink/api/lobby/rooms"

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
