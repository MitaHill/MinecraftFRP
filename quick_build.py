#!/usr/bin/env python3
"""
快速构建脚本
简化版 build.py --v2 的快捷方式
"""
import subprocess
import sys
from pathlib import Path


def print_banner():
    """打印横幅"""
    print()
    print("=" * 70)
    print("  🚀 MinecraftFRP V2 快速构建")
    print("=" * 70)
    print()


def check_venv():
    """检查虚拟环境是否激活"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ 虚拟环境已激活")
        return True
    else:
        print("⚠️  虚拟环境未激活")
        print("   请先运行: .venv\\Scripts\\activate")
        print("   或使用完整路径: .venv\\Scripts\\python.exe quick_build.py")
        return False


def run_build():
    """执行构建"""
    print()
    print("📌 开始构建...")
    print()
    
    try:
        # 调用 build.py --v2
        result = subprocess.run(
            [sys.executable, "build.py", "--v2"],
            check=True
        )
        
        print()
        print("=" * 70)
        print("  ✅ 构建完成！")
        print("=" * 70)
        print()
        
        # 列出生成的安装包
        dist_dir = Path("dist")
        if dist_dir.exists():
            print("📦 安装包位置:")
            for setup_file in dist_dir.glob("MinecraftFRP_Setup_*.exe"):
                size_mb = setup_file.stat().st_size / (1024 * 1024)
                print(f"   {setup_file} ({size_mb:.2f} MB)")
            print()
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print()
        print("=" * 70)
        print("  ❌ 构建失败！")
        print("=" * 70)
        print()
        print(f"错误代码: {e.returncode}")
        return 1
    except KeyboardInterrupt:
        print()
        print("⚠️  构建被用户中断")
        return 130


def main():
    """主函数"""
    print_banner()
    
    if not check_venv():
        return 1
    
    return run_build()


if __name__ == "__main__":
    sys.exit(main())
