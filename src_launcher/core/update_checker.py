"""
更新检查模块
"""
import logging
import requests
from pathlib import Path
from src._version import __version__

logger = logging.getLogger("Launcher")

# 硬编码的URL
VERSION_URL = "https://z.clash.ink/chfs/shared/MinecraftFRP/Data/version.json"
INSTALLER_URL = "https://z.clash.ink/chfs/shared/MinecraftFRP/lastet/Minecraft_FRP_Installer.exe"


class UpdateChecker:
    """更新检查器"""
    
    def __init__(self):
        self.current_version = __version__
        self.latest_version = None
        self.download_url = INSTALLER_URL
    
    def check_update(self):
        """
        检查是否有更新
        返回: (has_update: bool, latest_version: str, download_url: str)
        """
        try:
            logger.info(f"Checking for updates... Current version: {self.current_version}")
            response = requests.get(VERSION_URL, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            self.latest_version = data.get("version", "0.0.0")
            
            logger.info(f"Latest version: {self.latest_version}")
            
            # 比较版本
            has_update = self._compare_versions(self.current_version, self.latest_version)
            
            return has_update, self.latest_version, self.download_url
            
        except Exception as e:
            logger.error(f"Failed to check update: {e}")
            return False, self.current_version, None
    
    def _compare_versions(self, current, latest):
        """比较版本号，如果latest > current返回True"""
        try:
            curr_parts = [int(x) for x in current.split('.')]
            latest_parts = [int(x) for x in latest.split('.')]
            
            # 补齐长度
            max_len = max(len(curr_parts), len(latest_parts))
            curr_parts.extend([0] * (max_len - len(curr_parts)))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            
            return latest_parts > curr_parts
        except:
            return False
