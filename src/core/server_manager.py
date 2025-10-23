import json
from src.network.ping_utils import download_json, read_json_file
from src.utils.crypto import decrypt_data, load_servers_from_json

# 默认服务器配置
DEFAULT_SERVERS = {
    "宁波": ("c.clash.ink", 7000, "kindmita"),
    "北京1": ("beijing1.clash.ink", 7000, "kindmita"),
    "北京2": ("beijing2.clash.ink", 7000, "kindmita"),
    "香港": ("clash.ink", 7000, "kindmita"),
    "美国": ("us-1.clash.ink", 7000, "kindmita")
}

class ServerManager:
    def __init__(self):
        self.servers = DEFAULT_SERVERS.copy()
        self.load_servers()
    
    def load_servers(self):
        url = "https://clash.ink/file/frp-server-list.json"
        local_path = "frp-server-list.json"
        key = "clashman"

        # 尝试下载JSON文件
        if download_json(url, f"config/{local_path}"):
            print("成功下载JSON文件")
        else:
            print("下载JSON文件失败，尝试使用本地文件")

        # 读取JSON文件
        encrypted_data = read_json_file(f"config/{local_path}")
        if encrypted_data:
            # 解密
            decrypted_data = decrypt_data(encrypted_data, key)
            if decrypted_data:
                # 解析JSON
                json_data = json.loads(decrypted_data)
                servers = load_servers_from_json(json_data)
                if servers:
                    self.servers = servers
                    print("成功加载服务器列表")
                else:
                    print("解析服务器列表失败，使用默认列表")
                    self.servers = DEFAULT_SERVERS
            else:
                print("解密失败，使用默认列表")
                self.servers = DEFAULT_SERVERS
        else:
            print("未找到JSON文件，使用默认列表")
            self.servers = DEFAULT_SERVERS
    
    def get_servers(self):
        return self.servers