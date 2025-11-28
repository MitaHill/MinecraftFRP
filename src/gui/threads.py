from PySide6.QtCore import QMutexLocker, QEventLoop, QTimer

from src.core.ping_thread import PingThread
from src.network.minecraft_lan import MinecraftLANPoller
from src.network.ping_utils import save_ping_data

THREAD_TIMEOUT = 3000

def start_lan_poller(window):
    """启动局域网Minecraft端口轮询线程"""
    with QMutexLocker(window.app_mutex):
        if window.lan_poller is None:
            window.lan_poller = MinecraftLANPoller()
            window.lan_poller.port_found.connect(window.set_port)
            window.lan_poller.terminated.connect(window.onLANPollerTerminated)
            window.lan_poller.start()

def stop_lan_poller(window, wait=True):
    """停止局域网轮询线程"""
    with QMutexLocker(window.app_mutex):
        if window.lan_poller and window.lan_poller.isRunning():
            window.lan_poller.stop()
            if wait:
                wait_for_thread(window.lan_poller)

def load_ping_values(window):
    """加载并更新服务器延迟"""
    window.ping_thread = PingThread(window.SERVERS)
    window.ping_thread.ping_results.connect(window.update_server_combo)
    window.ping_thread.start()

def update_server_combo(window, results):
    """使用ping结果更新服务器下拉列表"""
    if results is None:
        results = {}
    for i, name in enumerate(window.SERVERS.keys()):
        text = results.get(name, f"{name}    timeout")
        window.mapping_tab.server_combo.setItemText(i, text)
    save_ping_data(results)

def wait_for_thread(thread):
    """等待线程优雅退出，带超时"""
    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    thread.terminated.connect(loop.quit)
    timer.start(THREAD_TIMEOUT)
    loop.exec()

    if timer.isActive():
        timer.stop()
    else:
        print(f"{type(thread).__name__} 线程超时未响应，强制继续")
