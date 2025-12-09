"""
UpdaterManager - 管理updater程序的释放和调用
"""
import os
import sys
import shutil
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class UpdaterManager:
    """管理updater程序的提取和部署"""
    
    @staticmethod
    def is_compiled() -> bool:
        """检测程序是否是编译后的可执行文件"""
        # Nuitka编译后 __file__ 会指向实际位置，但sys.argv[0]会是.exe
        # PyInstaller会设置sys._MEIPASS
        return (
            getattr(sys, 'frozen', False) or  # PyInstaller
            hasattr(sys, '_MEIPASS') or       # PyInstaller
            sys.argv[0].endswith('.exe')      # Nuitka
        )
    
    @staticmethod
    def get_updater_embedded_path() -> str:
        """获取内嵌updater.exe的路径"""
        from src.utils.PathUtils import get_resource_path
        return get_resource_path("updater.exe")
    
    @staticmethod
    def get_runtime_updater_path() -> str:
        """获取运行时updater.exe应该存放的路径（主程序同目录）"""
        if UpdaterManager.is_compiled():
            # 编译后，使用可执行文件所在目录
            exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        else:
            # 开发环境，使用项目根目录
            exe_dir = os.path.dirname(os.path.abspath(__file__))
            exe_dir = os.path.join(exe_dir, "..", "..")
            exe_dir = os.path.abspath(exe_dir)
        
        return os.path.join(exe_dir, "updater.exe")
    
    @staticmethod
    def extract_updater() -> Optional[str]:
        """
        将updater从程序内部提取到运行目录
        返回：提取后的updater路径，失败返回None
        """
        if not UpdaterManager.is_compiled():
            logger.info("开发环境，跳过updater提取")
            return None
        
        try:
            embedded_path = UpdaterManager.get_updater_embedded_path()
            runtime_path = UpdaterManager.get_runtime_updater_path()
            
            # 检查内嵌updater是否存在
            if not os.path.exists(embedded_path):
                logger.error(f"内嵌updater不存在: {embedded_path}")
                return None
            
            # 如果运行时updater已存在且是最新的，跳过
            if os.path.exists(runtime_path):
                embedded_size = os.path.getsize(embedded_path)
                runtime_size = os.path.getsize(runtime_path)
                if embedded_size == runtime_size:
                    logger.info("Updater已是最新版本，跳过提取")
                    return runtime_path
            
            # 复制updater到运行目录
            logger.info(f"提取updater: {embedded_path} -> {runtime_path}")
            shutil.copy2(embedded_path, runtime_path)
            
            # 设置可执行权限（Unix系统需要）
            try:
                os.chmod(runtime_path, 0o755)
            except:
                pass
            
            logger.info("Updater提取成功")
            return runtime_path
            
        except Exception as e:
            logger.error(f"提取updater失败: {e}", exc_info=True)
            return None
    
    @staticmethod
    def cleanup_old_updater():
        """清理旧的临时updater（如果存在）"""
        import tempfile
        old_updater = os.path.join(tempfile.gettempdir(), "mcfrp_updater.exe")
        if os.path.exists(old_updater):
            try:
                os.remove(old_updater)
                logger.info("已清理旧的临时updater")
            except Exception as e:
                logger.warning(f"清理旧updater失败: {e}")
