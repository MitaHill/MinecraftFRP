"""
Module to upload/deploy files to the remote server.
Used by build.py and v2_builder.py to deploy server backend or client artifacts.
"""
import sys
import os
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
