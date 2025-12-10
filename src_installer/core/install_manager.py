"""
安装管理器
处理安装、升级、卸载逻辑
"""
import os
import shutil
import zipfile
import logging
from pathlib import Path
from typing import Optional, Tuple

# 兼容打包和开发环境的导入
try:
    from core.config_manager import ConfigManager
    from core.file_operations import FileOperations
except ImportError:
    from src_installer.core.config_manager import ConfigManager
    from src_installer.core.file_operations import FileOperations

logger = logging.getLogger(__name__)

class InstallManager:
    def __init__(self):
        self.config_mgr = ConfigManager()
        self.file_ops = FileOperations()
        self.previous_install = self.config_mgr.get_install_info()
        
    def get_default_install_path(self) -> str:
        """获取默认安装路径"""
        username = os.environ.get('USERNAME', 'User')
        return f"C:\\Users\\{username}\\AppData\\Local\\MinecraftFRP"
    
    def is_upgrade(self) -> bool:
        """是否为升级安装"""
        return self.previous_install is not None
    
    def get_previous_path(self) -> Optional[str]:
        """获取之前的安装路径"""
        if self.previous_install:
            return self.previous_install.get('install_path')
        return None
    
    def validate_install_path(self, path: str) -> Tuple[bool, str]:
        """验证安装路径"""
        if not path or path.strip() == "":
            return False, "安装路径不能为空"
        
        path_obj = Path(path)
        
        # 检查路径是否合法
        try:
            path_obj.resolve()
        except Exception as e:
            return False, f"路径格式错误: {e}"
        
        # 检查父目录是否存在或可创建
        parent = path_obj.parent
        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"无法创建目录: {e}"
        
        # 检查写入权限
        if not os.access(str(parent), os.W_OK):
            return False, "没有写入权限"
        
        return True, ""
    
    def install(self, install_path: str, zip_path: str, progress_callback=None) -> Tuple[bool, str]:
        """
        执行安装
        :param install_path: 安装路径
        :param zip_path: 压缩包路径
        :param progress_callback: 进度回调 callback(current, total, message)
        :return: (成功, 错误消息)
        """
        try:
            install_dir = Path(install_path)
            
            # 创建安装目录
            if progress_callback:
                progress_callback(10, 100, "创建安装目录...")
            install_dir.mkdir(parents=True, exist_ok=True)
            
            # 如果是升级，备份配置文件
            backup_files = []
            if self.is_upgrade() and install_dir.exists():
                if progress_callback:
                    progress_callback(20, 100, "备份配置文件...")
                backup_files = self.file_ops.backup_config_files(str(install_dir))
            
            # 解压文件
            if progress_callback:
                progress_callback(30, 100, "解压安装文件...")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                total_files = len(zip_ref.namelist())
                for i, file in enumerate(zip_ref.namelist()):
                    zip_ref.extract(file, str(install_dir))
                    if progress_callback and i % 5 == 0:
                        progress = 30 + int((i / total_files) * 40)
                        progress_callback(progress, 100, f"解压文件 {i+1}/{total_files}")
            
            # 恢复配置文件
            if backup_files:
                if progress_callback:
                    progress_callback(75, 100, "恢复配置文件...")
                self.file_ops.restore_config_files(str(install_dir), backup_files)
            
            # 创建快捷方式
            if progress_callback:
                progress_callback(80, 100, "创建快捷方式...")
            self.file_ops.create_shortcuts(str(install_dir))
            
            # 创建卸载程序
            if progress_callback:
                progress_callback(90, 100, "创建卸载程序...")
            self.file_ops.create_uninstaller(str(install_dir))
            
            # 保存安装信息
            if progress_callback:
                progress_callback(95, 100, "保存安装信息...")
            self.config_mgr.save_install_info(install_path)
            
            if progress_callback:
                progress_callback(100, 100, "安装完成!")
            
            logger.info(f"Installation completed successfully to {install_path}")
            return True, ""
            
        except Exception as e:
            error_msg = f"安装失败: {e}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def uninstall(self, install_path: str, remove_config: bool = False) -> Tuple[bool, str]:
        """
        执行卸载
        :param install_path: 安装路径
        :param remove_config: 是否删除配置文件
        :return: (成功, 错误消息)
        """
        try:
            install_dir = Path(install_path)
            
            if not install_dir.exists():
                return False, "安装目录不存在"
            
            # 删除快捷方式
            self.file_ops.remove_shortcuts()
            
            # 删除安装目录
            shutil.rmtree(str(install_dir), ignore_errors=True)
            
            # 删除配置信息
            if remove_config:
                self.config_mgr.remove_install_info()
                config_dir = self.config_mgr.get_config_dir()
                if config_dir.exists():
                    shutil.rmtree(str(config_dir), ignore_errors=True)
            
            logger.info(f"Uninstallation completed for {install_path}")
            return True, ""
            
        except Exception as e:
            error_msg = f"卸载失败: {e}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
