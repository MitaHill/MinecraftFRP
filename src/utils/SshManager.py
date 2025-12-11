"""
SSH连接管理器
用于连接服务器下载和上传服务器列表文件
"""

import paramiko
import os
import tempfile
from pathlib import Path
from src.utils.LogManager import get_logger

logger = get_logger()

class SSHManager:
    def __init__(self):
        self.client = None
        
    def connect(self, hostname, username, password, port=22):
        """建立SSH连接"""
        logger.info(f"正在尝试连接SSH: 主机={hostname}, 用户名={username}, 端口={port}")
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(hostname, port=port, username=username, password=password, timeout=10)
            logger.info("SSH连接成功")
            return True
        except Exception as e:
            logger.error(f"SSH连接失败: {e}", exc_info=True)
            return False
    
    def download_file(self, remote_path, local_path):
        """下载文件"""
        if not self.client:
            logger.error("下载文件失败: SSH客户端未连接")
            return False
        logger.info(f"正在下载文件: 从 {remote_path} 到 {local_path}")
        try:
            sftp = self.client.open_sftp()
            sftp.get(remote_path, local_path)
            sftp.close()
            logger.info("文件下载成功")
            return True
        except Exception as e:
            logger.error(f"下载文件失败: {e}", exc_info=True)
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
            logger.error(f"上传文件失败: {e}")
            return False
    
    def close(self):
        """关闭SSH连接"""
        if self.client:
            self.client.close()
            self.client = None

class ServerManagementConfig:
    def __init__(self):
        """此功能已移至独立的管理员工具。"""
        pass

    def verify_admin_password(self, password):
        return False
    
    def download_server_list(self):
        return False, "此功能已禁用"
    
    def upload_server_list(self, local_file_path):
        return False, "此功能已禁用"
