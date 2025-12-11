"""
Argument Parser - 命令行参数解析器
负责解析和验证命令行参数
"""
import argparse


def parse_arguments():
    """
    解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数对象
    """
    parser = argparse.ArgumentParser(
        description="MinecraftFRP build & deploy script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build.py                          # 默认使用安装器架构进行构建（快速）
  python build.py --upload                 # 构建并上传到服务器
  python build.py -u "修复BUG并优化性能"       # 构建并指定更新日志
  python build.py --fast                   # 快速构建（禁用LTO）
  python build.py --clean                  # 构建前清理缓存
  python build.py --verify-only            # 仅验证依赖
        """
    )
    
    # 构建相关参数
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Enable fast build (no LTO optimization)"
    )
    
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean Nuitka cache before building"
    )
    
    parser.add_argument(
        "--skip-updater",
        action="store_true",
        help="Skip building updater (reuse existing)"
    )
    
    # 发布通道（dev/stable）
    parser.add_argument(
        "--channel", "-c",
        choices=["dev", "stable"],
        default="dev",
        help="选择发布通道：dev（默认）或 stable"
    )
    
    # 更新日志（替代 Git 生成机制）
    parser.add_argument(
        "--update-messages", "-u",
        type=str,
        help="手动指定本次构建的更新日志（将写入 version.json），忽略 Git 日志"
    )
    
    # 部署相关参数
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload artifacts via SSH after build"
    )
    
    parser.add_argument(
        "--ssh-user",
        type=str,
        help="SSH username (overrides cicd.yaml)"
    )
    
    parser.add_argument(
        "--ssh-pass",
        type=str,
        help="SSH password (overrides cicd.yaml)"
    )
    
    # 服务端部署
    parser.add_argument(
        "--server-on",
        action="store_true",
        help="Deploy server-side code to /root/MitaHillFRP-Server"
    )
    
    # 其他参数
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify dependencies and exit"
    )
    
    args = parser.parse_args()
    
    # 默认启用快速模式以提升构建速度（安装器架构无需LTO）
    if not args.fast:
        args.fast = True
    
    return args
