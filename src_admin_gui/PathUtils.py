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
    elif "__compiled__" in globals() or hasattr(sys, "frozen"):
        # Nuitka 或其他打包环境
        # 优先检查 exe 同级目录 (例如单文件模式或开发调试)
        exe_dir = os.path.dirname(sys.argv[0])
        
        # 如果同级目录不存在 base，则尝试上级目录 (安装器结构: app/MitaHill-FRP-APP/exe vs app/base)
        if not os.path.exists(os.path.join(exe_dir, "base")) and os.path.exists(os.path.join(exe_dir, "..", "base")):
            base_path = os.path.abspath(os.path.join(exe_dir, ".."))
        else:
            base_path = exe_dir
    else:
        # 开发环境
        # 假设 PathUtils.py 位于 src/utils/ 目录下
        # 项目根目录为 ../../
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.abspath(os.path.join(current_dir, "..", ".."))
    
    return os.path.join(base_path, relative_path)
