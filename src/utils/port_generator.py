import random
from threading import Lock
from src.core.yaml_config import YamlConfigManager, DEFAULT_APP_CONFIG

# 配置管理器
config_manager = YamlConfigManager()
app_config = config_manager.load_config("app_config.yaml", DEFAULT_APP_CONFIG)

# 避免使用的端口列表
RESERVED_PORTS = set(app_config.get("network", {}).get("reserved_ports", [80, 443, 3306, 8080, 25565]))

# 生成随机端口
def gen_port():
    port_mutex = Lock()
    with port_mutex:
        while (p := random.randint(10000, 65534)) in RESERVED_PORTS:
            pass
        return p