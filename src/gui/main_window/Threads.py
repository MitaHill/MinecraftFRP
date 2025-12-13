from PySide6.QtCore import QMutexLocker, QEventLoop, QTimer

from src.core.PingThread import PingThread
from src.network.MinecraftLan import MinecraftLANPoller
from src.network.PingUtils import save_ping_data
from src.core.ServerUpdateThread import ServerUpdateThread
from src.utils.LogManager import get_logger

logger = get_logger()

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
    # 优先读取缓存，立即填充界面
    from src.network.PingUtils import load_ping_data
    cached = load_ping_data()
    if cached:
        update_server_combo(window, cached)
    
    # 防止重入：如果Ping还在进行中，跳过本次
    if window.ping_thread and window.ping_thread.isRunning():
        return

    # 后台异步刷新真实延迟
    window.ping_thread = PingThread(window.SERVERS)
    window.ping_thread.ping_results.connect(window.update_server_combo)
    # 自动清理
    window.ping_thread.finished.connect(window.ping_thread.deleteLater)
    window.ping_thread.start()

def start_server_list_update(window):
    """启动后台线程，从网络更新服务器列表"""
    if window.server_update_thread and window.server_update_thread.isRunning():
        return

    window.server_update_thread = ServerUpdateThread()
    window.server_update_thread.servers_updated.connect(window.on_servers_updated)
    window.server_update_thread.finished.connect(window.server_update_thread.deleteLater)
    window.server_update_thread.start()

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
    if not thread:
        return
        
    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    
    # 使用标准的 finished 信号，兼容所有 QThread
    thread.finished.connect(loop.quit)
    # 兼容自定义的 terminated 信号 (如果有)
    if hasattr(thread, 'terminated'):
        thread.terminated.connect(loop.quit)
        
    timer.start(THREAD_TIMEOUT)
    loop.exec()

    if timer.isActive():
        timer.stop()
    else:
        logger.warning(f"{type(thread).__name__} 线程超时未响应，强制继续")
