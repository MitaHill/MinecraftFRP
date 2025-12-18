import sys
import os
import shutil
import logging
from src.utils.PathUtils import get_resource_path

logger = logging.getLogger(__name__)

class UpdaterManager:
    @staticmethod
    def get_updater_path() -> str:
        """获取更新程序（updater.exe）的路径"""
        if getattr(sys, 'frozen', False):
            # 编译后的环境
            base_path = os.path.dirname(sys.executable)
            return os.path.join(base_path, "updater.exe")
        else:
            # 开发环境
            return get_resource_path("updater/updater.exe")

    @staticmethod
    def extract_updater():
        """
        如果是编译版本，将内嵌的 updater.exe 提取到与主程序相同的目录。
        """
        if not getattr(sys, 'frozen', False):
            logger.info("在开发模式下，跳过提取更新程序。")
            return

        logger.info("检查更新程序是否存在...")
        updater_src_path = get_resource_path("updater/updater.exe")
        updater_dest_path = UpdaterManager.get_updater_path()

        if not os.path.exists(updater_src_path):
            logger.warning("在资源文件中找不到更新程序，无法提取。")
            return

        # 仅在目标文件不存在或内容不同时提取
        try:
            if os.path.exists(updater_dest_path):
                # 比较文件哈希值以决定是否覆盖
                import hashlib
                
                def get_file_hash(path):
                    sha256 = hashlib.sha256()
                    with open(path, 'rb') as f:
                        while chunk := f.read(8192):
                            sha256.update(chunk)
                    return sha256.hexdigest()

                src_hash = get_file_hash(updater_src_path)
                dest_hash = get_file_hash(updater_dest_path)

                if src_hash == dest_hash:
                    logger.info("更新程序已是最新版本，无需提取。")
                    return
                else:
                    logger.info("检测到更新程序版本不同，准备覆盖。")
            
            logger.info(f"正在提取更新程序到: {updater_dest_path}")
            shutil.copy2(updater_src_path, updater_dest_path)
            logger.info("更新程序提取成功。")

        except (IOError, OSError, shutil.Error) as e:
            logger.error(f"提取更新程序时发生错误: {e}", exc_info=True)
            # 根据需要，可以决定是否抛出异常或让程序继续
            # raise  # 如果这是一个关键失败

    @staticmethod
    def cleanup_old_updater():
        """
        清理旧的更新程序文件（例如 updater.exe.old）。
        """
        updater_path = UpdaterManager.get_updater_path()
        old_updater_path = updater_path + ".old"
        
        if os.path.exists(old_updater_path):
            logger.info(f"找到旧的更新程序文件: {old_updater_path}，正在尝试删除...")
            try:
                os.remove(old_updater_path)
                logger.info("旧的更新程序文件已成功删除。")
            except (IOError, OSError) as e:
                logger.warning(f"删除旧的更新程序文件失败: {e}")
