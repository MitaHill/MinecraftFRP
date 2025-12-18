import os
import tempfile
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    _temp_dir = None
    _created_files = set()

    @staticmethod
    def get_temp_dir() -> Path:
        """获取或创建用于存放临时配置文件的目录"""
        if ConfigManager._temp_dir is None:
            # 使用 appdirs 或一个更标准的位置可能更好，但目前保持简单
            base_temp = Path(tempfile.gettempdir())
            app_temp_dir = base_temp / "MitaHillFRP"
            app_temp_dir.mkdir(parents=True, exist_ok=True)
            ConfigManager._temp_dir = app_temp_dir
        return ConfigManager._temp_dir

    @staticmethod
    def create_temp_config(content: str, user_id: str, suffix: str = ".ini") -> str:
        """
        在临时目录中创建一个唯一的配置文件。
        返回配置文件的绝对路径 (字符串形式)。
        """
        temp_dir = ConfigManager.get_temp_dir()
        # 使用 os.getpid() 和用户ID确保唯一性
        unique_name = f"frpc_{os.getpid()}_{user_id}{suffix}"
        
        # 使用 Path 对象来处理路径，确保跨平台和 Unicode 安全性
        config_path = temp_dir / unique_name
        
        try:
            # 使用 utf-8-sig 写入，可以帮助某些程序（尤其是Windows上的）正确识别UTF-8编码
            config_path.write_text(content, encoding='utf-8-sig')
            
            # 记录创建的文件以供清理
            ConfigManager._created_files.add(config_path)
            
            logger.info(f"创建临时配置文件: {config_path}")
            
            # 返回字符串路径，因为 subprocess 等接口可能需要
            return str(config_path)
            
        except (IOError, OSError) as e:
            logger.error(f"无法创建临时配置文件 {config_path}: {e}", exc_info=True)
            raise

    @staticmethod
    def cleanup_temp_dir():
        """删除所有由此会话创建的临时文件"""
        if not ConfigManager._created_files:
            return
            
        logger.info(f"正在清理 {len(ConfigManager._created_files)} 个临时配置文件...")
        for file_path in list(ConfigManager._created_files):
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.debug(f"已删除: {file_path}")
                ConfigManager._created_files.remove(file_path)
            except (IOError, OSError) as e:
                logger.warning(f"删除临时文件 {file_path} 失败: {e}")

# 示例用法 (非直接运行)
if __name__ == '__main__':
    try:
        # 模拟创建
        config_content = "[common]\nserver_addr = 127.0.0.1"
        path1 = ConfigManager.create_temp_config(config_content, "user123")
        path2 = ConfigManager.create_temp_config(config_content, "user456", ".toml")
        
        print(f"创建的文件: {path1}, {path2}")
        
    finally:
        # 模拟程序退出时清理
        ConfigManager.cleanup_temp_dir()
        print("清理完成。")
