"""
测试 Launcher 清理旧安装包功能
"""
import sys
import os
from pathlib import Path

# 模拟环境
DOCUMENTS_PATH = Path.home() / "Documents" / "MitaHillFRP"
DOWNLOADS_PATH = DOCUMENTS_PATH / "downloads"

def test_cleanup():
    """测试清理功能"""
    print("=" * 60)
    print("测试 Launcher 清理旧安装包功能")
    print("=" * 60)
    
    # 创建测试环境
    DOWNLOADS_PATH.mkdir(parents=True, exist_ok=True)
    
    # 创建模拟的旧安装包
    test_installers = [
        "0.5.50_MitaHill_FRP_Dev_Install.exe",
        "0.5.51_MitaHill_FRP_Stable_Installer.exe",
        "0.5.52_MitaHill_FRP_Dev_Install.exe",
    ]
    
    print(f"\n📁 下载目录: {DOWNLOADS_PATH}")
    print("\n创建测试文件...")
    
    for installer in test_installers:
        file_path = DOWNLOADS_PATH / installer
        with open(file_path, 'wb') as f:
            f.write(b"fake installer content")
        print(f"  ✅ 创建: {installer}")
    
    # 显示当前文件列表
    print("\n📦 当前安装包:")
    current_files = list(DOWNLOADS_PATH.glob("*.exe"))
    for f in current_files:
        size = f.stat().st_size
        print(f"  - {f.name} ({size} bytes)")
    
    print(f"\n总计: {len(current_files)} 个文件")
    
    # 模拟清理逻辑
    print("\n🧹 执行清理...")
    cleaned_count = 0
    for installer in DOWNLOADS_PATH.glob("*.exe"):
        try:
            installer.unlink()
            cleaned_count += 1
            print(f"  🗑️  删除: {installer.name}")
        except Exception as e:
            print(f"  ❌ 删除失败: {installer.name} - {e}")
    
    # 验证清理结果
    print("\n✅ 清理完成")
    remaining_files = list(DOWNLOADS_PATH.glob("*.exe"))
    
    if len(remaining_files) == 0:
        print(f"✅ 成功清理 {cleaned_count} 个文件")
        print("📂 下载目录已清空")
    else:
        print(f"⚠️  仍有 {len(remaining_files)} 个文件未删除:")
        for f in remaining_files:
            print(f"  - {f.name}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_cleanup()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
