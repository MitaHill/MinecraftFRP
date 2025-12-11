import sys
import signal
import argparse
import logging
import atexit
from PySide6.QtWidgets import QApplication

from src.core.ServerManager import ServerManager
from src.core.ConfigManager import ConfigManager
from src.gui.MainWindow import PortMappingApp
from src.cli.runner import run_cli
from src.utils.UpdaterManager import UpdaterManager
from src.version import VERSION, GIT_HASH, get_version_string

logger = logging.getLogger(__name__)

def sigint_handler(sig_num, frame):
    """Handles the interrupt signal."""
    if PortMappingApp.inst:
        PortMappingApp.inst.close()
    sys.exit(0)

def cleanup():
    """Application exit cleanup."""
    try:
        ConfigManager.cleanup_temp_dir()
    except Exception:
        pass

def parse_args(server_choices):
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Minecraft Port Mapping Tool")
    parser.add_argument('--local_port', type=str, help="Local port number (1-65535)")
    parser.add_argument('--auto-find', action='store_true', help="Prioritize auto-finding Minecraft LAN port")
    parser.add_argument('--server', type=str, choices=server_choices, help="Server name")
    return parser.parse_args()

def main():
    """Main application entry point."""
    atexit.register(cleanup)
    try:
        # 设置全局异常钩子
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
            # 同时写入crash_log.txt以防日志模块未初始化
            try:
                with open("crash_log.txt", "w", encoding="utf-8") as f:
                    import traceback
                    traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
            except:
                pass

        sys.excepthook = handle_exception

        signal.signal(signal.SIGINT, sigint_handler)
        
        # 输出版本信息
        version_str = get_version_string()
        print(f"\n{'='*60}")
        print(f"  {version_str}")
        print(f"{'='*60}\n")
        logger.info(f"Application started: {version_str}")
        logger.info(f"Version: {VERSION}, Git Hash: {GIT_HASH}")
        
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
    except Exception as e:
        logger.critical(f"Fatal error in main loop: {e}", exc_info=True)
        try:
            with open("crash_log.txt", "w", encoding="utf-8") as f:
                import traceback
                f.write(f"Fatal error: {e}\n")
                traceback.print_exc(file=f)
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
