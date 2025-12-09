import subprocess
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QMessageBox)
from src.gui.dialogs.NetworkDialogs import NetworkInfoDialog, PingDialog
from src.utils.PathUtils import get_resource_path

class ToolboxTab(QWidget):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        ping_button = QPushButton("Ping 测试")
        ping_button.clicked.connect(self.open_ping_dialog)
        layout.addWidget(ping_button)

        tracert_button = QPushButton("路由追踪")
        tracert_button.clicked.connect(self.open_tracert)
        layout.addWidget(tracert_button)

        view_network_adapters_button = QPushButton("查看网络适配器")
        view_network_adapters_button.clicked.connect(self.view_network_adapters)
        layout.addWidget(view_network_adapters_button)

        layout.addStretch()

    def open_ping_dialog(self):
        # Uses parent's servers list, assuming parent has self.SERVERS
        # Or we can pass servers to ToolboxTab.
        # For now, using parent_window.SERVERS if available, or parent_window itself as parent.
        # The original code passed 'self' (MainWindow) to PingDialog.
        dialog = PingDialog(self.parent_window)
        dialog.exec()

    def open_tracert(self):
        try:
            exe_path = get_resource_path("base\\tracert_gui.exe")
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
        # Copied logic from original main_window.py
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
