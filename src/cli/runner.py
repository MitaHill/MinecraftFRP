import sys
import random
from PySide6.QtCore import QEventLoop

from src.core.config_manager import ConfigManager
from src.core.frpc_thread import FrpcThread
from src.network.minecraft_lan import poll_minecraft_lan_once
from src.utils.port_generator import gen_port

def run_cli(servers, args):
    """处理命令行启动逻辑"""
    server_name = args.server if args.server else list(servers.keys())[0]
    if server_name not in servers:
        print(f"错误: 无效的服务器名称 '{server_name}'。可用服务器: {', '.join(servers.keys())}")
        sys.exit(1)

    local_port = determine_local_port(args)
    if not local_port:
        print("错误: 必须提供 --local_port 或 --auto-find 并成功检测到端口")
        sys.exit(1)

    start_mapping_cli(server_name, local_port, servers)

def determine_local_port(args):
    """根据参数确定本地端口"""
    if args.auto_find:
        port = poll_minecraft_lan_once()
        if port:
            print(f"检测到Minecraft游戏端口: {port}")
            return port
        else:
            print("未检测到Minecraft游戏端口")
            if not args.local_port:
                return None
    
    if args.local_port:
        if not args.local_port.isdigit() or not 1 <= int(args.local_port) <= 65535:
            print("错误: 请输入有效端口 (1-65535)")
            sys.exit(1)
        return args.local_port
    
    return None

def start_mapping_cli(server_name, local_port, servers):
    """启动 frpc 映射进程 (CLI模式)"""
    config_manager = ConfigManager()
    host, port, token = servers[server_name]
    remote_port = gen_port()
    user_id = random.randint(10000, 99999)

    if not config_manager.create_config(host, port, token, local_port, remote_port, user_id):
        print("错误: 无法写入配置文件，请检查权限")
        sys.exit(1)

    link = f"{host}:{remote_port}"
    print(f"开始映射本地端口 {local_port} 到 {link}")

    th = FrpcThread("config/frpc.ini")
    th.out.connect(lambda msg: print(msg))
    th.warn.connect(lambda msg: print(f"警告: {msg}"))
    th.success.connect(lambda: print(f"映射成功！映射地址: {link}"))
    th.error.connect(lambda msg: (print(f"错误: {msg}"), sys.exit(1)))
    th.terminated.connect(lambda: (print("frpc进程已终止"), sys.exit(0)))
    th.start()

    # 保持事件循环以使信号生效
    loop = QEventLoop()
    th.terminated.connect(loop.quit)
    loop.exec()
