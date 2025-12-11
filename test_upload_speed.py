"""
测试 SFTP 上传速度优化效果
快速验证新的部署参数
"""
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src_builder.config import BuildConfig
from src_builder.deployer import Deployer


def test_upload_speed():
    """测试上传速度"""
    print("=" * 80)
    print("SFTP 上传速度测试")
    print("=" * 80)
    
    # 加载配置
    config = BuildConfig()
    ssh_cfg = config.get_ssh_config()
    
    print(f"\n目标服务器: {ssh_cfg['host']}")
    print(f"用户名: {ssh_cfg['user']}")
    
    # 创建测试文件（10MB）
    test_file = Path("test_upload_10mb.bin")
    test_size_mb = 10
    
    if not test_file.exists():
        print(f"\n创建 {test_size_mb}MB 测试文件...")
        with open(test_file, 'wb') as f:
            f.write(os.urandom(test_size_mb * 1024 * 1024))
        print("✅ 测试文件创建完成")
    
    # 创建临时 version.json
    version_json = Path("test_version.json")
    with open(version_json, 'w') as f:
        f.write('{"version": "test"}')
    
    # 执行上传测试
    print(f"\n开始上传测试 ({test_size_mb}MB 文件)...")
    print("-" * 80)
    
    deployer = Deployer(
        ssh_cfg,
        ssh_cfg['user'],
        ssh_cfg['password']
    )
    
    # 修改上传路径为临时测试路径
    deployer.exe_remote_path = "/tmp/test_upload_10mb.bin"
    deployer.version_remote_path = "/tmp/test_version.json"
    
    success = deployer.deploy(str(test_file), str(version_json))
    
    # 清理
    if test_file.exists():
        test_file.unlink()
    if version_json.exists():
        version_json.unlink()
    
    if success:
        print("\n" + "=" * 80)
        print("✅ 上传测试成功！")
        print("=" * 80)
        print("\n💡 如果速度达到 2MB/s+，说明优化生效")
        print("💡 如果速度仍然很慢，请检查网络带宽和服务器性能")
    else:
        print("\n❌ 上传测试失败")
    
    return success


if __name__ == "__main__":
    try:
        test_upload_speed()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
