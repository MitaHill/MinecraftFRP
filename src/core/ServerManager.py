import json
from typing import Dict, Tuple, Optional
from src.network.PingUtils import download_json, read_json_file
from src.utils.Crypto import decrypt_data, load_servers_from_json
from src.utils.LogManager import get_logger

logger = get_logger()

# 加密后的默认服务器列表 (Anti-Cracking)
DEFAULT_SERVERS_ENCRYPTED = (
    "tpYiHuAnqdnDx8y23klPcTac7oSB2NdKRfUNJDo50xAwlwFip7+zDVQn+SpYDitLEqG3fBSWAEWWuYL7hjQClWaq1JuuEqBT5lo4E+xvtS2iE1V826A1/gDIW4LnFl6ZGqmiRr2DJ5jBdhawL"
    "/iSDZ/w1skd5PChRqWseWIppjuEbzzik7DTzKYPIOGtx5s6b4/J6BvXYehI0qCaCkSoYxvvPXu0TNIr6U7fCaAZuG6oyg1Cp0L3+2bTIptKPdSefrs10NMM1oHP8g1MbSR30JioEC5cSqXHKE"
    "crMO6Bf+4eHn8PTeyc89peBOx96ALTsud15TojUp+pD4edv/Jgi+9doLg393gF0KCK9jCHGYPqsGdZDcRVwATtaUhERdbxJeEojhuOBOhadS5IMdkZjZqGlr5zT2SA7oi730lfWq30cShJ5Gf"
    "Icqn6Vd1+TkBV5aV9IaGXemJAlbZs7eR9efbC9nto4L1L7KdWaDSzBjU5B3fCRQJSbQ9U6m8eiZX4iZteAW4H3i+IsPXSUgNBUsvtb01dSrvtxQHPnY20cgoKeO1iUaGa6afhGKR2ycnG3b34"
    "6oO1DHeRBHuSQYJ0vjWkJuYDDUDk1sLZy87J6IeoasgF5aDxg7dQY0r9NB57"
)

class ServerManager:
    def __init__(self):
        # 简单的密钥混淆
        k_part1 = "clash"
        k_part2 = "man"
        self.key = k_part1 + k_part2

        # 首先加载内置的，然后尝试从本地文件覆盖
        self.servers = self._load_default_servers()
        self._load_servers_from_local()

    def _load_default_servers(self) -> Dict[str, Tuple[str, int, str]]:
        """加载并解密内置的默认服务器列表"""
        try:
            decrypted = decrypt_data(DEFAULT_SERVERS_ENCRYPTED, self.key)
            if decrypted:
                json_data = json.loads(decrypted)
                return load_servers_from_json(json_data)
        except Exception as e:
            logger.error(f"无法加载内置服务器列表: {e}")
        return {}

    def _load_servers_from_local(self) -> None:
        """从本地文件加载服务器列表，不进行网络下载"""
        local_path = "config/frp-server-list.json"
        encrypted_data = read_json_file(local_path)
        if not encrypted_data:
            logger.info("本地服务器列表文件不存在或为空，使用内置列表。")
            return

        try:
            decrypted_data = decrypt_data(encrypted_data, self.key)
            if decrypted_data:
                json_data = json.loads(decrypted_data)
                servers = load_servers_from_json(json_data)
                if servers:
                    self.servers = servers
                    logger.info("已从本地文件加载服务器列表。")
        except Exception as e:
            logger.error(f"从本地文件加载服务器列表失败: {e}，将使用内置列表。")

    def update_servers_from_network(self) -> Optional[Dict[str, Tuple[str, int, str]]]:
        """从网络下载并更新服务器列表，返回新的服务器字典"""
        url = "https://clash.ink/file/frp-server-list.json"
        local_path = "config/frp-server-list.json"

        if not download_json(url, local_path):
            logger.warning("下载新的服务器列表失败。")
            return None

        logger.info("成功下载新的服务器列表文件。")
        encrypted_data = read_json_file(local_path)
        if encrypted_data:
            try:
                decrypted_data = decrypt_data(encrypted_data, self.key)
                if decrypted_data:
                    json_data = json.loads(decrypted_data)
                    servers = load_servers_from_json(json_data)
                    if servers:
                        self.servers = servers
                        logger.info("成功从网络更新并加载服务器列表。")
                        return servers
            except Exception as e:
                logger.error(f"解析下载的服务器列表失败: {e}")

        return None

    def get_servers(self) -> Dict[str, Tuple[str, int, str]]:
        return self.servers