import random
import getpass
from PySide6.QtCore import QTimer, QMutexLocker
from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtGui import QTextCursor

from src.core.FrpcThread import FrpcThread
from src.core.ConfigManager import ConfigManager
from src.utils.PortGenerator import gen_port
from src.gui.main_window.Threads import wait_for_thread
from src.gui.styles import STYLE
from src.network.WebGuard import WebGuard
from heartbeat_manager import HeartbeatManager

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
        
        # 判断是否为特殊节点（名称包含“特殊节点”）
        is_special = "特殊节点" in server_name
        if is_special:
            # 使用 TOML 与 new-frpc.exe
            cfg = ConfigManager("frpc.toml")
            ok = cfg.create_config(host, port, "", window.mapping_tab.port_edit.text().strip(), remote_port, random.randint(10000, 99999))
            config_path = str(cfg.filename)
            window.current_server_is_special = True
            window._current_cfg_manager = cfg
        else:
            ok = window.config_manager.create_config(host, port, token, window.mapping_tab.port_edit.text().strip(), remote_port, random.randint(10000, 99999))
            config_path = str(window.config_manager.filename)
            window.current_server_is_special = False
            window._current_cfg_manager = window.config_manager
        
        if not ok:
            QMessageBox.warning(window, "错误", "无法写入配置文件，请检查权限")
            return

        # 保存上下文供心跳使用
        window._current_mapping = {
            "server_name": server_name,
            "host": host,
            "remote_port": remote_port
        }

        window.link = f"{host}:{remote_port}"
        start_frpc_thread(window, config_path)
        log_message(window, f"开始映射本地端口 {window.mapping_tab.port_edit.text().strip()} 到 {window.link}", "blue")

        # 启动WebGuard周期检测，防止用户建站
        try:
            window.web_guard = WebGuard(
                port_getter=lambda: int(window.mapping_tab.port_edit.text().strip() or '0'),
                stop_callback=lambda msg: _stop_mapping_due_to_web(window, msg),
                interval_sec=30,
            )
            window.web_guard.start()
        except Exception:
            pass

def start_frpc_thread(window, config_path: str):
    """初始化并启动FrpcThread"""
    window.th = FrpcThread(config_path)
    window.th.out.connect(window.mapping_tab.log_text.append)
    window.th.warn.connect(lambda m: log_message(window, m, "red"))
    window.th.success.connect(lambda: on_mapping_success(window))
    window.th.error.connect(lambda m: on_mapping_error(window, m))
    window.th.terminated.connect(window.onFrpcTerminated)
    window.th.start()
    # 安全策略：在启动后1秒尝试删除当前使用的配置文件（仅在非特殊情况下执行，特殊节点需保留更久）
    try:
        from PySide6.QtCore import QTimer
        import os
        def _safe_delete():
            try:
                # 特殊节点下保留文件，避免“找不到配置文件”问题
                if not getattr(window, 'current_server_is_special', False) and os.path.exists(config_path):
                    try:
                        os.chmod(config_path, 0o600)
                    except Exception:
                        pass
                    os.remove(config_path)
            except Exception:
                pass
        QTimer.singleShot(1000, _safe_delete)
    except Exception:
        pass

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
    
    # 自动复制到剪贴板
    QApplication.clipboard().setText(window.link)
    log_message(window, "映射地址已自动复制到剪贴板", "green")

    # 若为特殊节点，启动房间心跳
    try:
        if getattr(window, "current_server_is_special", False) and hasattr(window, "_current_mapping"):
            # 特殊节点名到 node_id 的映射（单字母节点：A=5, B=6, C=7...）
            special_node_ids = {chr(65 + i): 5 + i for i in range(26)}  # A-Z 映射到 5-30
            server_name = window._current_mapping.get("server_name")
            node_id = special_node_ids.get(server_name)
            if node_id:
                if not hasattr(window, "heartbeat_manager"):
                    window.heartbeat_manager = HeartbeatManager(
                        "https://lytapi.asia/api.php",
                        lambda msg, c=None: log_message(window, msg, c),
                        lambda: bool(window.th and window.th.manager.is_running())
                    )
                room_info = {
                    "full_room_code": f"{window._current_mapping['remote_port']}_{node_id}",
                    "room_name": f"{server_name}的房间",
                    "game_version": "未知版本",
                    "player_count": 1,
                    "max_players": 20,
                    "description": f"通过{server_name}连接",
                    "is_public": True,
                    "host_player": getpass.getuser() or "玩家",
                    "server_addr": window._current_mapping["host"],
                }
                window.heartbeat_manager.submit_room_info(room_info, start_heartbeat=True)
                log_message(window, "已启动联机大厅心跳", "blue")
    except Exception as e:
        log_message(window, f"启动心跳失败: {e}", "orange")

from PySide6.QtCore import QTimer

def _stop_mapping_due_to_web(window, message):
    # 停止周期 WebGuard，避免重复触发
    try:
        if hasattr(window, "web_guard"):
            window.web_guard.stop()
    except Exception:
        pass
    # 异步停止映射线程，避免阻塞事件循环
    try:
        if window.th and window.th.isRunning():
            QTimer.singleShot(0, window.th.stop)
    except Exception:
        pass
    # 立即提示用户，但不阻塞线程终止
    log_message(window, message, "red")
    try:
        QMessageBox.warning(window, "安全策略", message)
    except Exception:
        pass


def on_mapping_error(window, message):
    """映射失败时的UI更新"""
    log_message(window, f"⚠️ {message}", "red")
    QMessageBox.warning(window, "错误", message)
    log_message(window, "映射失败", "red")

def copy_link(window):
    """复制映射链接到剪贴板"""
    QApplication.clipboard().setText(window.link)
    log_message(window, "游戏链接地址已复制到剪贴板", "green")
    QTimer.singleShot(3000, window.update_ad)

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

def on_server_changed(window, text):
    """线路选择变更处理，保存记忆"""
    if not text:
        return
    # text 格式可能是 "ServerName 50ms" 或 "ServerName"
    server_name = text.split()[0]
    
    window.app_config["settings"]["last_server"] = server_name
    window.yaml_config.save_config("app_config.yaml", window.app_config)
