import random
from PySide6.QtCore import QTimer, QMutexLocker
from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtGui import QTextCursor

from src.core.frpc_thread import FrpcThread
from src.utils.port_generator import gen_port
from src.gui.main_window.threads import wait_for_thread
from src.gui.Styles import STYLE

def set_port(window, port):
    """当检测到端口时，设置端口并触发自动映射"""
    window.mapping_tab.port_edit.setText(port)
    if window.auto_mapping_enabled:
        log_message(window, f"自动映射: 检测到端口{port}，开始自动映射", "blue")
        QTimer.singleShot(1000, lambda: auto_start_mapping(window))

def auto_start_mapping(window):
    """自动开始映射的实现"""
    if not window.auto_mapping_enabled:
        return
    
    if window.th and window.th.isRunning():
        log_message(window, "自动映射: 检测到端口变化，重新开始映射", "orange")
        window.th.stop()
        QTimer.singleShot(2000, lambda: start_map(window))
    else:
        start_map(window)
        if hasattr(window, 'th') and window.th:
            window.th.success.connect(lambda: auto_copy_link(window))

def start_map(window):
    """启动frpc映射的核心逻辑"""
    with QMutexLocker(window.app_mutex):
        if window.is_closing:
            return

        if window.th and window.th.isRunning():
            log_message(window, "正在关闭旧进程...", "orange")
            window.th.stop()
            wait_for_thread(window.th)
            log_message(window, "已终止旧进程", "green")

        if not validate_port(window):
            return

        server_name, host, port, token = get_server_details(window)
        remote_port = gen_port()
        
        if not window.config_manager.create_config(host, port, token, window.mapping_tab.port_edit.text().strip(), remote_port, random.randint(10000, 99999)):
            QMessageBox.warning(window, "错误", "无法写入配置文件，请检查权限")
            return

        window.link = f"{host}:{remote_port}"
        start_frpc_thread(window)
        log_message(window, f"开始映射本地端口 {window.mapping_tab.port_edit.text().strip()} 到 {window.link}", "blue")

def start_frpc_thread(window):
    """初始化并启动FrpcThread"""
    window.th = FrpcThread("config/frpc.ini")
    window.th.out.connect(window.mapping_tab.log_text.append)
    window.th.warn.connect(lambda m: log_message(window, m, "red"))
    window.th.success.connect(lambda: on_mapping_success(window))
    window.th.error.connect(lambda m: on_mapping_error(window, m))
    window.th.terminated.connect(window.onFrpcTerminated)
    window.th.start()

def validate_port(window):
    """验证端口输入的有效性"""
    local_port = window.mapping_tab.port_edit.text().strip()
    if not local_port.isdigit() or not 1 <= int(local_port) <= 65535:
        QMessageBox.warning(window, "错误", "请输入有效端口 (1-65535)")
        return False
    return True

def get_server_details(window):
    """从UI获取服务器选择信息"""
    server_text = window.mapping_tab.server_combo.currentText()
    server_name = server_text.split()[0]
    host, port, token = window.SERVERS[server_name]
    return server_name, host, port, token

def on_mapping_success(window):
    """映射成功时的UI更新"""
    window.mapping_tab.link_label.setText(f"映射地址: {window.link}")
    window.mapping_tab.link_label.setStyleSheet("color: green; font-weight: bold; font-size: 16px;")
    window.mapping_tab.copy_button.setEnabled(True)
    log_message(window, "映射成功！", "green")

def on_mapping_error(window, message):
    """映射失败时的UI更新"""
    log_message(window, f"⚠️ {message}", "red")
    QMessageBox.warning(window, "错误", message)
    log_message(window, "映射失败", "red")

def copy_link(window):
    """复制映射链接到剪贴板"""
    QApplication.clipboard().setText(window.link)
    log_message(window, "游戏链接地址已复制到剪贴板", "red")
    QTimer.singleShot(3000, window.update_ad)

def auto_copy_link(window):
    """自动复制链接（用于自动映射模式）"""
    if window.auto_mapping_enabled and window.link:
        QApplication.clipboard().setText(window.link)
        log_message(window, "自动映射: 映射地址已自动复制到剪贴板", "green")

def log_message(window, message, color=None):
    """向日志文本框输出带颜色的信息"""
    cursor = window.mapping_tab.log_text.textCursor()
    cursor.movePosition(QTextCursor.End)
    window.mapping_tab.log_text.setTextCursor(cursor)

    if color == "blue" and window.theme == "dark":
        color = "cyan"

    if color:
        window.mapping_tab.log_text.insertHtml(f"<span style='color:{color};'>{message}</span><br>")
    else:
        window.mapping_tab.log_text.append(message)

    cursor.movePosition(QTextCursor.End)
    window.mapping_tab.log_text.setTextCursor(cursor)

def on_auto_mapping_changed(window, state):
    """自动映射选项变更处理"""
    window.auto_mapping_enabled = bool(state)
    window.app_config["settings"]["auto_mapping"] = window.auto_mapping_enabled
    window.yaml_config.save_config("app_config.yaml", window.app_config)
    
    log_message(window, "已启用自动映射模式" if window.auto_mapping_enabled else "已关闭自动映射模式", "green" if window.auto_mapping_enabled else "orange")

def on_dark_mode_changed(window, state):
    """夜间模式选项变更处理"""
    window.dark_mode_override = True
    window.force_dark_mode = bool(state)
    
    settings = window.app_config["settings"]
    settings["dark_mode_override"] = window.dark_mode_override
    settings["force_dark_mode"] = window.force_dark_mode
    window.yaml_config.save_config("app_config.yaml", window.app_config)
    
    window.theme = 'dark' if window.force_dark_mode else 'light'
    window.setStyleSheet(STYLE[window.theme])
    
    mode_text = "夜间模式" if window.force_dark_mode else "昼间模式"
    log_message(window, f"已切换到{mode_text}，暂停自动昼夜切换", "blue")
