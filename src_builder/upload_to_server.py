"""
Script to upload/deploy files to the remote server.
Can be used to deploy the server backend or client artifacts.
"""
import sys
import os
import argparse
from pathlib import Path

# Add project root to path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from src_builder.config import BuildConfig
from src_builder.deployer import Deployer

def deploy_server_backend(ssh_user=None, ssh_pass=None):
    """
    Deploy the 'server' directory to the remote server.
    """
    print("[模式] 仅部署服务端 (Server Deployment Only)")
    
    cfg = BuildConfig()
    ssh_cfg = cfg.get_ssh_config()
    if not ssh_cfg:
        print("❌ 无法加载 SSH 配置")
        return False
        
    user = ssh_user or ssh_cfg.get('user')
    password = ssh_pass or ssh_cfg.get('password')
    
    if not user or not password:
        print("❌ SSH 凭据缺失")
        return False
        
    deployer = Deployer(ssh_cfg, user, password)
    return deployer.deploy_server("server")

def main():
    parser = argparse.ArgumentParser(description="MinecraftFRP Upload Tool")
    parser.add_argument("--server", action="store_true", help="Deploy server backend code")
    parser.add_argument("--ssh-user", help="SSH Username (overrides config)")
    parser.add_argument("--ssh-pass", help="SSH Password (overrides config)")
    
    args = parser.parse_args()
    
    if args.server:
        success = deploy_server_backend(args.ssh_user, args.ssh_pass)
        sys.exit(0 if success else 1)
    else:
        print("Please specify an action (e.g., --server)")
        sys.exit(1)

if __name__ == "__main__":
    main()
