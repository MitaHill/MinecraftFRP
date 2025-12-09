import sys
import signal
import argparse
import logging
from PySide6.QtWidgets import QApplication

from src.core.ServerManager import ServerManager
from src.gui.MainWindow import PortMappingApp
from src.cli.runner import run_cli
from src.utils.UpdaterManager import UpdaterManager

logger = logging.getLogger(__name__)

def sigint_handler(sig_num, frame):
    """Handles the interrupt signal."""
    if PortMappingApp.inst:
        PortMappingApp.inst.close()
    sys.exit(0)

def parse_args(server_choices):
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Minecraft Port Mapping Tool")
    parser.add_argument('--local_port', type=str, help="Local port number (1-65535)")
    parser.add_argument('--auto-find', action='store_true', help="Prioritize auto-finding Minecraft LAN port")
    parser.add_argument('--server', type=str, choices=server_choices, help="Server name")
    return parser.parse_args()

def main():
    """Main application entry point."""
    signal.signal(signal.SIGINT, sigint_handler)
    
    # 如果是编译版本，提取updater到运行目录
    try:
        UpdaterManager.extract_updater()
        UpdaterManager.cleanup_old_updater()
    except Exception as e:
        # 提取失败不影响主程序运行
        logger.warning(f"Updater提取失败（不影响正常使用）: {e}")

    if len(sys.argv) > 1 and any(arg.startswith('--') for arg in sys.argv[1:]):
        server_manager = ServerManager()
        servers = server_manager.get_servers()
        args = parse_args(servers.keys())
        app = QApplication(sys.argv)
        run_cli(servers, args)
        sys.exit(0)

    app = QApplication(sys.argv)
    main_window = PortMappingApp({})
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
