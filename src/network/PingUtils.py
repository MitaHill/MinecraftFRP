import subprocess
import re
import os
import socket
import time
from src.utils.HttpManager import fetch_url_content
from src.utils.LogManager import get_logger

logger = get_logger()

# Ping 函数，仅支持Windows
def ping_host(host):
    try:
        p = subprocess.Popen(
            ["ping", "-n", "1", "-w", "1000", host],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW,
            text=True
        )
        output, _ = p.communicate()
        # 兼容中文 "时间=xxms" 和英文 "time=xxms" / "Time=xxms"
        match = re.search(r"(?:时间|time|Time)[=<](\d+)ms", output, re.IGNORECASE)
        return int(match.group(1)) if match else None
    except Exception as e:
        logger.error(f"Ping 出错: {e}")
        return None

# TCP端口测试函数
def test_tcp_port(host, port, timeout=2):
    """测试TCP端口连通性
    
    Args:
        host: 主机地址
        port: 端口号
        timeout: 超时时间（秒）
    
    Returns:
        dict: 包含success, latency, error的字典
    """
    try:
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        elapsed = int((time.time() - start_time) * 1000)  # 毫秒
        sock.close()
        
        if result == 0:
            return {'success': True, 'latency': elapsed, 'error': None}
        else:
            return {'success': False, 'latency': elapsed, 'error': f'连接失败 (错误码: {result})'}
    except socket.timeout:
        return {'success': False, 'latency': timeout*1000, 'error': '连接超时'}
    except Exception as e:
        logger.error(f"TCP端口测试出错 {host}:{port}: {e}")
        return {'success': False, 'latency': 0, 'error': str(e)}

# 保存Ping数据到YAML文件
def save_ping_data(ping_results, filename="config/ping_data.yaml"):
    import yaml
    data = {name: result for name, result in ping_results.items()}
    try:
        with open(filename, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)
    except Exception as e:
        logger.error(f"保存Ping数据出错: {e}")

# 加载Ping数据从YAML文件
def load_ping_data(filename="config/ping_data.yaml"):
    import yaml
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                # 确保返回字典，yaml.safe_load可能返回None
                return data if data is not None else {}
        except Exception as e:
            logger.error(f"加载Ping数据出错: {e}")
    return {}

# 下载JSON文件
def download_json(url, local_path):
    try:
        content = fetch_url_content(url)
        with open(local_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"下载JSON文件失败: {e}")
        return False

# 读取JSON文件
def read_json_file(local_path):
    if os.path.exists(local_path):
        try:
            with open(local_path, 'r', encoding='utf-8') as f:
                return f.read()  # 返回字符串，因为加密数据是文本
        except Exception as e:
            logger.error(f"读取JSON文件失败: {e}")
            return None
    return None
