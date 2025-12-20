# src/config/SecretConfig.py

class SecretConfig:
    """
    存储应用程序的关键配置和URL。
    此文件将被编译为二进制扩展 (.pyd) 以增强安全性。
    """
    # Server Manager
    SERVER_LIST_URL = "https://z.clash.ink/chfs/shared/MinecraftFRP/Data/frp-server-list.json"
    ENCRYPTION_KEY = "clashman" # 直接组合，或者保持分开，编译后都是字符串常量
    
    # Ad System
    AD_INDEX_URL = "https://z.clash.ink/chfs/shared/MinecraftFRP/Data/ads/ads_index.yaml"
    AD_IMAGE_BASE_URL = "https://z.clash.ink/chfs/shared/MinecraftFRP/Data/ads/photos/"
    
    # API Endpoints
    TUNNEL_VALIDATE_API = "https://mapi.clash.ink/api/tunnel/validate"
    LOBBY_ROOMS_API = "https://mapi.clash.ink/api/lobby/rooms"
    SPECIAL_HEARTBEAT_API = "https://lytapi.asia/api.php"
    
    # Other
    USER_AGENT = "LMFP/1.3.1"
