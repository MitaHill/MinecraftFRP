#!/usr/bin/env python3
"""
Inno Setup 环境检查脚本
检查构建环境和依赖项是否就绪
"""
import os
import sys
from pathlib import Path


def print_section(title: str):
    """打印分隔线标题"""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print()


def check_inno_setup() -> bool:
    """检查 Inno Setup 是否安装"""
    print("[1/4] 检查 Inno Setup...")
    
    iscc_path = Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe")
    
    if iscc_path.exists():
        print(f"  ✅ 已安装: {iscc_path}")
        return True
    else:
        print(f"  ❌ 未找到 Inno Setup 编译器")
        print(f"     请下载并安装: https://jrsoftware.org/isdl.php")
        return False


def check_setup_iss() -> bool:
    """检查 setup.iss 配置文件"""
    print()
    print("[2/4] 检查 setup.iss...")
    
    iss_file = Path("setup.iss")
    
    if iss_file.exists():
        print(f"  ✅ 找到配置文件: {iss_file}")
        return True
    else:
        print(f"  ❌ 未找到 setup.iss")
        return False


def check_build_output() -> bool:
    """检查构建输出目录"""
    print()
    print("[3/4] 检查构建输出...")
    
    build_dir = Path("dist/MinecraftFRP_build")
    
    if not build_dir.exists():
        print(f"  ⚠️  构建目录不存在: {build_dir}")
        print(f"     请先运行: python build.py --v2")
        return False
    
    print(f"  ✅ 找到构建目录: {build_dir}")
    
    # 检查 launcher.exe
    launcher = build_dir / "launcher.exe"
    if launcher.exists():
        size_mb = launcher.stat().st_size / (1024 * 1024)
        print(f"    ✅ launcher.exe ({size_mb:.2f} MB)")
    else:
        print(f"    ❌ launcher.exe 不存在")
        return False
    
    # 检查 app.dist 目录
    app_dist = build_dir / "app.dist"
    if app_dist.exists() and app_dist.is_dir():
        file_count = sum(1 for _ in app_dist.rglob("*") if _.is_file())
        print(f"    ✅ app.dist/ ({file_count} 个文件)")
        
        # 检查 MinecraftFRP.exe
        main_exe = app_dist / "MinecraftFRP.exe"
        if main_exe.exists():
            size_mb = main_exe.stat().st_size / (1024 * 1024)
            print(f"      ✅ MinecraftFRP.exe ({size_mb:.2f} MB)")
        else:
            print(f"      ❌ MinecraftFRP.exe 不存在")
            return False
    else:
        print(f"    ❌ app.dist/ 目录不存在")
        return False
    
    return True


def check_resources():
    """检查资源文件"""
    print()
    print("[4/4] 检查资源文件...")
    
    base_dir = Path("base")
    if base_dir.exists() and base_dir.is_dir():
        file_count = sum(1 for _ in base_dir.rglob("*") if _.is_file())
        print(f"  ✅ base/ ({file_count} 个文件)")
    else:
        print(f"  ⚠️  base/ 目录不存在（可选）")
    
    config_dir = Path("config")
    if config_dir.exists() and config_dir.is_dir():
        file_count = sum(1 for _ in config_dir.rglob("*") if _.is_file())
        print(f"  ✅ config/ ({file_count} 个文件)")
    else:
        print(f"  ⚠️  config/ 目录不存在（可选）")


def main():
    """主函数"""
    print_section("🔍 Inno Setup 配置验证")
    
    # 执行所有检查
    checks = [
        check_inno_setup(),
        check_setup_iss(),
        check_build_output(),
    ]
    
    check_resources()
    
    print()
    print_section("检查结果")
    
    if all(checks):
        print("  ✅ 所有检查通过！可以执行构建")
        print()
        print("💡 执行构建命令:")
        print("   python build.py --v2")
        print()
        return 0
    else:
        print("  ❌ 部分检查失败，请修复后再试")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
