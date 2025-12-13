import sys
import os
import traceback
import ctypes

# --- Bootstrapper: Catch early crashes (Missing DLLs, ImportErrors) ---
# This block ensures that even if the app crashes before logging is set up,
# the user gets a visual error message.

# Redirect stderr to a temp file immediately
temp_dir = os.environ.get("TEMP", os.environ.get("TMP", "."))
boot_log_path = os.path.join(temp_dir, "MinecraftFRP_boot_error.log")

try:
    # Explicitly flush stderr to file
    sys.stderr = open(boot_log_path, "w", encoding="utf-8", buffering=1)
except:
    pass # If we can't write to temp, we proceed (MsgBox is backup)

try:
    # --- Original Imports and Code ---
    import signal
    import logging
    import atexit
    from pathlib import Path

    # 全局变量，由 setup_logging 初始化
    logger = None
    CRASH_LOG = None

    def setup_logging():
        """
        配置日志记录，并提供备用方案。
        尝试在 Documents/MitaHillFRP/logs 记录，如果失败，则回退到本地 'logs' 文件夹。
        """
        log_dir_primary = Path.home() / "Documents" / "MitaHillFRP" / "logs"
        log_dir_fallback = Path.cwd() / "logs"
        log_dir = None

        # 尝试主要日志目录
        try:
            log_dir_primary.mkdir(parents=True, exist_ok=True)
            log_dir = log_dir_primary
        except Exception as e1:
            # 如果主要目录失败，尝试备用目录
            try:
                log_dir_fallback.mkdir(parents=True, exist_ok=True)
                log_dir = log_dir_fallback
            except Exception as e2:
                # 如果两个都失败，日志记录将被禁用
                sys.stderr.write(f"FATAL: Could not create log directory.\n")
                sys.stderr.write(f"Primary error: {e1}\n")
                sys.stderr.write(f"Fallback error: {e2}\n")
                return None, None

        startup_log_file = log_dir / "app_startup.log"
        crash_log_file = log_dir / "crash_log.txt"

        try:
            logging.basicConfig(
                filename=startup_log_file,
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                encoding='utf-8',
                force=True  # 如果已配置，则重新配置
            )
            _logger = logging.getLogger()
            _logger.info("--- Application Starting ---")
            _logger.info(f"Logging initialized successfully. Log directory: {log_dir}")
            return _logger, crash_log_file
        except Exception as e:
            sys.stderr.write(f"FATAL: Failed to configure basicConfig: {e}\n")
            return None, None

    def sigint_handler(sig_num, frame):
        """处理中断信号。"""
        if logger:
            logger.info("SIGINT received, shutting down.")
        from src.gui.MainWindow import PortMappingApp
        if PortMappingApp.inst:
            PortMappingApp.inst.close()
        sys.exit(0)

    def cleanup():
        """应用程序退出清理。"""
        if logger:
            logger.info("Application cleanup started.")
        try:
            from src.core.ConfigManager import ConfigManager
            ConfigManager.cleanup_temp_dir()
        except Exception as e:
            if logger:
                logger.error(f"Error during cleanup: {e}")

    def main():
        """主应用程序入口点。"""
        global logger, CRASH_LOG
        logger, CRASH_LOG = setup_logging()

        if not logger:
            try:
                ctypes.windll.user32.MessageBoxW(0, "无法初始化日志系统，程序无法启动。\n请检查权限或联系开发者。", "MinecraftFRP 致命错误", 16)
            except:
                pass
            sys.exit(1)

        atexit.register(cleanup)
        
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
            
            if CRASH_LOG:
                try:
                    with open(CRASH_LOG, "w", encoding="utf-8") as f:
                        f.write("Application Crash Report\n")
                        f.write("=========================\n")
                        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
                except Exception as e:
                    logger.error(f"Failed to write crash log: {e}")
            
            try:
                ctypes.windll.user32.MessageBoxW(0, f"程序发生严重错误已崩溃。\n请查看日志: {CRASH_LOG}", "MinecraftFRP Crash", 16)
            except:
                pass

        sys.excepthook = handle_exception
        signal.signal(signal.SIGINT, sigint_handler)

        try:
            logger.info("Importing version info...")
            from src.version import VERSION, GIT_HASH, get_version_string
            version_str = get_version_string()
            logger.info(f"Application started: {version_str}")
            logger.info(f"Version: {VERSION}, Git Hash: {GIT_HASH}")
            
            # --- Environment Check ---
            logger.info("Checking critical dependencies...")
            try:
                import yaml
                logger.info(f"PyYAML detected: {yaml.__version__}")
            except ImportError:
                logger.critical("PyYAML not found!")
                raise

            try:
                import Crypto
                from Crypto.Cipher import AES
                logger.info(f"PyCryptodome detected (Crypto package found).")
            except ImportError:
                logger.critical("PyCryptodome not found! Please install requirements.txt.")
                raise
            # -------------------------
            
            logger.info("Initializing UpdaterManager...")
            from src.utils.UpdaterManager import UpdaterManager
            try:
                UpdaterManager.extract_updater()
                UpdaterManager.cleanup_old_updater()
                logger.info("UpdaterManager tasks completed.")
            except Exception as e:
                logger.warning(f"Updater extraction failed (non-critical): {e}")

            logger.info("Importing PySide6...")
            from PySide6.QtWidgets import QApplication, QMessageBox
            from PySide6.QtCore import QLockFile, QDir
            logger.info("PySide6 imported successfully.")

            logger.info("Creating QApplication...")
            app = QApplication(sys.argv)
            logger.info("QApplication created.")
            
            logger.info("Checking launch source...")
            if "--launched-by-launcher" not in sys.argv:
                logger.warning("Application not launched by launcher.")
                QMessageBox.critical(None, "启动错误", 
                                     "请使用启动器 (Launcher.exe) 启动本程序！\n\n"
                                     "Please run Launcher.exe to start the application.")
                sys.exit(1)
            
            logger.info("Checking for single instance...")
            lock_file = QLockFile(QDir.tempPath() + "/MinecraftFRP.lock")
            lock_file.setStaleLockTime(0)
            if not lock_file.tryLock(100):
                logger.warning("Another instance is already running.")
                QMessageBox.critical(None, "提示", "程序已经在运行中！\n请不要重复启动。")
                sys.exit(1)
            app._lock_file = lock_file
            logger.info("Single instance lock acquired.")

            logger.info("Importing and creating MainWindow...")
            from src.gui.MainWindow import PortMappingApp
            main_window = PortMappingApp({})
            logger.info("MainWindow created.")
            
            main_window.show()
            logger.info("MainWindow shown. Starting event loop...")
            sys.exit(app.exec())
            
        except ImportError as e:
            error_msg = f"Failed to import dependencies: {e}\nProbable cause: Missing VC++ Redistributable or corrupted installation."
            logger.critical(error_msg, exc_info=True)
            if CRASH_LOG:
                with open(CRASH_LOG, "w", encoding="utf-8") as f:
                    f.write(error_msg)
            try:
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

except Exception:
    # --- Ultra-Safe Crash Handler ---
    # Catch any error that happens during imports or early setup (e.g. missing DLLs)
    
    # Write full traceback to stderr (redirected to file)
    traceback.print_exc()
    sys.stderr.flush()
    sys.stderr.close()
    
    # Read the log content to show in message box
    err_msg = "Unknown startup error."
    try:
        if os.path.exists(boot_log_path):
            with open(boot_log_path, "r", encoding="utf-8") as f:
                err_msg = f.read()
    except:
        pass
        
    err_msg = f"Application failed to start.\n\nError Details:\n{err_msg}\n\nLog saved to: {boot_log_path}"
    
    try:
        ctypes.windll.user32.MessageBoxW(0, err_msg, "MinecraftFRP Fatal Startup Error", 16)
    except:
        pass
    
    sys.exit(1)

