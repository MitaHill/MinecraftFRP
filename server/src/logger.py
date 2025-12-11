import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger():
    """
    配置服务端全局日志
    - 输出到 logs/server.log
    - 大小限制 1MB
    - 保留 1 个备份
    - 同时输出到控制台
    """
    # 确保日志目录存在
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_file = os.path.join(log_dir, "server.log")
    
    # 创建 Logger
    logger = logging.getLogger("MinecraftFRP_Server")
    logger.setLevel(logging.INFO)
    
    # 防止重复添加 Handler
    if logger.handlers:
        return logger
        
    # 格式化
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 1. 文件处理器 (Rolling 1MB)
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=1*1024*1024, # 1MB
        backupCount=1, 
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 2. 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# 全局单例
logger = setup_logger()
