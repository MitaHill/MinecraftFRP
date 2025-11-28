import json
from src.network.ping_utils import download_json, read_json_file
from src.utils.crypto import decrypt_data, load_servers_from_json

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
        
        self.servers = self._load_default_servers()
        self.load_servers()
    
    def _load_default_servers(self):
        """加载并解密内置的默认服务器列表"""
        try:
            decrypted = decrypt_data(DEFAULT_SERVERS_ENCRYPTED, self.key)
            if decrypted:
                json_data = json.loads(decrypted)
                return load_servers_from_json(json_data)
        except Exception as e:
            print(f"无法加载内置服务器列表: {e}")
        return {}

    def load_servers(self):
        url = "https://clash.ink/file/frp-server-list.json"
        local_path = "frp-server-list.json"

        # 尝试下载JSON文件
        if download_json(url, f"config/{local_path}"):
            print("成功下载JSON文件")
        else:
            print("下载JSON文件失败，尝试使用本地文件")

        # 读取JSON文件
        encrypted_data = read_json_file(f"config/{local_path}")
        if encrypted_data:
            # 解密
            decrypted_data = decrypt_data(encrypted_data, self.key)
            if decrypted_data:
                # 解析JSON
                json_data = json.loads(decrypted_data)
                servers = load_servers_from_json(json_data)
                if servers:
                    self.servers = servers
                    print("成功加载服务器列表")
                    return

        print("使用内置默认服务器列表")
        # 如果self.servers已经在__init__中初始化为默认值，则保持不变
        # 再次确认默认值是否有效
        if not self.servers:
             # 如果解密失败且无远程配置，则是一个严重错误，但为了防止crash，我们返回空字典
             print("警告: 无法加载任何服务器配置")

    def get_servers(self):
        return self.servers