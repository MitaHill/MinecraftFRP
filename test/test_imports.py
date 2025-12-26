"""
测试所有installer模块的导入
"""
import sys
import traceback

def test_imports():
    print("🧪 测试installer模块导入...\n")
    
    modules_to_test = [
        ("installer.py主模块", "src_installer.installer"),
        ("GUI窗口", "src_installer.gui.installer_window"),
        ("安装管理器", "src_installer.core.install_manager"),
        ("配置管理", "src_installer.core.config_manager"),
        ("文件操作", "src_installer.core.file_operations"),
        ("日志工具", "src_installer.utils.logger"),
    ]
    
    results = []
    
    for name, module_path in modules_to_test:
        try:
            __import__(module_path)
            print(f"✅ {name}: {module_path}")
            results.append((name, True, None))
        except Exception as e:
            print(f"❌ {name}: {module_path}")
            print(f"   错误: {type(e).__name__}: {e}")
            results.append((name, False, e))
    
    print("\n" + "="*60)
    print("📊 导入测试总结:")
    success = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"   成功: {success}/{total}")
    
    if success < total:
        print("\n❌ 失败的模块:")
        for name, ok, err in results:
            if not ok:
                print(f"   - {name}: {err}")
                print(f"     Traceback:")
                traceback.print_exception(type(err), err, err.__traceback__)
    
    return success == total

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
