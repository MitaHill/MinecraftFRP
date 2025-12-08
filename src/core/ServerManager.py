import json
from typing import Dict, Tuple, Optional
from src.network.PingUtils import download_json, read_json_file
from src.utils.Crypto import decrypt_data, load_servers_from_json
from src.utils.LogManager import get_logger

logger = get_logger()

# 加密后的默认服务器列表 (Anti-Cracking) - 包含特殊节点
DEFAULT_SERVERS_ENCRYPTED = (
    "pZRl39qlwvH6E3jTxG7FyQNxIBuUs27pryM6VNV2hjhDlZh8tCtmtBcVglI7UP/5Pj6+h+ks01+sQ4oqiC9HiK3TdxdIE4tPb1bV7OqDhGTE7LR8ZXT3T8Qmg7xsX4Tr5aj36qHZPfjOJ+p2Z70uHs7LUtCrjv86pVmZsQ+rts9wvaKp7K/t2HGVwWTDhQeGQH6MIopged9AqihEgXKyFucfAjU/IHk+6QeJ9mLaj4Xvl1tysPsj2n1owQTJpGoe/mQW9OZX/RyVlZPF8auNWY0F02jAFR89WCM3G3gF5SE4aSZjIly65Y0H/0yNeU+iXL7x4hRx9Lof9gSLLv3ZqcEtiBhUa7sE2rPS2JG3J/M9NJeG5bw2gCaWOxZRQoVkvXnUswa0E1MFwiy7X7EFlZqcBd+E9u/qQwrtHaBOg14f61Y2CIFpNFMyw+TkSj1XvtKAG61rTOOVWG1VRLUj24uocCPe4yMLaYIEYyIzJu9WUviJ9kobs3nZCcc8nZn8iPug7cRfgJvufmCe+wUsmiDLpk9sG2SR80l1PEp0xvvmtIIgY6W2RTJyDNl4T9XpgRn2n/sW2rI5MDzp6DEO6RCpNlmQT7MxcZUQWUPPGIVciH4sGmQEcIuV9l9u0ejjVnYcjm+htwB9TY/jIG6Sx0Ix5voT7mGBTZOlMgCWK1agXX/Aqtgv7WYxOo3Vif89TG47m875NJ8PZgdm1teHUf1QWzXp76lAz+ed2wWCppR+5hodLFSo4s2KEFPfTcKWBRZp5ItkabQuHutvWz9doqxmDPczrdWTihDSwB2WcoJEiq9houwrTkDKUodMF2pu"
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
        url = "https://z.clash.ink/chfs/shared/MinecraftFRP/Data/frp-server-list.json"
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