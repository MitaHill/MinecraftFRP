"""
测试脚本 - 验证 HTTP 修复

此脚本验证：
1. HttpManager 的 fetch_url_content 函数可以正常工作
2. SSL 降级机制正常
3. 编码处理正确
"""

import sys
from src.utils.HttpManager import fetch_url_content
from src.utils.LogManager import get_logger

logger = get_logger()

def test_http_manager():
    """测试 HttpManager 的统一接口"""
    print("="*60)
    print("测试 HttpManager.fetch_url_content()")
    print("="*60)

    test_urls = [
        ("https://z.clash.ink/chfs/shared/MinecraftFRP/Data/version.json", "版本检查"),
        ("https://z.clash.ink/chfs/shared/MinecraftFRP/Data/ads.json", "广告下载"),
        ("https://z.clash.ink/chfs/shared/MinecraftFRP/Data/frp-server-list.json", "服务器列表"),
    ]

    results = []
    for url, description in test_urls:
        print(f"\n测试: {description}")
        print(f"URL: {url}")
        try:
            content = fetch_url_content(url, timeout=10)
            status = "✅ 成功"
            print(f"结果: {status}")
            print(f"内容长度: {len(content)} 字符")
            print(f"内容预览: {content[:100]}...")
            results.append((description, True, None))
        except Exception as e:
            status = "❌ 失败"
            print(f"结果: {status}")
            print(f"错误: {e}")
            results.append((description, False, str(e)))

    # 打印总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    success_count = sum(1 for _, success, _ in results if success)
    total_count = len(results)
    print(f"成功: {success_count}/{total_count}")

    for desc, success, error in results:
        status = "✅" if success else "❌"
        print(f"{status} {desc}")
        if error:
            print(f"   错误: {error}")

    return success_count == total_count

if __name__ == "__main__":
    try:
        all_passed = test_http_manager()
        sys.exit(0 if all_passed else 1)
    except Exception as e:
        print(f"\n❌ 测试脚本出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

