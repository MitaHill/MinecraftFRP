import base64
import json
import os
import hashlib
from Crypto.Cipher import AES
from .LogManager import get_logger

logger = get_logger()

# 解密JSON文件
def decrypt_data(encrypted_data, key):
    try:
        encrypted_data = base64.b64decode(encrypted_data)
        iv = encrypted_data[:16]
        cipher_text = encrypted_data[16:]
        cipher = AES.new(key.encode('utf-8').ljust(16, b'\0')[:16], AES.MODE_CBC, iv)  # 密钥补齐到16字节
        decrypted = cipher.decrypt(cipher_text)
        pad_len = decrypted[-1]
        decrypted = decrypted[:-pad_len]
        return decrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"解密失败: {e}")
        return None

# 加密数据
def encrypt_data(data, key):
    try:
        # 生成随机IV
        iv = os.urandom(16)
        
        # 创建AES加密器
        cipher = AES.new(key.encode('utf-8').ljust(16, b'\0')[:16], AES.MODE_CBC, iv)
        
        # 数据填充到16字节的倍数
        data_bytes = data.encode('utf-8')
        pad_len = 16 - (len(data_bytes) % 16)
        padded_data = data_bytes + bytes([pad_len]) * pad_len
        
        # 加密数据
        encrypted = cipher.encrypt(padded_data)
        
        # 组合IV和加密数据，然后base64编码
        combined = iv + encrypted
        return base64.b64encode(combined).decode('utf-8')
        
    except Exception as e:
        logger.error(f"加密失败: {e}")
        return None

# 从JSON数据加载服务器列表
def load_servers_from_json(json_data):
    try:
        servers = {}
        for server in json_data['servers']:
            name = server['name']
            host = server['host']
            port = server['port']
            token = server['token']
            servers[name] = (host, port, token)
        return servers
    except Exception as e:
        logger.error(f"解析服务器列表失败: {e}")
        return None

def calculate_sha256(filepath):
    """Calculates the SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()