import os
import random
import subprocess
import sys
import datetime
import webbrowser
import signal
import socket
import struct
import re
import threading
import time
import json
import requests
import argparse
from threading import Lock
from pathlib import Path
from Crypto.Cipher import AES
import base64
from PySide6.QtCore import QThread, Signal, Qt, QMutex, QMutexLocker, QTimer, QEventLoop
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, \
    QLineEdit, QTextEdit, QMessageBox, QProgressDialog, QMainWindow, QInputDialog, QDialog, QTabWidget
from PySide6.QtGui import QTextCursor, QIcon, QCloseEvent

# 默认服务器配置
DEFAULT_SERVERS = {
    "宁波": ("c.clash.ink", 7000, "kindmita"),
    "北京1": ("beijing1.clash.ink", 7000, "kindmita"),
    "北京2": ("beijing2.clash.ink", 7000, "kindmita"),
    "香港": ("clash.ink", 7000, "kindmita"),
    "美国": ("us-1.clash.ink", 7000, "kindmita")
}

# 主题样式
STYLE = {
    "light": """
QWidget{background:#f8f9fa;font:14px 'Microsoft YaHei';}
QLabel{color:#495057;margin-bottom:8px;}
QPushButton{background:#4CAF50;color:#fff;padding:8px 16px;border:none;border-radius:4px;}
QPushButton:hover{background:#45a049;}
QLineEdit,QTextEdit{background:#fff;border:1px solid #dee2e6;padding:8px;border-radius:4px;}
QComboBox{min-width:150px;}
QTabBar::tab {
    background: white;
    color: black;
    padding: 8px;
    border: 1px solid #dee2e6;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background: #d0d0d0;
    color: black;
    border-bottom: 2px solid #4CAF50;
}
QTabBar::tab:hover {
    background: #f0f0f0;
}
QTabWidget::pane {
    background: #f8f9fa;
}
""",
    "dark": """
QWidget{background:#1e1e1e;font:14px 'Microsoft YaHei';color:#e0e0e0;}
QLabel{color:#b3b3b3;}
QPushButton{background:#fff;color:#333;padding:8px 16px;border:none;border-radius:4px;}
QPushButton:hover{background:#f0f0f0;}
QLineEdit,QTextEdit{background:#2d2d2d;border:1px solid #404040;padding:8px;border-radius:4px;color:#e0e0e0;}
QComboBox{min-width:150px;}
QTabBar::tab {
    background: black;
    color: white;
    padding: 8px;
    border: 1px solid #404040;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background: #444444;
    color: white;
    border-bottom: 2px solid #4CAF50;
}
QTabBar::tab:hover {
    background: #555555;
}
QTabWidget::pane {
    background: #1e1e1e;
}
""",
}

# Minecraft LAN 探测配置
MCAST_GRP = '224.0.2.60'
MCAST_PORT = 4445
BUFFER_SIZE = 1024
MOTD_RE = re.compile(rb'\[MOTD\](.*?)\[/MOTD\]')
PORT_RE = re.compile(rb'\[AD\](\d+)\[/AD\]')

# 配置文件名
CONFIG_FILENAME = "frpc.ini"
PING_DATA_FILENAME = "ping_data.json"

# 避免使用的端口列表
RESERVED_PORTS = {80, 443, 3306, 8080, 25565}

# 线程超时时间（毫秒）
THREAD_TIMEOUT = 3000


# 生成随机端口
def gen_port():
    port_mutex = Lock()
    with port_mutex:
        while (p := random.randint(10000, 65534)) in RESERVED_PORTS:
            pass
        return p


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


# 保存Ping数据到JSON文件
def save_ping_data(ping_results):
    data = {name: result for name, result in ping_results.items()}
    try:
        with open(PING_DATA_FILENAME, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存Ping数据出错: {e}")


# 加载Ping数据从JSON文件
def load_ping_data():
    if os.path.exists(PING_DATA_FILENAME):
        try:
            with open(PING_DATA_FILENAME, "r", encoding="utf-8") as f:
                return json.load(f)
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
        print(f"解密失败: {e}")
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
        print(f"解析服务器列表失败: {e}")
        return None


# Ping 线程类
class PingThread(QThread):
    ping_results = Signal(dict)

    def __init__(self, servers):
        super().__init__()
        self.servers = servers

    def run(self):
        results = {}
        for name, (host, _, _) in self.servers.items():
            ping = ping_host(host)
            item_text = f"{name}    {ping}ms" if ping is not None else f"{name}    timeout"
            results[name] = item_text
        self.ping_results.emit(results)


class AdManager:
    def __init__(self):
        self.ads = []
        self.current_ad_index = 0
        self._start_download_thread()

    def _start_download_thread(self):
        thread = threading.Thread(target=self.download_ads, daemon=True)
        thread.start()

    def download_ads(self):
        try:
            response = requests.get(
                "https://clash.ink/file/minecraft-frp/ads.json",
                timeout=5
            )
            if response.status_code == 200:
                with open("ads.json", "w", encoding="utf-8") as f:
                    f.write(response.text)
                self.parse_ads()
            else:
                print(f"下载ads.json失败，状态码: {response.status_code}")
                self.try_load_local_ads()
        except Exception as e:
            print(f"下载ads.json时出错: {e}")
            self.try_load_local_ads()

    def parse_ads(self):
        try:
            with open("ads.json", "r", encoding="utf-8") as f:
                self.ads = json.load(f)
        except Exception as e:
            print(f"解析ads.json时出错: {e}")
            self.load_default_ads()

    def try_load_local_ads(self):
        if os.path.exists("ads.json"):
            print("发现本地ads.json，尝试读取。")
            self.parse_ads()
        else:
            print("本地没有ads.json，使用默认广告。")
            self.load_default_ads()

    def load_default_ads(self):
        self.ads = [
            {"show": "请更新到最新版本，此版本可能有一些问题。", "url": "https://example.com"}
        ]

    def get_next_ad(self):
        if not self.ads:
            return None
        ad = self.ads[self.current_ad_index]
        self.current_ad_index = (self.current_ad_index + 1) % len(self.ads)
        return ad


class FrpcThread(QThread):
    out = Signal(str)
    warn = Signal(str)
    success = Signal()
    error = Signal(str)
    terminated = Signal()

    def __init__(self, ini_path):
        super().__init__()
        self.ini_path = ini_path
        self.p = None
        self.mutex = QMutex()
        self._stop_requested = False

    def run(self):
        si, fb = subprocess.STARTUPINFO(), subprocess.CREATE_NO_WINDOW
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            if not os.path.exists("frpc.exe"):
                self.error.emit("frpc.exe 未找到，请确保文件存在")
                return

            self.p = subprocess.Popen(
                ["frpc.exe", "-c", self.ini_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                startupinfo=si,
                creationflags=fb
            )

            for line in self.p.stdout:
                if self._stop_requested:
                    break

                line_stripped = line.strip()
                self.out.emit(line_stripped)

                if "start proxy success" in line_stripped:
                    self.success.emit()
                elif "already" in line_stripped:
                    self.warn.emit("端口已被占用，尝试重新分配端口...")

        except Exception as e:
            self.error.emit(f"运行frpc时出错: {str(e)}")
        finally:
            self._cleanup()
            self.terminated.emit()

    def stop(self):
        with QMutexLocker(self.mutex):
            self._stop_requested = True
            if self.p:
                try:
                    self.p.terminate()
                    deadline = time.time() + 1
                    while time.time() < deadline and self.p.poll() is None:
                        time.sleep(0.1)
                    if self.p.poll() is None:
                        self.p.kill()
                except Exception as e:
                    print(f"停止frpc进程时出错: {e}")
                finally:
                    self.p = None

    def _cleanup(self):
        with QMutexLocker(self.mutex):
            if self.p:
                try:
                    if self.p.poll() is None:
                        self.p.terminate()
                        deadline = time.time() + 1
                        while time.time() < deadline and self.p.poll() is None:
                            time.sleep(0.1)
                        if self.p.poll() is None:
                            self.p.kill()
                except:
                    pass
                finally:
                    self.p = None


class MinecraftLANPoller(QThread):
    port_found = Signal(str)
    terminated = Signal()

    def __init__(self):
        super().__init__()
        self._stop_requested = False
        self.mutex = QMutex()
        self.last_port = None

    def run(self):
        while not self._stop_requested:
            try:
                port = self._poll_minecraft_lan()
                if port and port != self.last_port:
                    self.last_port = port
                    self.port_found.emit(port)
            except Exception as e:
                print(f"LAN轮询器出错: {e}", file=sys.stderr)

            for _ in range(3):
                if self._stop_requested:
                    break
                time.sleep(0.1)

        self.terminated.emit()

    def _poll_minecraft_lan(self):
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(0.5)

            try:
                sock.bind(('', MCAST_PORT))
            except OSError as e:
                print(f"绑定端口失败: {e}", file=sys.stderr)
                return None

            mreq = struct.pack("=4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                port_match = PORT_RE.search(data)
                if port_match:
                    return port_match.group(1).decode()
            except socket.timeout:
                pass
            except Exception as e:
                print(f"接收LAN广播时出错: {e}", file=sys.stderr)

            return None

        except Exception as e:
            print(f"创建LAN轮询器套接字时出错: {e}", file=sys.stderr)
            return None
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass

    def stop(self):
        with QMutexLocker(self.mutex):
            self._stop_requested = True


class ConfigManager:
    def __init__(self, filename=CONFIG_FILENAME):
        self.filename = filename
        self.mutex = Lock()

    def create_config(self, host, port, token, local_port, remote_port, user_id):
        with self.mutex:
            config_content = f"""[common]
server_addr={host}
server_port={port}
token={token}

[map{user_id}]
type=tcp
local_ip=127.0.0.1
local_port={local_port}
remote_port={remote_port}
"""
            try:
                with open(self.filename, "w") as f:
                    f.write(config_content)
                return True
            except Exception as e:
                print(f"写入配置文件出错: {e}")
                return False

    def delete_config(self):
        with self.mutex:
            try:
                if os.path.exists(self.filename):
                    os.remove(self.filename)
                    return True
            except Exception as e:
                print(f"删除配置文件出错: {e}")
            return False


class NetworkInfoDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("网络适配器信息")
        self.setMinimumSize(600, 400)
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)

    def set_info(self, html):
        self.text_area.setHtml(html)
        QTimer.singleShot(0, self.adjust_size)

    def adjust_size(self):
        doc = self.text_area.document()
        ideal_width = doc.idealWidth()
        new_width = min(ideal_width * 1.2, 800)
        current_height = 400
        self.resize(new_width, current_height)


class PingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ping 测试")
        self.setGeometry(200, 200, 400, 300)
        layout = QVBoxLayout(self)
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("输入要 Ping 的地址")
        layout.addWidget(self.address_input)
        self.ping_button = QPushButton("开始 Ping")
        self.ping_button.clicked.connect(self.start_ping)
        layout.addWidget(self.ping_button)
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)
        self.ping_manager = PingManager()

    def start_ping(self):
        address = self.address_input.text().strip()
        if not address:
            QMessageBox.warning(self, "错误", "请输入要 Ping 的地址")
            return
        result = self.ping_manager.ping(address)
        self.result_text.setPlainText(result)


class PortMappingApp(QWidget):
    inst = None
    link = ""

    def __init__(self, args=None):
        super().__init__()
        PortMappingApp.inst = self
        self.args = args
        self.th = None
        self.lan_poller = None
        self.config_manager = ConfigManager()
        self.app_mutex = QMutex()
        self.is_closing = False
        self.ad_manager = AdManager()

        # 加载服务器列表
        self.load_servers()

        if self.args and (self.args.local_port or self.args.auto_find or self.args.server):
            self.run_non_gui()
        else:
            self.setupUI()
            self.ad_timer = QTimer()
            self.ad_timer.timeout.connect(self.update_ad)
            self.ad_timer.start(3000)
            self.initial_port_query()
            self.startLANPoller()

        if not os.path.exists("frpc.exe"):
            if self.args and (self.args.local_port or self.args.auto_find or self.args.server):
                print("错误: frpc.exe 未找到")
                sys.exit(1)
            else:
                QMessageBox.critical(self, "错误", "frpc.exe 未找到，程序即将退出。")
                sys.exit(1)

    def load_servers(self):
        url = "https://clash.ink/file/frp-server-list.json"
        local_path = "frp-server-list.json"
        key = "clashman"

        # 尝试下载JSON文件
        if download_json(url, local_path):
            print("成功下载JSON文件")
        else:
            print("下载JSON文件失败，尝试使用本地文件")

        # 读取JSON文件
        encrypted_data = read_json_file(local_path)
        if encrypted_data:
            # 解密
            decrypted_data = decrypt_data(encrypted_data, key)
            if decrypted_data:
                # 解析JSON
                json_data = json.loads(decrypted_data)
                servers = load_servers_from_json(json_data)
                if servers:
                    self.SERVERS = servers
                    print("成功加载服务器列表")
                else:
                    print("解析服务器列表失败，使用默认列表")
                    self.SERVERS = DEFAULT_SERVERS
            else:
                print("解密失败，使用默认列表")
                self.SERVERS = DEFAULT_SERVERS
        else:
            print("未找到JSON文件，使用默认列表")
            self.SERVERS = DEFAULT_SERVERS

    def start_web_browser(self):
        try:
            url = "https://b.clash.ink/#/memo/8"
            if not webbrowser.open(url):
                raise RuntimeError("无法启动默认浏览器")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开网址失败: {e}")

    def setupUI(self):
        self.setWindowTitle("Minecraft 端口映射工具")
        self.setGeometry(100, 100, 400, 550)

        try:
            icon_path = Path("Minecraft-Logo-ICON.ico")
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
        except Exception as e:
            print(f"设置图标出错: {e}", file=sys.stderr)

        h = datetime.datetime.now().hour
        self.theme = 'light' if 7 <= h < 18 else 'dark'
        self.setStyleSheet(STYLE[self.theme])

        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Mapping tab
        mapping_widget = QWidget()
        mapping_layout = QVBoxLayout(mapping_widget)
        mapping_layout.setSpacing(10)
        mapping_layout.setContentsMargins(15, 15, 15, 15)

        server_layout = QHBoxLayout()
        help_button = QPushButton("帮助")
        help_button.setMaximumWidth(60)
        help_button.setStyleSheet(
            "QPushButton{background:#1E90FF;color:#fff;padding:8px 16px;border:none;border-radius:4px;}"
            "QPushButton:hover{background:#1E90FF;}"
        )
        help_button.clicked.connect(self.start_web_browser)
        server_layout.addWidget(help_button)

        server_layout.addWidget(QLabel("选择线路:"))
        self.server_combo = QComboBox()
        saved_pings = load_ping_data()
        for name in self.SERVERS.keys():
            item_text = saved_pings.get(name, f"{name}    未测试")
            self.server_combo.addItem(item_text)
        server_layout.addWidget(self.server_combo)
        mapping_layout.addLayout(server_layout)

        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("输入本地端口:"))
        self.port_edit = QLineEdit()
        self.port_edit.setPlaceholderText("1-65535")
        port_layout.addWidget(self.port_edit)
        mapping_layout.addLayout(port_layout)

        button_layout = QHBoxLayout()
        self.start_button = QPushButton("启动映射")
        self.start_button.clicked.connect(self.start_map)
        button_layout.addWidget(self.start_button)
        self.copy_button = QPushButton("复制链接")
        self.copy_button.clicked.connect(self.copy_link)
        self.copy_button.setEnabled(False)
        button_layout.addWidget(self.copy_button)
        mapping_layout.addLayout(button_layout)

        mapping_layout.addWidget(QLabel("运行日志:"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        mapping_layout.addWidget(self.log_text)
        self.link_label = QLabel("映射地址: 无")
        mapping_layout.addWidget(self.link_label)
        self.ad_label = QLabel("准备就绪")
        self.ad_label.setOpenExternalLinks(True)
        mapping_layout.addWidget(self.ad_label)

        self.tab_widget.addTab(mapping_widget, "映射")

        # Toolbox tab
        toolbox_widget = QWidget()
        toolbox_layout = QVBoxLayout(toolbox_widget)
        toolbox_layout.setSpacing(10)
        toolbox_layout.setContentsMargins(15, 15, 15, 15)

        ping_button = QPushButton("Ping 测试")
        ping_button.clicked.connect(self.open_ping_dialog)
        toolbox_layout.addWidget(ping_button)

        tracert_button = QPushButton("路由追踪")
        tracert_button.clicked.connect(self.open_tracert)
        toolbox_layout.addWidget(tracert_button)

        view_network_adapters_button = QPushButton("查看网络适配器")
        view_network_adapters_button.clicked.connect(self.view_network_adapters)
        toolbox_layout.addWidget(view_network_adapters_button)

        toolbox_layout.addStretch()
        self.tab_widget.addTab(toolbox_widget, "工具箱")

        self.load_ping_values()

        self.ping_timer = QTimer()
        self.ping_timer.timeout.connect(self.load_ping_values)
        self.ping_timer.start(3000)

    def load_ping_values(self):
        self.ping_thread = PingThread(self.SERVERS)
        self.ping_thread.ping_results.connect(self.update_server_combo)
        self.ping_thread.start()

    def update_server_combo(self, results):
        for i, name in enumerate(self.SERVERS.keys()):
            self.server_combo.setItemText(i, results.get(name, f"{name}    timeout"))
        save_ping_data(results)

    def run_non_gui(self):
        server_name = self.args.server if self.args.server else list(self.SERVERS.keys())[0]
        if server_name not in self.SERVERS:
            print(f"错误: 无效的服务器名称 '{server_name}'。可用服务器: {', '.join(self.SERVERS.keys())}")
            sys.exit(1)

        local_port = None
        if self.args.auto_find:
            local_port = self._poll_minecraft_lan()
            if local_port:
                print(f"检测到Minecraft游戏端口: {local_port}")
            else:
                print("未检测到Minecraft游戏端口")
                if not self.args.local_port:
                    print("错误: 未提供 --local_port 且自动查找失败")
                    sys.exit(1)
        if self.args.local_port:
            local_port = self.args.local_port
            if not local_port.isdigit() or not 1 <= int(local_port) <= 65535:
                print("错误: 请输入有效端口 (1-65535)")
                sys.exit(1)

        if not local_port:
            print("错误: 必须提供 --local_port 或启用 --auto-find 并成功检测端口")
            sys.exit(1)

        self.start_map_non_gui(server_name, local_port)

    def start_map_non_gui(self, server_name, local_port):
        host, port, token = self.SERVERS[server_name]
        remote_port = gen_port()
        user_id = random.randint(10000, 99999)

        if not self.config_manager.create_config(host, port, token, local_port, remote_port, user_id):
            print("错误: 无法写入配置文件，请检查权限")
            sys.exit(1)

        PortMappingApp.link = f"{host}:{remote_port}"
        print(f"开始映射本地端口 {local_port} 到 {host}:{remote_port}")

        self.th = FrpcThread(CONFIG_FILENAME)
        self.th.out.connect(lambda msg: print(msg))
        self.th.warn.connect(lambda msg: print(f"警告: {msg}"))
        self.th.success.connect(lambda: print(f"映射成功！映射地址: {PortMappingApp.link}"))
        self.th.error.connect(lambda msg: print(f"错误: {msg}") or sys.exit(1))
        self.th.terminated.connect(lambda: print("frpc进程已终止") or sys.exit(0))
        self.th.start()

        loop = QEventLoop()
        self.th.terminated.connect(loop.quit)
        loop.exec()

    def update_ad(self):
        ad = self.ad_manager.get_next_ad()
        if ad:
            ad_color = "cyan" if self.theme == "dark" else "blue"
            self.ad_label.setText(f'<a href="{ad["url"]}" style="color:{ad_color}">{ad["show"]}</a>')
        else:
            self.ad_label.setText("无广告")

    def initial_port_query(self):
        port = self._poll_minecraft_lan()
        if port:
            self.port_edit.setText(port)
            self.log(f"检测到Minecraft游戏端口: {port}", "green")
            self.log(f"请点击“启动映射”按钮来开启映射", "red")
        else:
            self.log("未检测到Minecraft游戏端口", "orange")

    def _poll_minecraft_lan(self):
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(2)

            sock.bind(('', MCAST_PORT))
            mreq = struct.pack("=4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

            data, _ = sock.recvfrom(BUFFER_SIZE)
            port_match = PORT_RE.search(data)
            if port_match:
                return port_match.group(1).decode()
        except socket.timeout:
            return None
        except Exception as e:
            print(f"UDP查询出错: {e}")
            return None
        finally:
            if sock:
                sock.close()
        return None

    def startLANPoller(self):
        with QMutexLocker(self.app_mutex):
            if self.lan_poller is None:
                self.lan_poller = MinecraftLANPoller()
                self.lan_poller.port_found.connect(self.set_port)
                self.lan_poller.terminated.connect(self.onLANPollerTerminated)
                self.lan_poller.start()

    def stopLANPoller(self, wait=True):
        with QMutexLocker(self.app_mutex):
            if self.lan_poller and self.lan_poller.isRunning():
                self.lan_poller.stop()
                if wait:
                    loop = QEventLoop()
                    timer = QTimer()
                    timer.setSingleShot(True)
                    timer.timeout.connect(loop.quit)
                    self.lan_poller.terminated.connect(loop.quit)
                    timer.start(THREAD_TIMEOUT)
                    loop.exec()

                    if timer.isActive():
                        timer.stop()
                    else:
                        print("LAN轮询线程超时未响应，强制继续")

    def onLANPollerTerminated(self):
        if self.is_closing:
            self.lan_poller = None
            self.continueClosing()

    def set_port(self, port):
        self.port_edit.setText(port)

    def log(self, message, color=None):
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)

        if color == "blue" and self.theme == "dark":
            color = "cyan"

        if color:
            self.log_text.insertHtml(f"<span style='color:{color};'>{message}</span><br>")
        else:
            self.log_text.append(message)

        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)

    def start_map(self):
        with QMutexLocker(self.app_mutex):
            if self.is_closing:
                return

            if self.th and self.th.isRunning():
                self.log("正在关闭旧进程...", "orange")
                self.th.stop()

                loop = QEventLoop()
                timer = QTimer()
                timer.setSingleShot(True)
                timer.timeout.connect(loop.quit)
                self.th.terminated.connect(loop.quit)
                timer.start(THREAD_TIMEOUT)
                loop.exec()

                if timer.isActive():
                    timer.stop()
                    self.log("已终止旧进程", "green")
                else:
                    self.log("进程超时未响应，强制终止", "red")

            local_port = self.port_edit.text().strip()
            if not local_port.isdigit() or not 1 <= int(local_port) <= 65535:
                QMessageBox.warning(self, "错误", "请输入有效端口 (1-65535)")
                return

            server_text = self.server_combo.currentText()
            server_name = server_text.split()[0]
            host, port, token = self.SERVERS[server_name]

            remote_port = gen_port()
            user_id = random.randint(10000, 99999)

            if not self.config_manager.create_config(host, port, token, local_port, remote_port, user_id):
                QMessageBox.warning(self, "错误", f"无法写入配置文件，请检查权限")
                return

            PortMappingApp.link = f"{host}:{remote_port}"

            self.th = FrpcThread(CONFIG_FILENAME)
            self.th.out.connect(self.log_text.append)
            self.th.warn.connect(lambda m: self.log(m, "red"))
            self.th.success.connect(self.disp_succ)
            self.th.error.connect(lambda m: self.show_error(m))
            self.th.terminated.connect(self.onFrpcTerminated)
            self.th.start()

            self.log(f"开始映射本地端口 {local_port} 到 {host}:{remote_port}", "blue")
            self.log(f"请注意，如果房间的本地端口{local_port}变更需要重新点击启动映射按钮", "red")

    def onFrpcTerminated(self):
        if self.is_closing:
            self.th = None
            self.continueClosing()

    def disp_succ(self):
        self.link_label.setText(f"映射地址: {PortMappingApp.link}")
        self.link_label.setStyleSheet("color: green; font-weight: bold; font-size: 16px;")
        self.copy_button.setEnabled(True)
        self.log(f"")
        self.log(f"点击复制链接将游戏链接复制到剪切板，分享给别人即可联机游玩", "blue")
        self.log(f"映射成功！", "green")

    def show_error(self, message):
        self.log(f"⚠️ {message}", "red")
        QMessageBox.warning(self, "错误", message)
        self.log("映射失败", "red")

    def copy_link(self):
        QApplication.clipboard().setText(PortMappingApp.link)
        self.log("------", "red")
        self.log("游戏链接地址已复制到剪切板", "red")
        self.log("------", "red")
        QTimer.singleShot(3000, self.update_ad)

    def closeEvent(self, event: QCloseEvent):
        self.is_closing = True
        self.ad_timer.stop()
        self.ping_timer.stop()

        self.progress_dialog = QProgressDialog("正在关闭程序，请稍候...", None, 0, 0, self)
        self.progress_dialog.setWindowTitle("关闭中")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.show()

        self.close_timer = QTimer()
        self.close_timer.setSingleShot(True)
        self.close_timer.timeout.connect(self.forceClose)
        self.close_timer.start(THREAD_TIMEOUT)

        frpc_running = False
        with QMutexLocker(self.app_mutex):
            if self.th and self.th.isRunning():
                frpc_running = True
                self.log("正在关闭frpc进程...", "orange")
                self.th.stop()

        lan_running = False
        with QMutexLocker(self.app_mutex):
            if self.lan_poller and self.lan_poller.isRunning():
                lan_running = True
                self.lan_poller.stop()

        ping_running = False
        if hasattr(self, 'ping_thread') and self.ping_thread.isRunning():
            ping_running = True
            self.ping_thread.wait()

        if not frpc_running and not lan_running and not ping_running:
            self.forceClose()
            event.accept()
        else:
            event.ignore()

    def continueClosing(self):
        all_terminated = True

        with QMutexLocker(self.app_mutex):
            if self.th is not None:
                all_terminated = False

            if self.lan_poller is not None:
                all_terminated = False

        if all_terminated:
            self.forceClose()

    def forceClose(self):
        if hasattr(self, 'close_timer') and self.close_timer.isActive():
            self.close_timer.stop()

        with QMutexLocker(self.app_mutex):
            if self.th and self.th.isRunning():
                self.th.terminate()
                self.th = None

            if self.lan_poller and self.lan_poller.isRunning():
                self.lan_poller.terminate()
                self.lan_poller = None

        self.config_manager.delete_config()

        if hasattr(self, 'progress_dialog') and self.progress_dialog.isVisible():
            self.progress_dialog.close()

        QApplication.quit()

    def open_ping_dialog(self):
        dialog = PingDialog(self)
        dialog.exec()

    def open_tracert(self):
        try:
            subprocess.Popen("tracert_gui.exe")
        except FileNotFoundError:
            QMessageBox.critical(self, "错误", "tracert_gui.exe 未找到")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开 tracert_gui.exe 失败: {e}")

    def view_network_adapters(self):
        try:
            result = subprocess.run("ipconfig /all", capture_output=True, text=True, check=True)
            info = result.stdout
            adapters = self.parse_ipconfig(info)
            html = self.generate_html(adapters)
            dialog = NetworkInfoDialog(self)
            dialog.set_info(html)
            dialog.exec()
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "错误", f"执行 ipconfig 失败: {e}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发生错误: {e}")

    def parse_ipconfig(self, info):
        adapters = []
        current_adapter = None
        lines = info.splitlines()

        for line in lines:
            if line.startswith("   ") and line.strip().endswith(":"):
                if current_adapter:
                    adapters.append(current_adapter)
                current_adapter = {"name": line.strip().rstrip(":")}
            elif current_adapter and ":" in line:
                key, value = [part.strip() for part in line.split(":", 1)]
                if "物理地址" in key or "Physical Address" in key:
                    current_adapter["mac"] = value
                elif "IPv4 地址" in key or "IPv4 Address" in key:
                    current_adapter["ipv4"] = value.split("(")[0].strip()
                elif "子网掩码" in key or "Subnet Mask" in key:
                    current_adapter["subnet"] = value
                elif "默认网关" in key or "Default Gateway" in key:
                    current_adapter["gateway"] = value if value else "N/A"
                elif "DNS 服务器" in key or "DNS Servers" in key:
                    current_adapter["dns"] = value

        if current_adapter:
            adapters.append(current_adapter)

        complete_adapters = []
        incomplete_adapters = []
        required_keys = {"mac", "ipv4", "subnet", "gateway", "dns"}

        for adapter in adapters:
            if all(key in adapter for key in required_keys) and adapter["ipv4"] != "N/A":
                complete_adapters.append(adapter)
            else:
                incomplete_adapters.append(adapter)

        return complete_adapters + incomplete_adapters

    def generate_html(self, adapters):
        html = """
        <html>
        <body style='font-family: Microsoft YaHei;'>
        <style>
            table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
            td { padding: 8px; border: 1px solid #ddd; }
            .field-name { font-weight: 600; font-size: 14px; width: 40%; }
            .ipv4 { font-weight: bold; font-size: 16px; }
        </style>
        """
        for adapter in adapters:
            html += f"<h3>{adapter['name']}</h3>"
            html += "<table>"
            html += f"<tr><td class='field-name'>物理地址</td><td>{adapter.get('mac', 'N/A')}</td></tr>"
            html += f"<tr><td class='field-name'>IPv4 地址</td><td class='ipv4'>{adapter.get('ipv4', 'N/A')}</td></tr>"
            html += f"<tr><td class='field-name'>子网掩码</td><td>{adapter.get('subnet', 'N/A')}</td></tr>"
            html += f"<tr><td class='field-name'>默认网关</td><td>{adapter.get('gateway', 'N/A')}</td></tr>"
            html += f"<tr><td class='field-name'>DNS 服务器</td><td>{adapter.get('dns', 'N/A')}</td></tr>"
            html += "</table>"
        html += "</body></html>"
        return html


def sigint_handler(sig_num, frame):
    if PortMappingApp.inst:
        PortMappingApp.inst.forceClose()
    sys.exit(0)


def parse_args():
    parser = argparse.ArgumentParser(description="Minecraft 端口映射工具")
    parser.add_argument('--local_port', type=str, help="本地端口号 (1-65535)")
    parser.add_argument('--auto-find', action='store_true', help="优先自动寻找Minecraft LAN端口")
    parser.add_argument('--server', type=str, choices=DEFAULT_SERVERS.keys(), help="服务器名称")
    return parser.parse_args()


class PingManager:
    def __init__(self):
        pass

    def ping(self, address, count=4):
        try:
            p = subprocess.Popen(
                ["ping", "-n", str(count), address],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True
            )
            output, _ = p.communicate()
            return output
        except Exception as e:
            return f"发生错误: {e}"


if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigint_handler)
    args = parse_args()
    app = QApplication(sys.argv)
    w = PortMappingApp(args)
    if not (args.local_port or args.auto_find or args.server):
        w.show()
    sys.exit(app.exec())