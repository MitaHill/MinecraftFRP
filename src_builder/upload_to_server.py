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

def deploy_client_artifacts(local_exe, local_version_json, channel="dev", ssh_user=None, ssh_pass=None):
    """
    Deploy client installer and version.json to the remote server.
    """
    print(f"[模式] 部署客户端安装包 (Channel: {channel})")
    
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

    # Determine remote paths
    base_remote_path = "/root/chfs/share/MinecraftFRP"
    if channel == 'dev':
        remote_exe_path = f"{base_remote_path}/Dev/MitaHill_Dev_FRP.exe"
    else:
        remote_exe_path = f"{base_remote_path}/Stable/MitaHill_Stable_FRP.exe"
    
    # Create a new config for Deployer with specific paths
    deploy_config = ssh_cfg.copy()
    deploy_config['exe_path'] = remote_exe_path
    deploy_config['version_json_path'] = f"{base_remote_path}/Data/version.json"

    deployer = Deployer(deploy_config, user, password)
    return deployer.deploy(local_exe, local_version_json)

def main():
    parser = argparse.ArgumentParser(description="MinecraftFRP Upload Tool")
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--server", action="store_true", help="Deploy server backend code")
    mode_group.add_argument("--client", action="store_true", help="Deploy client artifacts (requires --exe and --version-json)")
    
    # Auth overrides
    parser.add_argument("--ssh-user", help="SSH Username (overrides config)")
    parser.add_argument("--ssh-pass", help="SSH Password (overrides config)")
    
    # Client arguments
    parser.add_argument("--exe", help="Path to local installer executable")
    parser.add_argument("--version-json", help="Path to local version.json")
    parser.add_argument("--channel", default="dev", choices=["dev", "stable"], help="Release channel (default: dev)")
    
    args = parser.parse_args()
    
    if args.server:
        success = deploy_server_backend(args.ssh_user, args.ssh_pass)
        sys.exit(0 if success else 1)
        
    elif args.client:
        if not args.exe or not args.version_json:
            print("❌ Error: --client mode requires --exe and --version-json")
            sys.exit(1)
            
        success = deploy_client_artifacts(
            args.exe, 
            args.version_json, 
            args.channel, 
            args.ssh_user, 
            args.ssh_pass
        )
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
