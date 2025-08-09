"""
Minecraft FRP 端口映射工具
主程序入口文件
"""
import sys
import signal
import argparse
from PySide6.QtWidgets import QApplication

from src.gui.window import PortMappingApp
from src.utils.constants import DEFAULT_SERVERS


def sigint_handler(sig_num, frame):
    """信号处理器"""
    if PortMappingApp.inst:
        PortMappingApp.inst.forceClose()
    sys.exit(0)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="Minecraft 端口映射工具")
    parser.add_argument('--local_port', type=str, help="本地端口号 (1-65535)")
    parser.add_argument('--auto-find', action='store_true', help="优先自动寻找Minecraft LAN端口")
    parser.add_argument('--server', type=str, choices=DEFAULT_SERVERS.keys(), help="服务器名称")
    return parser.parse_args()


def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, sigint_handler)
    
    # 解析命令行参数
    args = parse_args()
    
    # 创建Qt应用
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = PortMappingApp(args)
    
    # 如果不是CLI模式，显示窗口
    if not (args.local_port or args.auto_find or args.server):
        window.show()
    
    # 启动应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()