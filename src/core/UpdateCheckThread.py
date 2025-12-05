from PySide6.QtCore import QThread, Signal
import requests
import json
from src.utils.LogManager import get_logger

logger = get_logger()

class UpdateCheckThread(QThread):
    """
    在后台线程检查应用更新。
    """
    update_info_fetched = Signal(dict)
    error_occurred = Signal(str)

    VERSION_URL = "https://z.clash.ink/chfs/shared/MinecraftFRP/version.json"

    def __init__(self):
        super().__init__()

    def run(self):
        """
        在后台执行网络请求，获取最新的 version.json。
        成功后，通过信号发送新的版本信息。
        """
        logger.info("后台更新检查线程已启动。")
        
        try:
            response = requests.get(self.VERSION_URL, timeout=10)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
            
            version_info = response.json()
            
            if version_info:
                self.update_info_fetched.emit(version_info)
                logger.info("成功获取到更新信息，并已发送信号。")
            else:
                logger.warning("获取到的更新信息为空。")
                self.error_occurred.emit("获取到的更新信息为空。")

        except requests.exceptions.RequestException as e:
            error_message = f"检查更新时发生网络错误: {e}"
            logger.error(error_message)
            self.error_occurred.emit(error_message)
        except json.JSONDecodeError as e:
            error_message = f"解析更新信息失败 (无效的JSON): {e}"
            logger.error(error_message)
            self.error_occurred.emit(error_message)
        except Exception as e:
            error_message = f"检查更新时发生未知错误: {e}"
            logger.error(error_message)
            self.error_occurred.emit(error_message)
