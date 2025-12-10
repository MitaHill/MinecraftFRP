"""
MinecraftFRP Build & Deploy Script (Modular Version)

简洁的构建脚本入口点，所有逻辑都已模块化到src_builder包中。

使用方法:
    python build.py --fast                # 快速构建（无LTO优化）
    python build.py --upload              # 构建并上传到服务器
    python build.py --fast --upload       # 快速构建并上传
    python build.py --clean               # 清理缓存后构建
    python build.py --verify-only         # 仅验证依赖
    python build.py --skip-updater        # 跳过更新器构建
"""

import sys
import os

# 设置环境变量以支持UTF-8输出（Windows）
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')  # 切换到UTF-8代码页
    # 重新配置stdout/stderr为UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

from src_builder.arg_parser import parse_arguments
from src_builder.build_orchestrator import BuildOrchestrator
from src_builder.v2_builder import V2Builder


def main():
    """构建脚本主入口函数"""
    args = parse_arguments()
    
    # 根据参数选择构建器
    if args.v2:
        builder = V2Builder(args)
    else:
        builder = BuildOrchestrator(args)
    
    exit_code = builder.run()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
