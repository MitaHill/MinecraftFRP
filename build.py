"""
MinecraftFRP Build & Deploy Script (Modular Version)

简洁的构建脚本入口点，所有逻辑都已模块化到src_builder包中。

使用方法:
    python build.py --fast                # 快速构建（无LTO优化）
    python build.py --upload              # 构建并上传到服务器
    python build.py --fast --upload       # 快速构建并上传
    python build.py --clean               # 清理缓存后构建
    python build.py --verify-only         # 仅验证依赖
    python build.py --skip-updater        # 跳过更新器构建
"""

import sys
import os

# 设置环境变量以支持UTF-8输出（Windows）
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')  # 切换到UTF-8代码页
    # 重新配置stdout/stderr为UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

from src_builder.arg_parser import parse_arguments
from src_builder.v2_builder import V2Builder


def main():
    """构建脚本主入口函数"""
    args = parse_arguments()

    # [新增] 仅部署服务端模式检测
    if getattr(args, 'server_on', False) and not args.upload:
        print("[模式] 仅部署服务端 (Server Deployment Only)")
        from src_builder.config import BuildConfig
        from src_builder.deployer import Deployer
        
        cfg = BuildConfig()
        ssh_cfg = cfg.get_ssh_config()
        if not ssh_cfg:
            print("❌ 无法加载 SSH 配置")
            sys.exit(1)
            
        ssh_user = args.ssh_user or ssh_cfg.get('user')
        ssh_pass = args.ssh_pass or ssh_cfg.get('password')
        
        if not ssh_user or not ssh_pass:
            print("❌ SSH 凭据缺失")
            sys.exit(1)
            
        deployer = Deployer(ssh_cfg, ssh_user, ssh_pass)
        success = deployer.deploy_server("server")
        
        sys.exit(0 if success else 1)

    # 构建前置操作：自动清空 build/ 缓存并进行版本号自增
    import shutil
    from src_builder.config import BuildConfig
    build_dir = os.path.join(os.getcwd(), 'build')
    if os.path.isdir(build_dir):
        print("[前置检查] 正在清空构建缓存目录: .\\build\\ ...")
        # 仅清空内容，不删除 build 目录本身
        for name in os.listdir(build_dir):
            path = os.path.join(build_dir, name)
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    os.remove(path)
            except Exception as e:
                print(f"[WARN] 清理 {path} 失败: {e}")
    else:
        print("[前置检查] 未检测到 .\\build\\ 目录，跳过清理。")

    # 版本号自增（每次构建+1），并保存到 cicd.yaml
    cfg = BuildConfig()
    old_ver = cfg.get_version_string()
    new_ver = cfg.increment_version()
    if cfg.save_config():
        print(f"[版本管理] 版本号自增: {old_ver} -> {new_ver}")
    else:
        print("[版本管理] ❌ 无法写入 cicd.yaml，已终止。")
        sys.exit(1)

    # 默认使用安装器架构的构建器
    builder = V2Builder(args)

    exit_code = builder.run()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
