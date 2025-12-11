"""
文件操作工具
处理文件复制、快捷方式创建等
"""
import os
import shutil
import logging
from pathlib import Path
from typing import List

# win32com是可选的，用于创建快捷方式
try:
    import win32com.client
    HAS_WIN32COM = True
except ImportError:
    HAS_WIN32COM = False
    logging.warning("win32com not available, shortcuts will not be created")

logger = logging.getLogger(__name__)

class FileOperations:
    CONFIG_FILES = ["app_config.yaml", "frpc.toml", "frp-server-list.json"]
    
    def backup_config_files(self, install_dir: str) -> List[tuple]:
        """
        备份配置文件
        :return: [(filename, content), ...]
        """
        backup = []
        install_path = Path(install_dir)
        
        for config_file in self.CONFIG_FILES:
            file_path = install_path / "config" / config_file
            if file_path.exists():
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    backup.append((config_file, content))
                    logger.info(f"Backed up {config_file}")
                except Exception as e:
                    logger.error(f"Failed to backup {config_file}: {e}")
        
        return backup
    
    def restore_config_files(self, install_dir: str, backup_files: List[tuple]):
        """恢复配置文件"""
        install_path = Path(install_dir)
        config_dir = install_path / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        for filename, content in backup_files:
            file_path = config_dir / filename
            try:
                with open(file_path, 'wb') as f:
                    f.write(content)
                logger.info(f"Restored {filename}")
            except Exception as e:
                logger.error(f"Failed to restore {filename}: {e}")
    
    def create_shortcuts(self, install_dir: str):
        """创建快捷方式"""
        if not HAS_WIN32COM:
            logger.warning("win32com not available, skipping shortcut creation")
            return
        
        install_path = Path(install_dir)
        launcher_path = install_path / "launcher.exe"
        
        if not launcher_path.exists():
            logger.warning(f"Launcher not found at {launcher_path}")
            return
        
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            
            # 桌面快捷方式
            desktop = Path(shell.SpecialFolders("Desktop"))
            desktop_shortcut = desktop / "Minecraft联机工具.lnk"
            shortcut = shell.CreateShortCut(str(desktop_shortcut))
            shortcut.TargetPath = str(launcher_path)
            shortcut.WorkingDirectory = str(install_path)
            shortcut.IconLocation = str(launcher_path)
            shortcut.Description = "Minecraft FRP 联机工具"
            shortcut.save()
            logger.info(f"Created desktop shortcut: {desktop_shortcut}")
            
            # 开始菜单快捷方式
            start_menu = Path(shell.SpecialFolders("Programs"))
            start_menu_dir = start_menu / "Minecraft联机工具"
            start_menu_dir.mkdir(parents=True, exist_ok=True)
            start_shortcut = start_menu_dir / "Minecraft联机工具.lnk"
            shortcut = shell.CreateShortCut(str(start_shortcut))
            shortcut.TargetPath = str(launcher_path)
            shortcut.WorkingDirectory = str(install_path)
            shortcut.IconLocation = str(launcher_path)
            shortcut.Description = "Minecraft FRP 联机工具"
            shortcut.save()
            logger.info(f"Created start menu shortcut: {start_shortcut}")
            
        except Exception as e:
            logger.error(f"Failed to create shortcuts: {e}")
    
    def remove_shortcuts(self):
        """删除快捷方式"""
        if not HAS_WIN32COM:
            logger.warning("win32com not available, skipping shortcut removal")
            return
        
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            
            # 删除桌面快捷方式
            desktop = Path(shell.SpecialFolders("Desktop"))
            desktop_shortcut = desktop / "Minecraft联机工具.lnk"
            if desktop_shortcut.exists():
                desktop_shortcut.unlink()
                logger.info("Removed desktop shortcut")
            
            # 删除开始菜单快捷方式
            start_menu = Path(shell.SpecialFolders("Programs"))
            start_menu_dir = start_menu / "Minecraft联机工具"
            if start_menu_dir.exists():
                shutil.rmtree(str(start_menu_dir), ignore_errors=True)
                logger.info("Removed start menu shortcuts")
                
        except Exception as e:
            logger.error(f"Failed to remove shortcuts: {e}")
    
    def create_uninstaller(self, install_dir: str):
        """创建卸载程序"""
        # TODO: 在后续实现卸载程序生成
        pass
