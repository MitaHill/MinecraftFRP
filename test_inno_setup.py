#!/usr/bin/env python3
"""
测试 Inno Setup 编译
仅测试安装包生成步骤
"""
import subprocess
import sys
from pathlib import Path


def test_inno_setup():
    """测试 Inno Setup 编译"""
    print()
    print("=" * 70)
    print("  🔧 测试 Inno Setup 编译")
    print("=" * 70)
    print()
    
    # 检查必要文件
    print("[1/3] 检查必要文件...")
    
    iscc = Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe")
    setup_iss = Path("setup.iss")
    build_dir = Path("dist/MinecraftFRP_build")
    
    if not iscc.exists():
        print(f"❌ Inno Setup 未安装: {iscc}")
        return 1
    print(f"✅ Inno Setup: {iscc}")
    
    if not setup_iss.exists():
        print(f"❌ 配置文件不存在: {setup_iss}")
        return 1
    print(f"✅ 配置文件: {setup_iss}")
    
    if not build_dir.exists():
        print(f"❌ 构建目录不存在: {build_dir}")
        print("   请先运行: python build.py --v2")
        return 1
    print(f"✅ 构建目录: {build_dir}")
    
    # 执行编译
    print()
    print("[2/3] 开始编译...")
    print()
    
    output_dir = Path("dist").absolute()
    
    cmd = [
        str(iscc),
        str(setup_iss.absolute()),
        f"/O{output_dir}"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        
        print()
        print("[3/3] 检查输出...")
        
        # 查找生成的安装包
        setup_files = list(output_dir.glob("MinecraftFRP_Setup_*.exe"))
        
        if setup_files:
            for setup_file in setup_files:
                size_mb = setup_file.stat().st_size / (1024 * 1024)
                print(f"✅ 生成安装包: {setup_file.name} ({size_mb:.2f} MB)")
            
            print()
            print("=" * 70)
            print("  ✅ Inno Setup 编译成功！")
            print("=" * 70)
            return 0
        else:
            print("❌ 未找到生成的安装包")
            return 1
            
    except subprocess.CalledProcessError as e:
        print()
        print("❌ 编译失败！")
        print()
        print("错误输出:")
        print(e.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(test_inno_setup())
