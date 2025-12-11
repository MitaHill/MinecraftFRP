import os
import shutil
from threading import Lock
from pathlib import Path
from src.utils.LogManager import get_logger

logger = get_logger()

class ConfigManager:
    def __init__(self, filename="frpc.ini"):
        self.mutex = Lock()
        # 使用用户文档下的隐藏临时目录
        docs_dir = Path.home() / "Documents" / "MitaHillFRP"
        self.temp_dir = docs_dir / ".temp"
        
        try:
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            # 在Windows上设置隐藏属性
            if os.name == 'nt':
                try:
                    import ctypes
                    FILE_ATTRIBUTE_HIDDEN = 0x02
                    ctypes.windll.kernel32.SetFileAttributesW(str(self.temp_dir), FILE_ATTRIBUTE_HIDDEN)
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"创建临时目录失败: {e}")
            
        self.filename = self.temp_dir / filename

    def create_config(self, host: str, port: int, token: str, local_port: int, remote_port: int, user_id: int) -> bool:
        with self.mutex:
            # 根据文件后缀生成对应的配置格式（INI 或 TOML）
            # 注意：此处文件名可能通过 self.filename 获取后缀，或者默认 .ini
            suffix = Path(self.filename).suffix or ".ini"
            
            if suffix == ".toml":
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
                # 为每次运行生成唯一的配置文件名，避免冲突
                unique_name = f"frpc_{os.getpid()}_{user_id}{suffix}"
                self.filename = self.temp_dir / unique_name
                
                with open(self.filename, "w", encoding="utf-8") as f:
                    f.write(config_content)
                return True
            except Exception as e:
                logger.error(f"写入配置文件出错: {e}")
                return False

    def delete_config(self) -> bool:
        with self.mutex:
            try:
                if self.filename and os.path.exists(self.filename):
                    try:
                        os.chmod(self.filename, 0o600)
                    except Exception:
                        pass
                    os.remove(self.filename)
                    return True
            except Exception as e:
                logger.error(f"删除配置文件出错: {e}")
            return False

    @staticmethod
    def cleanup_temp_dir():
        """清理整个临时目录"""
        try:
            docs_dir = Path.home() / "Documents" / "MitaHillFRP"
            temp_dir = docs_dir / ".temp"
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f"清理临时目录失败: {e}")