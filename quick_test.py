"""快速测试 - 验证 SSL 降级修复"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("测试 SSL 降级修复")
print("="*60)

try:
    print("\n1. 导入模块...")
    from src.utils.HttpManager import fetch_url_content
    print("   ✅ 模块导入成功")
    
    print("\n2. 测试 SSL 降级 (clash.ink 有 SSL 问题)...")
    test_url = "https://z.clash.ink/chfs/shared/MinecraftFRP/Data/ads.json"
    print(f"   URL: {test_url}")
    
    try:
        content = fetch_url_content(test_url, timeout=15)
        print(f"   ✅ 成功! 内容长度: {len(content)} 字符")
        print(f"   预览: {content[:100]}...")
        print("\n🎉 测试通过! SSL 降级功能正常工作。")
        sys.exit(0)
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        print("\n⚠️ SSL 降级仍有问题")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
except Exception as e:
    print(f"\n❌ 测试出错: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

