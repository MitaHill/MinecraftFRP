import json
from pathlib import Path
from PySide6.QtWidgets import QMessageBox

from src.utils.Crypto import decrypt_data, encrypt_data

def load_and_decrypt_server_list(dialog):
    """加载并解密服务器列表文件"""
    try:
        remote_file_path = Path("config/frp-server-list-remote.json")
        if not remote_file_path.exists():
            return False
            
        with open(remote_file_path, 'r', encoding='utf-8') as f:
            encrypted_data = f.read()
        
        decrypted_data = decrypt_data(encrypted_data, dialog.config_manager.encryption_key)
        if not decrypted_data:
            return False
        
        json_data = json.loads(decrypted_data)
        dialog.server_data = json_data.get('servers', [])
        return True
        
    except Exception as e:
        print(f"加载解密服务器列表失败: {e}")
        return False

def save_and_upload_server_list(dialog):
    """收集、加密并准备上传服务器列表"""
    try:
        servers = collect_table_data(dialog)
        if not servers:
            QMessageBox.warning(dialog, "错误", "没有有效的服务器数据")
            return None

        json_data = {'servers': servers}
        json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
        
        encrypted_data = encrypt_data(json_str, dialog.config_manager.encryption_key)
        if not encrypted_data:
            QMessageBox.critical(dialog, "错误", "数据加密失败")
            return None
        
        temp_file = Path("config/frp-server-list-upload.json")
        temp_file.parent.mkdir(exist_ok=True)
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(encrypted_data)
        
        return temp_file
        
    except Exception as e:
        QMessageBox.critical(dialog, "错误", f"保存过程中发生错误: {e}")
        return None

def collect_table_data(dialog):
    """从UI表格中收集服务器数据"""
    servers = []
    for row in range(dialog.server_table.rowCount()):
        items = [dialog.server_table.item(row, col) for col in range(4)]
        if all(item and item.text() for item in items):
            try:
                port = int(items[3].text().strip())
                server = {
                    'name': items[0].text().strip(),
                    'token': items[1].text().strip(),
                    'host': items[2].text().strip(),
                    'port': port
                }
                servers.append(server)
            except (ValueError, AttributeError):
                continue
    return servers
