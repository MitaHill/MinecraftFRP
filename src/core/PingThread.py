import time, threading
from PySide6.QtCore import QThread, Signal
from src.core.PingService import PingService
from src.utils.LogManager import get_logger

logger = get_logger()

class PingThread(QThread):
    """
    GUI 线程适配器：在后台线程运行 PingService，并将结果发送给 UI。
    """
    ping_results = Signal(dict)
    _last_log_times = []  # 类级别：记录最近4次日志时间戳
    _log_lock = threading.Lock()  # 线程安全锁

    def __init__(self, servers):
        super().__init__()
        self.servers = servers

    def run(self):
        service = PingService(max_workers=20) # 使用较多的线程以加快 I/O 密集型任务
        results = {}
        
        # 此时 ping_servers 是并发执行的，但我们在这里同步等待所有结果完成
        # (或者每完成一个就更新 results 字典，最后统一发送)
        for name, delay in service.ping_servers(self.servers):
            if delay is not None:
                item_text = f"{name}    {delay}ms"
            else:
                item_text = f"{name}    timeout"
            results[name] = item_text
            
        self.ping_results.emit(results)
        # 限流日志：50秒内只允许4条相同消息（线程安全）
        now = time.time()
        with PingThread._log_lock:
            PingThread._last_log_times = [t for t in PingThread._last_log_times if now - t < 50]
            should_log = len(PingThread._last_log_times) < 4
            if should_log:
                PingThread._last_log_times.append(now)
        
        if should_log:
            logger.info("Ping 测速完成，已发送结果信号")
