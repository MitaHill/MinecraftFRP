import os
import yaml
from pathlib import Path

class YamlConfigManager:
    """YAML配置文件管理器"""
    
    def __init__(self, config_dir="config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
    def load_config(self, filename, default_config=None):
        """加载YAML配置文件"""
        config_path = self.config_dir / filename
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"读取配置文件 {filename} 失败: {e}")
                if default_config:
                    self.save_config(filename, default_config)
                    return default_config
        else:
            if default_config:
                self.save_config(filename, default_config)
                return default_config
                
        return {}
    
    def save_config(self, filename, config):
        """保存YAML配置文件"""
        config_path = self.config_dir / filename
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件 {filename} 失败: {e}")
            return False
    
    def get_config_path(self, filename):
        """获取配置文件完整路径"""
        return self.config_dir / filename

# 默认应用配置
DEFAULT_APP_CONFIG = {
    "app": {
        "name": "Minecraft FRP Tool",
        "version": "2.0.0",
        "theme": "auto"  # auto, light, dark
    },
    "frp": {
        "config_filename": "frpc.ini",
        "thread_timeout": 3000,
        "ping_data_filename": "ping_data.yaml"
    },
    "decrypt_key": "clashman",
    "network": {
        "ping_timeout": 1000,
        "download_timeout": 5,
        "reserved_ports": [80, 443, 3306, 8080, 25565]
    },
    "ui": {
        "window_width": 400,
        "window_height": 550,
        "ad_update_interval": 3000,
        "ping_update_interval": 3000
    },
    "settings": {
        "auto_mapping": False,  # 自动映射开关
        "dark_mode_override": False,  # 手动主题模式覆盖
        "force_dark_mode": False  # 强制夜间模式
    }
}