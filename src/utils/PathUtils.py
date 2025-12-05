import sys
import os

def get_resource_path(relative_path: str) -> str:
    """
    获取资源的绝对路径。
    支持开发环境、PyInstaller 打包环境 (sys._MEIPASS) 和 Nuitka 环境。
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的临时目录
        base_path = sys._MEIPASS
    else:
        # 开发环境或 Nuitka
        # 假设 PathUtils.py 位于 src/utils/ 目录下
        # 项目根目录为 ../../
        # 对于 Nuitka，__file__ 指向的是编译后的模块位置（通常在临时目录中），
        # 因此使用相对路径是安全的。
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.abspath(os.path.join(current_dir, "..", ".."))
    
    return os.path.join(base_path, relative_path)
