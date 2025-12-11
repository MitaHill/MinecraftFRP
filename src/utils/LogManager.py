import logging
import sys
import os
from src.utils.PathUtils import get_resource_path

class ClosingFileHandler(logging.FileHandler):
    """每次写入后关闭文件的 Handler，以支持外部文件操作(如裁剪)"""
    def emit(self, record):
        try:
            super().emit(record)
        finally:
            self.close()

class LogManager:
    _instance = None
    _logger = None

    @staticmethod
    def get_logger(name: str = "MinecraftFRP") -> logging.Logger:
        """
        获取或配置全局 Logger 单例。
        """
        if LogManager._logger is None:
            LogManager._setup_logger()
        return logging.getLogger(name)

    @staticmethod
    def _setup_logger():
        """
        初始化日志配置：同时输出到控制台和文件。
        """
        logger = logging.getLogger("MinecraftFRP")
        logger.setLevel(logging.INFO)
        
        # 防止重复添加 Handler
        if logger.handlers:
            return

        # 格式化器
        formatter = logging.Formatter(
            fmt='[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 1. 控制台 Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)

        # 2. 文件 Handler (ClosingFileHandler)
        # 日志目录迁移到用户文档
        docs_path = os.path.join(os.path.expanduser('~'), 'Documents', 'MitaHillFRP')
        log_dir = os.path.join(docs_path, 'logs')
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception:
            pass

        log_file_path = os.path.join(log_dir, "app.log")
        
        try:
            # 使用自定义的 ClosingFileHandler
            file_handler = ClosingFileHandler(log_file_path, encoding='utf-8')
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.INFO)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Failed to setup file logging: {e}")

        LogManager._logger = logger

# 便捷入口
def get_logger(name: str = "MinecraftFRP") -> logging.Logger:
    return LogManager.get_logger(name)
