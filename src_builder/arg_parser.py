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
  python build.py --v2                      # V2 build with Inno Setup (fast by default)
  python build.py --v2 --upload             # V2 build and upload to server
  python build.py --fast                    # V1 fast build without LTO
  python build.py --upload                  # V1 build and upload to server
  python build.py --clean                   # Clean build cache before building
  python build.py --verify-only             # Only verify dependencies
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
    
    parser.add_argument(
        "--v2",
        action="store_true",
        help="Build using v2 installer-based architecture"
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
    
    # 其他参数
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify dependencies and exit"
    )
    
    args = parser.parse_args()
    
    # 如果使用v2架构，默认启用fast模式（Inno Setup不需要LTO）
    if args.v2 and not args.fast:
        args.fast = True
    
    return args
