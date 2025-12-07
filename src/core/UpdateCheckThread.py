from PySide6.QtCore import QThread, Signal
from src.utils.HttpManager import fetch_url_content
import json
from packaging.version import parse
from src.utils.LogManager import get_logger

logger = get_logger()

class UpdateCheckThread(QThread):
    """
    Checks for application updates in a background thread.
    """
    update_info_fetched = Signal(dict)
    error_occurred = Signal(str)
    up_to_date = Signal()

    VERSION_URL = "https://z.clash.ink/chfs/shared/MinecraftFRP/Data/version.json"

    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version

    def run(self):
        """
        Performs a network request to get the latest version.json.
        Emits a signal with the new version info if an update is available.
        """
        logger.info("Background update check thread started.")
        
        try:
            content = fetch_url_content(self.VERSION_URL)
            version_info = json.loads(content)
            
            if not version_info.get("version"):
                logger.warning("Update information is missing the 'version' key.")
                self.error_occurred.emit("Update info is malformed.")
                return

            server_version = version_info["version"]
            
            # Compare versions
            if parse(server_version) > parse(self.current_version):
                logger.info(f"New version found: {server_version}. Emitting update signal.")
                self.update_info_fetched.emit(version_info)
            else:
                logger.info("Application is up to date.")
                self.up_to_date.emit()

        except Exception as e:
            error_message = f"An unknown error occurred during update check: {e}"
            logger.error(error_message)
            self.error_occurred.emit(error_message)
