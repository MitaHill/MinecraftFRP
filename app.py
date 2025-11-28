import sys
import signal
import argparse
from PySide6.QtWidgets import QApplication

from src.core.server_manager import ServerManager
from src.gui.MainWindow import PortMappingApp

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
    
    # 创建QApplication实例
    app = QApplication(sys.argv)
    
    # 初始化服务器管理器
    server_manager = ServerManager()
    servers = server_manager.get_servers()
    
    # 解析命令行参数
    args = parse_args(servers.keys())
    
    # 创建主窗口
    main_window = PortMappingApp(servers, args)
    
    # 显示窗口（仅在非命令行模式下）
    if not (args.local_port or args.auto_find or args.server):
        main_window.show()
    
    # 运行应用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    main()