import random
from threading import Lock
from src.core.YamlConfig import YamlConfigManager, DEFAULT_APP_CONFIG

# 配置管理器（用户文档路径）
import os
config_manager = YamlConfigManager(config_dir=os.path.join(os.path.expanduser('~'), 'Documents', 'MitaHillFRP', 'Config'))
app_config = config_manager.load_config("app_config.yaml", DEFAULT_APP_CONFIG)

# 避免使用的端口列表，防御性编程处理 None
RESERVED_PORTS = set((app_config or {}).get("network", {}).get("reserved_ports", [80, 443, 3306, 8080, 25565]))

# 生成随机端口
def gen_port():
    port_mutex = Lock()
    with port_mutex:
        while (p := random.randint(10000, 65534)) in RESERVED_PORTS:
            pass
        return p