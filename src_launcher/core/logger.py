"""
日志管理模块
"""
import logging
from pathlib import Path


def setup_logger():
    """设置日志系统"""
    log_dir = Path.home() / "Documents" / "MitaHillFRP" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "launcher.log"
    
    # 配置日志
    logger = logging.getLogger("Launcher")
    logger.setLevel(logging.INFO)
    
    # 文件处理器
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.INFO)
    
    # 控制台处理器
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # 格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger
