"""
导入辅助模块
自动处理开发环境和打包环境的导入差异
"""
import sys
import importlib

def smart_import(module_path, package_name):
    """
    智能导入：先尝试相对导入（打包后），失败则使用完整路径（开发时）
    
    Args:
        module_path: 相对路径，如 "core.config_manager"
        package_name: 包名，如 "src_installer"
    
    Returns:
        导入的模块
    
    Example:
        # 在 src_installer 中使用:
        ConfigManager = smart_import("core.config_manager", "src_installer").ConfigManager
    """
    try:
        # 打包后的路径 (相对导入)
        module = importlib.import_module(module_path)
        return module
    except (ImportError, ModuleNotFoundError):
        # 开发环境的路径 (完整路径)
        full_path = f"{package_name}.{module_path}"
        try:
            module = importlib.import_module(full_path)
            return module
        except (ImportError, ModuleNotFoundError) as e:
            raise ImportError(
                f"Failed to import {module_path} from either "
                f"relative path or {full_path}: {e}"
            )

def get_from_module(module_path, package_name, attr_name):
    """
    从模块中获取指定属性
    
    Example:
        ConfigManager = get_from_module("core.config_manager", "src_installer", "ConfigManager")
    """
    module = smart_import(module_path, package_name)
    return getattr(module, attr_name)
