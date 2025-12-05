import sys
import signal
import argparse
from PySide6.QtWidgets import QApplication

from src.core.ServerManager import ServerManager
from src.gui.MainWindow import PortMappingApp
from src.cli.runner import run_cli

def sigint_handler(sig_num, frame):
    """处理中断信号"""
    if PortMappingApp.inst:
        PortMappingApp.inst.close()
    sys.exit(0)

def parse_args(server_choices):
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="Minecraft 端口映射工具")
    parser.add_argument('--local_port', type=str, help="本地端口号 (1-65535)")
    parser.add_argument('--auto-find', action='store_true', help="优先自动寻找Minecraft LAN端口")
    parser.add_argument('--server', type=str, choices=server_choices, help="服务器名称")
    return parser.parse_args()

def main():
    """主程序入口"""
    # 设置信号处理器
    signal.signal(signal.SIGINT, sigint_handler)

    # 优先处理CLI调用 (简化版，仅用于演示)
    # 完整的CLI逻辑需要后续重构以支持异步加载
    if len(sys.argv) > 1 and any(arg.startswith('--') for arg in sys.argv[1:]):
        server_manager = ServerManager()
        servers = server_manager.get_servers()
        args = parse_args(servers.keys())
        app = QApplication(sys.argv)
        run_cli(servers, args)
        sys.exit(0)

    # GUI 启动路径 - 传入空字典以实现快速启动
    app = QApplication(sys.argv)
    main_window = PortMappingApp({})  # Pass empty dict for instant startup
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
