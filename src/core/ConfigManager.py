import os
from threading import Lock
from pathlib import Path
from src.utils.LogManager import get_logger

logger = get_logger()

class ConfigManager:
    def __init__(self, filename="frpc.ini"):
        # 确保config目录存在
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        # 配置文件放在config目录中
        self.filename = config_dir / filename
        self.mutex = Lock()

    def create_config(self, host: str, port: int, token: str, local_port: int, remote_port: int, user_id: int) -> bool:
        with self.mutex:
            # 根据文件后缀生成对应的配置格式（INI 或 TOML）
            if str(self.filename).endswith(".toml"):
                config_content = (
                    f"serverAddr = \"{host}\"\n"
                    f"serverPort = {port}\n\n"
                    f"[[proxies]]\n"
                    f"name = \"mc_{remote_port}\"\n"
                    f"type = \"tcp\"\n"
                    f"localIP = \"127.0.0.1\"\n"
                    f"localPort = {local_port}\n"
                    f"remotePort = {remote_port}\n"
                )
            else:
                config_content = f"""[common]
server_addr={host}
server_port={port}
token={token}

[map{user_id}]
type=tcp
local_ip=127.0.0.1
local_port={local_port}
remote_port={remote_port}
"""
            try:
                with open(self.filename, "w", encoding="utf-8") as f:
                    f.write(config_content)
                return True
            except Exception as e:
                logger.error(f"写入配置文件出错: {e}")
                return False

    def delete_config(self) -> bool:
        with self.mutex:
            try:
                if os.path.exists(self.filename):
                    os.remove(self.filename)
                    return True
            except Exception as e:
                logger.error(f"删除配置文件出错: {e}")
            return False