"""
配置管理器
管理安装信息和用户配置
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfigManager:
    CONFIG_FILENAME = "install_info.json"
    
    def __init__(self):
        self.config_dir = self.get_config_dir()
        self.config_file = self.config_dir / self.CONFIG_FILENAME
        
    def get_config_dir(self) -> Path:
        """获取配置目录"""
        username = os.environ.get('USERNAME', 'User')
        config_dir = Path(f"C:\\Users\\{username}\\Documents\\MitaHillFRP")
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    def get_install_info(self) -> Optional[Dict]:
        """读取安装信息"""
        if not self.config_file.exists():
            return None
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Found previous installation at {data.get('install_path')}")
                return data
        except Exception as e:
            logger.error(f"Failed to read install info: {e}")
            return None
    
    def save_install_info(self, install_path: str, version: str = "0.5.32"):
        """保存安装信息"""
        try:
            data = {
                "install_path": install_path,
                "version": version,
                "install_date": datetime.now().isoformat(),
                "last_update": datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Saved install info to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save install info: {e}")
    
    def remove_install_info(self):
        """删除安装信息"""
        try:
            if self.config_file.exists():
                self.config_file.unlink()
                logger.info("Removed install info")
        except Exception as e:
            logger.error(f"Failed to remove install info: {e}")
