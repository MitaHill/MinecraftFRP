import subprocess
import re
import requests
import json
import os

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
        match = re.search(r"时间=(\d+)ms", output)
        return int(match.group(1)) if match else None
    except Exception as e:
        print(f"Ping 出错: {e}")
        return None

# 保存Ping数据到YAML文件
def save_ping_data(ping_results, filename="config/ping_data.yaml"):
    import yaml
    data = {name: result for name, result in ping_results.items()}
    try:
        with open(filename, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)
    except Exception as e:
        print(f"保存Ping数据出错: {e}")

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
            print(f"加载Ping数据出错: {e}")
    return {}

# 下载JSON文件
def download_json(url, local_path):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            return True
        else:
            return False
    except Exception as e:
        print(f"下载JSON文件失败: {e}")
        return False

# 读取JSON文件
def read_json_file(local_path):
    if os.path.exists(local_path):
        try:
            with open(local_path, 'r', encoding='utf-8') as f:
                return f.read()  # 返回字符串，因为加密数据是文本
        except Exception as e:
            print(f"读取JSON文件失败: {e}")
            return None
    return None