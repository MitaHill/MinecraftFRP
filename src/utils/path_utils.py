import sys
import os

def get_resource_path(relative_path):
    """
    获取资源的绝对路径。
    支持开发环境（当前目录）和 PyInstaller 打包环境（sys._MEIPASS）。
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的临时目录
        base_path = sys._MEIPASS
    else:
        # 开发环境当前目录
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)
