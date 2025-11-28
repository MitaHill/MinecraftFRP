import sys
import signal
import argparse
from PySide6.QtWidgets import QApplication

from src.core.server_manager import ServerManager
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
    
    # 初始化服务器管理器
    server_manager = ServerManager()
    servers = server_manager.get_servers()
    
    # 解析命令行参数
    args = parse_args(servers.keys())
    
    # 如果有命令行参数，则执行CLI逻辑
    if args.local_port or args.auto_find or args.server:
        # QApplication对于线程信号处理是必需的
        app = QApplication(sys.argv)
        run_cli(servers, args)
        sys.exit(0)
    
    # 否则，启动GUI
    app = QApplication(sys.argv)
    main_window = PortMappingApp(servers)
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
