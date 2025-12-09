"""
测试updater提取机制
"""
import sys
import os

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.UpdaterManager import UpdaterManager

def test_updater_extraction():
    print("="*80)
    print("测试 UpdaterManager")
    print("="*80)
    
    print(f"\n1. 检测编译状态:")
    is_compiled = UpdaterManager.is_compiled()
    print(f"   is_compiled() = {is_compiled}")
    print(f"   sys.argv[0] = {sys.argv[0]}")
    
    print(f"\n2. 获取路径:")
    try:
        embedded_path = UpdaterManager.get_updater_embedded_path()
        print(f"   内嵌路径: {embedded_path}")
        print(f"   内嵌文件存在: {os.path.exists(embedded_path)}")
    except Exception as e:
        print(f"   获取内嵌路径失败: {e}")
    
    runtime_path = UpdaterManager.get_runtime_updater_path()
    print(f"   运行时路径: {runtime_path}")
    print(f"   运行时文件存在: {os.path.exists(runtime_path)}")
    
    if is_compiled:
        print(f"\n3. 提取updater:")
        result = UpdaterManager.extract_updater()
        if result:
            print(f"   ✅ 提取成功: {result}")
            print(f"   文件大小: {os.path.getsize(result)} bytes")
        else:
            print(f"   ❌ 提取失败")
    else:
        print(f"\n3. 跳过提取（开发环境）")
    
    print("\n" + "="*80)
    print("测试完成")
    print("="*80)

if __name__ == "__main__":
    test_updater_extraction()
