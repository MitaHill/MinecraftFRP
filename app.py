import sys
import signal
import logging
import atexit
import os
import traceback
from pathlib import Path

# 设置日志和崩溃报告路径 (用户文档目录)
DOCS_DIR = Path.home() / "Documents" / "MitaHillFRP"
LOGS_DIR = DOCS_DIR / "logs"
CRASH_LOG = LOGS_DIR / "crash_log.txt"

try:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
except:
    pass

# 配置基础日志，确保在模块加载前就能记录
logging.basicConfig(
    filename=LOGS_DIR / "app_startup.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

def sigint_handler(sig_num, frame):
    """Handles the interrupt signal."""
    # 延迟导入
    from src.gui.MainWindow import PortMappingApp
    if PortMappingApp.inst:
        PortMappingApp.inst.close()
    sys.exit(0)

def cleanup():
    """Application exit cleanup."""
    try:
        from src.core.ConfigManager import ConfigManager
        ConfigManager.cleanup_temp_dir()
    except Exception:
        pass

def main():
    """Main application entry point."""
    atexit.register(cleanup)
    
    # 设置全局异常钩子
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        try:
            logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        except:
            pass
        # 写入崩溃日志
        try:
            with open(CRASH_LOG, "w", encoding="utf-8") as f:
                f.write("Application Crash Report\n")
                f.write("=========================\n")
                traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
        except:
            pass
        
        # 尝试弹窗提示 (如果 PySide6 已加载)
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, f"程序发生严重错误已崩溃。\n请查看日志: {CRASH_LOG}", "MinecraftFRP Crash", 16)
        except:
            pass

    sys.excepthook = handle_exception
    signal.signal(signal.SIGINT, sigint_handler)

    try:
        # 输出版本信息
        # 延迟导入
        from src.version import VERSION, GIT_HASH, get_version_string
        version_str = get_version_string()
        logger.info(f"Application started: {version_str}")
        logger.info(f"Version: {VERSION}, Git Hash: {GIT_HASH}")
        
        # 如果是编译版本，提取updater到运行目录
        from src.utils.UpdaterManager import UpdaterManager
        try:
            UpdaterManager.extract_updater()
            UpdaterManager.cleanup_old_updater()
        except Exception as e:
            logger.warning(f"Updater提取失败（不影响正常使用）: {e}")

        # 延迟导入 PySide6，防止 DLL 加载失败导致静默退出
        from PySide6.QtWidgets import QApplication, QMessageBox
        from PySide6.QtCore import QLockFile, QDir
        from src.gui.MainWindow import PortMappingApp

        app = QApplication(sys.argv)
        
        # --- 启动来源验证 ---
        if "--launched-by-launcher" not in sys.argv:
            QMessageBox.critical(None, "启动错误", 
                                 "请使用启动器 (Launcher.exe) 启动本程序！\n\n"
                                 "Please run Launcher.exe to start the application.")
            sys.exit(1)
        
        # --- 单实例互斥锁 ---
        lock_file = QLockFile(QDir.tempPath() + "/MinecraftFRP.lock")
        lock_file.setStaleLockTime(0) # 如果之前崩溃，立即接管
        if not lock_file.tryLock(100):
            QMessageBox.critical(None, "提示", "程序已经在运行中！\n请不要重复启动。")
            sys.exit(1)
        # 将锁挂载到 app 上防止被垃圾回收
        app._lock_file = lock_file

        main_window = PortMappingApp({})
        main_window.show()
        sys.exit(app.exec())
        
    except ImportError as e:
        # 捕获导入错误 (如 PySide6 DLL 缺失)
        error_msg = f"Failed to import dependencies: {e}\nProbable cause: Missing VC++ Redistributable or corrupted installation."
        logger.critical(error_msg)
        with open(CRASH_LOG, "w", encoding="utf-8") as f:
            f.write(error_msg)
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, error_msg, "Startup Error", 16)
        except:
            pass
        sys.exit(1)
        
    except Exception as e:
        logger.critical(f"Fatal error in main loop: {e}", exc_info=True)
        handle_exception(type(e), e, e.__traceback__)
        sys.exit(1)

if __name__ == "__main__":
    main()
