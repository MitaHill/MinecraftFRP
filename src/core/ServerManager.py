import json
import os
import threading
from pathlib import Path
from typing import Dict, Tuple, Optional
from src.network.PingUtils import download_json, read_json_file
from src.utils.Crypto import decrypt_data, load_servers_from_json
from src.utils.LogManager import get_logger
from src.config.SecretConfig import SecretConfig
# get_resource_path 仅用于读取内置默认值（如有必要），此处主要使用文档路径

logger = get_logger()

# 加密后的默认服务器列表 (Anti-Cracking) - 包含特殊节点
DEFAULT_SERVERS_ENCRYPTED = (
    "pZRl39qlwvH6E3jTxG7FyQNxIBuUs27pryM6VNV2hjhDlZh8tCtmtBcVglI7UP/5Pj6+h+ks01+sQ4oqiC9HiK3TdxdIE4tPb1bV7OqDhGTE7LR8ZXT3T8Qmg7xsX4Tr5aj36qHZPfjOJ+p2Z70uHs7LUtCrjv86pVmZsQ+rts9wvaKp7K/t2HGVwWTDhQeGQH6MIopged9AqihEgXKyFucfAjU/IHk+6QeJ9mLaj4Xvl1tysPsj2n1owQTJpGoe/mQW9OZX/RyVlZPF8auNWY0F02jAFR89WCM3G3gF5SE4aSZjIly65Y0H/0yNeU+iXL7x4hRx9Lof9gSLLv3ZqcEtiBhUa7sE2rPS2JG3J/M9NJeG5bw2gCaWOxZRQoVkvXnUswa0E1MFwiy7X7EFlZqcBd+E9u/qQwrtHaBOg14f61Y2CIFpNFMyw+TkSj1XvtKAG61rTOOVWG1VRLUj24uocCPe4yMLaYIEYyIzJu9WUviJ9kobs3nZCcc8nZn8iPug7cRfgJvufmCe+wUsmiDLpk9sG2SR80l1PEp0xvvmtIIgY6W2RTJyDNl4T9XpgRn2n/sW2rI5MDzp6DEO6RCpNlmQT7MxcZUQWUPPGIVciH4sGmQEcIuV9l9u0ejjVnYcjm+htwB9TY/jIG6Sx0Ix5voT7mGBTZOlMgCWK1agXX/Aqtgv7WYxOo3Vif89TG47m875NJ8PZgdm1teHUf1QWzXp76lAz+ed2wWCppR+5hodLFSo4s2KEFPfTcKWBRZp5ItkabQuHutvWz9doqxmDPczrdWTihDSwB2WcoJEiq9houwrTkDKUodMF2pu"
)

# 配置目录
DOCS_DIR = Path.home() / "Documents" / "MitaHillFRP"
CONFIG_DIR = DOCS_DIR / "Config"

class ServerManager:
    def __init__(self):
        self.key = SecretConfig.ENCRYPTION_KEY
        self.lock = threading.Lock() # 线程锁
        
        # 确保配置目录存在
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        # 首先加载内置的，然后尝试从本地文件覆盖
        # 初始化时是单线程环境，可以不用锁，但为了保险起见还是加上
        with self.lock:
            self.servers = self._load_default_servers()
            # _load_servers_from_local 和 _merge_special_nodes 可能会修改 self.servers
            # 但我们在 __init__ 内部直接调用，这里锁一次即可
            self._load_servers_from_local_internal()
            self._merge_special_nodes_internal()

    def _merge_special_nodes_internal(self) -> None:
        """内部方法：合并特殊节点（不加锁，供内部调用）"""
        try:
            # 优先从文档目录读取
            path = CONFIG_DIR / "special_nodes.json"
            if not path.exists():
                logger.warning(f"未找到 {path}，跳过特殊节点合并。")
                return
                
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self.servers.update(data)
        except Exception as e:
            logger.error(f"加载特殊节点失败: {e}")

    def _merge_special_nodes(self) -> None:
        """确保特殊节点始终存在于服务器列表中，并位于末尾（展示在底部）。(加锁版)"""
        with self.lock:
            self._merge_special_nodes_internal()

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

    def _load_servers_from_local_internal(self) -> None:
        """内部方法：从本地文件加载服务器列表（不加锁）"""
        local_path = CONFIG_DIR / "frp-server-list.json"
        # read_json_file 支持 Path 对象或字符串
        encrypted_data = read_json_file(str(local_path))
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

    def _load_servers_from_local(self) -> None:
        """从本地文件加载服务器列表，不进行网络下载"""
        with self.lock:
            self._load_servers_from_local_internal()

    def update_servers_from_network(self) -> Optional[Dict[str, Tuple[str, int, str]]]:
        """从网络下载并更新服务器列表，返回新的服务器字典"""
        url = SecretConfig.SERVER_LIST_URL
        local_path = CONFIG_DIR / "frp-server-list.json"

        if not download_json(url, str(local_path)):
            logger.warning("下载新的服务器列表失败。")
            return None

        logger.info("成功下载新的服务器列表文件。")
        encrypted_data = read_json_file(str(local_path))
        if encrypted_data:
            try:
                decrypted_data = decrypt_data(encrypted_data, self.key)
                if decrypted_data:
                    json_data = json.loads(decrypted_data)
                    servers = load_servers_from_json(json_data)
                    if servers:
                        with self.lock:
                            self.servers = servers
                            self._merge_special_nodes_internal()
                        logger.info("成功从网络更新并加载服务器列表。")
                        return self.get_servers() # 返回线程安全的副本
            except Exception as e:
                logger.error(f"解析下载的服务器列表失败: {e}")

        return None

    def get_servers(self) -> Dict[str, Tuple[str, int, str]]:
        with self.lock:
            servers = self.servers.copy()
            # Temporary: Hide nodes A and B as requested
            for node in ['A', 'B']:
                if node in servers:
                    del servers[node]
            return servers