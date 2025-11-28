import os
import random
import sys
import datetime
import webbrowser
from pathlib import Path
from PySide6.QtCore import QTimer, QMutex, QMutexLocker, QEventLoop
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QMessageBox, QTabWidget, QApplication)
from PySide6.QtGui import QTextCursor, QIcon, QCloseEvent

from src.gui.Styles import STYLE
from src.gui.tabs.MappingTab import MappingTab
from src.gui.tabs.ToolboxTab import ToolboxTab
from src.gui.tabs.SettingsTab import SettingsTab
from src.core.config_manager import ConfigManager
from src.core.frpc_thread import FrpcThread
from src.core.ping_thread import PingThread
from src.network.minecraft_lan import MinecraftLANPoller, poll_minecraft_lan_once
from src.utils.ad_manager import AdManager
from src.utils.port_generator import gen_port
from src.network.ping_utils import save_ping_data
from src.core.yaml_config import YamlConfigManager, DEFAULT_APP_CONFIG
from src.utils.path_utils import get_resource_path

# 线程超时时间（毫秒）
THREAD_TIMEOUT = 3000

class PortMappingApp(QWidget):
    inst = None
    link = ""

    def __init__(self, servers, args=None):
        super().__init__()
        PortMappingApp.inst = self
        self.SERVERS = servers
        self.args = args
        self.th = None
        self.lan_poller = None
        self.config_manager = ConfigManager()
        self.app_mutex = QMutex()
        self.is_closing = False
        self.ad_manager = AdManager()
        
        # 加载配置
        self.yaml_config = YamlConfigManager()
        self.app_config = self.yaml_config.load_config("app_config.yaml", DEFAULT_APP_CONFIG)
        
        # 设置相关变量
        self.auto_mapping_enabled = self.app_config.get("settings", {}).get("auto_mapping", False)
        self.dark_mode_override = self.app_config.get("settings", {}).get("dark_mode_override", False)
        self.force_dark_mode = self.app_config.get("settings", {}).get("force_dark_mode", False)

        if self.args and (self.args.local_port or self.args.auto_find or self.args.server):
            self.run_non_gui()
        else:
            self.setupUI()
            self.ad_timer = QTimer()
            self.ad_timer.timeout.connect(self.update_ad)
            self.ad_timer.start(3000)
            self.initial_port_query()
            self.startLANPoller()
        
        frpc_path = get_resource_path("frpc.exe")
        if not os.path.exists(frpc_path):
            if self.args and (self.args.local_port or self.args.auto_find or self.args.server):
                print(f"错误: frpc.exe 未找到: {frpc_path}")
                sys.exit(1)
            else:
                QMessageBox.critical(self, "错误", f"frpc.exe 未找到，程序即将退出。\n路径: {frpc_path}")
                sys.exit(1)

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

        # 自动加载程序图标
        try:
            icon_path = Path(get_resource_path("logo.ico"))
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
                print(f"已加载程序图标: {icon_path}")
            else:
                print(f"未找到 logo.ico 文件: {icon_path}")
        except Exception as e:
            print(f"设置图标出错: {e}", file=sys.stderr)

        # 主题逻辑
        if self.dark_mode_override:
            self.theme = 'dark' if self.force_dark_mode else 'light'
        else:
            h = datetime.datetime.now().hour
            self.theme = 'light' if 7 <= h < 18 else 'dark'
        self.setStyleSheet(STYLE[self.theme])

        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Initialize Tabs
        self.mapping_tab = MappingTab(self, self.SERVERS)
        self.toolbox_tab = ToolboxTab(self)
        self.settings_tab = SettingsTab(self)

        self.tab_widget.addTab(self.mapping_tab, "映射")
        self.tab_widget.addTab(self.toolbox_tab, "工具箱")
        self.tab_widget.addTab(self.settings_tab, "设置")

        self.load_ping_values()

        self.ping_timer = QTimer()
        self.ping_timer.timeout.connect(self.load_ping_values)
        self.ping_timer.start(3000)

    def load_ping_values(self):
        self.ping_thread = PingThread(self.SERVERS)
        self.ping_thread.ping_results.connect(self.update_server_combo)
        self.ping_thread.start()

    def update_server_combo(self, results):
        # Update combo box in MappingTab
        if results is None:
            results = {}
        for i, name in enumerate(self.SERVERS.keys()):
            self.mapping_tab.server_combo.setItemText(i, results.get(name, f"{name}    timeout"))
        save_ping_data(results)

    def run_non_gui(self):
        server_name = self.args.server if self.args.server else list(self.SERVERS.keys())[0]
        if server_name not in self.SERVERS:
            print(f"错误: 无效的服务器名称 '{server_name}'。可用服务器: {', '.join(self.SERVERS.keys())}")
            sys.exit(1)

        local_port = None
        if self.args.auto_find:
            local_port = poll_minecraft_lan_once()
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

        self.th = FrpcThread("config/frpc.ini")
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
            self.mapping_tab.ad_label.setText(f'<a href="{ad["url"]}" style="color:{ad_color}">{ad["show"]}</a>')
        else:
            self.mapping_tab.ad_label.setText("无广告")

    def initial_port_query(self):
        port = poll_minecraft_lan_once()
        if port:
            self.mapping_tab.port_edit.setText(port)
            self.log(f"检测到Minecraft游戏端口: {port}", "green")
            self.log("请点击'启动映射'按钮来开启映射", "red")
        else:
            self.log("未检测到Minecraft游戏端口", "orange")

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
        self.lan_poller = None

    def set_port(self, port):
        self.mapping_tab.port_edit.setText(port)
        
        # 如果启用了自动映射，则自动开始映射
        if self.auto_mapping_enabled:
            self.log(f"自动映射: 检测到端口{port}，开始自动映射", "blue")
            QTimer.singleShot(1000, self.auto_start_mapping)  # 延迟1秒后自动开始映射
    
    def auto_start_mapping(self):
        """自动开始映射"""
        if not self.auto_mapping_enabled:
            return
            
        # 检查是否已有映射在运行，如果有则先停止
        if self.th and self.th.isRunning():
            self.log("自动映射: 检测到端口变化，重新开始映射", "orange")
            self.th.stop()
            QTimer.singleShot(2000, self.start_map)  # 等待2秒后重新开始
        else:
            # 直接开始映射
            self.start_map()
            
            # 如果映射成功，自动复制链接到剪贴板
            if hasattr(self, 'th') and self.th:
                self.th.success.connect(self.auto_copy_link)

    def log(self, message, color=None):
        cursor = self.mapping_tab.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.mapping_tab.log_text.setTextCursor(cursor)

        if color == "blue" and self.theme == "dark":
            color = "cyan"

        if color:
            self.mapping_tab.log_text.insertHtml(f"<span style='color:{color};'>{message}</span><br>")
        else:
            self.mapping_tab.log_text.append(message)

        cursor.movePosition(QTextCursor.End)
        self.mapping_tab.log_text.setTextCursor(cursor)

    def on_auto_mapping_changed(self, state):
        """自动映射选项变更处理"""
        self.auto_mapping_enabled = bool(state)
        self.app_config["settings"]["auto_mapping"] = self.auto_mapping_enabled
        self.yaml_config.save_config("app_config.yaml", self.app_config)
        
        if self.auto_mapping_enabled:
            self.log("已启用自动映射模式", "green")
        else:
            self.log("已关闭自动映射模式", "orange")

    def on_dark_mode_changed(self, state):
        """夜间模式选项变更处理"""
        is_checked = bool(state)
        self.dark_mode_override = True
        self.force_dark_mode = is_checked
        
        self.app_config["settings"]["dark_mode_override"] = self.dark_mode_override
        self.app_config["settings"]["force_dark_mode"] = self.force_dark_mode
        self.yaml_config.save_config("app_config.yaml", self.app_config)
        
        # 立即应用主题变更
        self.theme = 'dark' if self.force_dark_mode else 'light'
        self.setStyleSheet(STYLE[self.theme])
        
        mode_text = "夜间模式" if self.force_dark_mode else "昼间模式"
        self.log(f"已切换到{mode_text}，暂停自动昼夜切换", "blue")

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

            local_port = self.mapping_tab.port_edit.text().strip()
            if not local_port.isdigit() or not 1 <= int(local_port) <= 65535:
                QMessageBox.warning(self, "错误", "请输入有效端口 (1-65535)")
                return

            server_text = self.mapping_tab.server_combo.currentText()
            server_name = server_text.split()[0]
            host, port, token = self.SERVERS[server_name]

            remote_port = gen_port()
            user_id = random.randint(10000, 99999)

            if not self.config_manager.create_config(host, port, token, local_port, remote_port, user_id):
                QMessageBox.warning(self, "错误", f"无法写入配置文件，请检查权限")
                return

            PortMappingApp.link = f"{host}:{remote_port}"

            self.th = FrpcThread("config/frpc.ini")
            self.th.out.connect(self.mapping_tab.log_text.append)
            self.th.warn.connect(lambda m: self.log(m, "red"))
            self.th.success.connect(self.disp_succ)
            self.th.error.connect(lambda m: self.show_error(m))
            self.th.terminated.connect(self.onFrpcTerminated)
            self.th.start()

            self.log(f"开始映射本地端口 {local_port} 到 {host}:{remote_port}", "blue")
            self.log(f"请注意，如果房间的本地端口{local_port}变更需要重新点击启动映射按钮", "red")

    def onFrpcTerminated(self):
        self.th = None

    def disp_succ(self):
        self.mapping_tab.link_label.setText(f"映射地址: {PortMappingApp.link}")
        self.mapping_tab.link_label.setStyleSheet("color: green; font-weight: bold; font-size: 16px;")
        self.mapping_tab.copy_button.setEnabled(True)
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
    
    def auto_copy_link(self):
        """自动复制链接到剪贴板（自动映射模式使用）"""
        if self.auto_mapping_enabled and PortMappingApp.link:
            QApplication.clipboard().setText(PortMappingApp.link)
            self.log("自动映射: 映射地址已自动复制到剪贴板", "green")

    def closeEvent(self, event: QCloseEvent):
        self.is_closing = True
        if hasattr(self, 'ad_timer'):
            self.ad_timer.stop()
        if hasattr(self, 'ping_timer'):
            self.ping_timer.stop()

        with QMutexLocker(self.app_mutex):
            if self.th and self.th.isRunning():
                self.log("正在关闭frpc进程...", "orange")
                self.th.stop()
                self.th.wait()

            if self.lan_poller and self.lan_poller.isRunning():
                self.lan_poller.stop()
                self.lan_poller.wait()

        self.config_manager.delete_config()
        QApplication.quit()

    def open_ping_dialog(self):
        dialog = PingDialog(self)
        dialog.exec()
    
    def open_server_management(self):
        """打开服务器管理配置对话框"""
        try:
            dialog = ServerManagementDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开服务器管理配置失败: {e}")

    def open_tracert(self):
        try:
            exe_path = get_resource_path("tracert_gui.exe")
            if not os.path.exists(exe_path):
                QMessageBox.critical(self, "错误", f"tracert_gui.exe 未找到\n路径: {exe_path}")
                return
            subprocess.Popen(exe_path)
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
        "
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