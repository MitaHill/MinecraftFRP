import os
from threading import Lock
from pathlib import Path
from src.utils.LogManager import get_logger

logger = get_logger()

class ConfigManager:
    def __init__(self, filename="frpc.ini"):
        # 优先使用系统临时目录，失败则回退到项目 config 目录
        self.mutex = Lock()
        tmp_dir = Path(os.environ.get('TEMP') or os.environ.get('TMP') or 'tmp')
        fallback_dir = Path("config")
        try:
            tmp_dir.mkdir(exist_ok=True)
            test_path = tmp_dir / (".wtest_" + filename)
            with open(test_path, "w", encoding="utf-8") as f:
                f.write("")
            os.remove(test_path)
            self.filename = tmp_dir / filename
        except Exception:
            fallback_dir.mkdir(exist_ok=True)
            self.filename = fallback_dir / filename

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
                # 先用 NamedTemporaryFile 验证路径可写，增加兼容性
                import tempfile
                base = Path(self.filename)
                tmp_test = None
                try:
                    tmp_test = tempfile.NamedTemporaryFile(prefix="frpc_", suffix=base.suffix or ".ini", dir=str(base.parent), delete=False)
                    tmp_test.close()
                    os.remove(tmp_test.name)
                except Exception:
                    pass
                # 为每次运行生成唯一的配置文件名，避免权限冲突
                unique_path = base.with_name(f"{base.stem}_{os.getpid()}_{user_id}{base.suffix}")
                self.filename = unique_path
                with open(self.filename, "w", encoding="utf-8") as f:
                    f.write(config_content)
                # 设置为仅当前用户可读写，避免删除失败
                try:
                    os.chmod(self.filename, 0o600)
                except Exception:
                    pass
                return True
            except Exception as e:
                logger.error(f"写入配置文件出错: {e}")
                # 回退到项目 config 目录再试一次
                try:
                    fallback_dir = Path("config"); fallback_dir.mkdir(exist_ok=True)
                    base = Path(self.filename)
                    fallback_path = fallback_dir / f"{base.stem}_{os.getpid()}_{user_id}{base.suffix}"
                    with open(fallback_path, "w", encoding="utf-8") as f:
                        f.write(config_content)
                    try:
                        os.chmod(fallback_path, 0o600)
                    except Exception:
                        pass
                    self.filename = fallback_path
                    return True
                except Exception as e2:
                    logger.error(f"写入回退配置文件仍失败: {e2}")
                    return False

    def delete_config(self) -> bool:
        with self.mutex:
            try:
                if os.path.exists(self.filename):
                    try:
                        os.chmod(self.filename, 0o600)
                    except Exception:
                        pass
                    os.remove(self.filename)
                    return True
            except Exception as e:
                logger.error(f"删除配置文件出错: {e}")
            return False