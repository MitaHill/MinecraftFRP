"""
SSH连接管理器
用于连接服务器下载和上传服务器列表文件
"""

import paramiko
import os
import tempfile
from pathlib import Path

class SSHManager:
    def __init__(self):
        self.client = None
        
    def connect(self, hostname, username, password, port=22):
        """建立SSH连接"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(hostname, port=port, username=username, password=password, timeout=10)
            return True
        except Exception as e:
            print(f"SSH连接失败: {e}")
            return False
    
    def download_file(self, remote_path, local_path):
        """下载文件"""
        if not self.client:
            return False
        try:
            sftp = self.client.open_sftp()
            sftp.get(remote_path, local_path)
            sftp.close()
            return True
        except Exception as e:
            print(f"下载文件失败: {e}")
            return False
    
    def upload_file(self, local_path, remote_path):
        """上传文件"""
        if not self.client:
            return False
        try:
            sftp = self.client.open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()
            return True
        except Exception as e:
            print(f"上传文件失败: {e}")
            return False
    
    def close(self):
        """关闭SSH连接"""
        if self.client:
            self.client.close()
            self.client = None

class ServerManagementConfig:
    def __init__(self):
        self.ssh_manager = SSHManager()
        self.admin_password = "kindmitaishere@gmail.com"
        self.server_host = "clash.ink"
        self.server_user = "root"
        self.server_password = "q174285396q"
        self.remote_file_path = "/opt/1panel/apps/openresty/openresty/www/sites/clash.ink/index/file/frp-server-list.json"
        self.encryption_key = "clashman"
        self.config_dir = Path("config")
        
    def verify_admin_password(self, password):
        """验证管理员密码"""
        return password == self.admin_password
    
    def download_server_list(self):
        """下载服务器列表文件"""
        try:
            # 连接SSH
            if not self.ssh_manager.connect(self.server_host, self.server_user, self.server_password):
                return False, "SSH连接失败"
            
            # 下载到config目录
            local_path = self.config_dir / "frp-server-list-remote.json"
            self.config_dir.mkdir(exist_ok=True)
            
            if self.ssh_manager.download_file(self.remote_file_path, str(local_path)):
                self.ssh_manager.close()
                return True, f"服务器列表已下载到 {local_path}"
            else:
                self.ssh_manager.close()
                return False, "下载文件失败"
                
        except Exception as e:
            self.ssh_manager.close()
            return False, f"下载过程中发生错误: {e}"
    
    def upload_server_list(self, local_file_path):
        """上传服务器列表文件"""
        try:
            # 连接SSH
            if not self.ssh_manager.connect(self.server_host, self.server_user, self.server_password):
                return False, "SSH连接失败"
            
            if self.ssh_manager.upload_file(local_file_path, self.remote_file_path):
                self.ssh_manager.close()
                return True, "服务器列表已成功上传"
            else:
                self.ssh_manager.close()
                return False, "上传文件失败"
                
        except Exception as e:
            self.ssh_manager.close()
            return False, f"上传过程中发生错误: {e}"