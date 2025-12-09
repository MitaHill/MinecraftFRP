import time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Tuple, Generator, Optional
from src.network.PingUtils import ping_host
from src.utils.LogManager import get_logger

logger = get_logger()

class PingService:
    """
    负责执行 Ping 测速的核心服务类。
    纯 Python 实现，无 GUI 依赖。
    """
    _last_log_times = []  # 类级别：记录最近4次日志时间戳
    _log_lock = threading.Lock()  # 线程安全锁

    def __init__(self, max_workers: int = 10):
        """
        初始化 PingService。
        
        Args:
            max_workers: 并发线程数，默认为 10。
        """
        self.max_workers = max_workers

    def ping_servers(self, servers: Dict[str, Tuple[str, int, str]]) -> Generator[Tuple[str, Optional[int]], None, None]:
        """
        并发 Ping 所有服务器，并以生成器的形式逐个返回结果。
        
        Args:
            servers: 服务器字典 {name: (host, port, token)}
            
        Yields:
            (server_name, delay_ms) 元组。delay_ms 为 None 表示超时/失败。
        """
        # 限流日志：50秒内只允许4条相同消息（线程安全）
        now = time.time()
        with PingService._log_lock:
            PingService._last_log_times = [t for t in PingService._last_log_times if now - t < 50]
            should_log = len(PingService._last_log_times) < 4
            if should_log:
                PingService._last_log_times.append(now)
        
        if should_log:
            logger.info(f"开始并发 Ping {len(servers)} 个服务器 (线程数: {self.max_workers})")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            # future_to_name: {Future: server_name}
            future_to_name = {
                executor.submit(self._ping_single, name, info[0]): name 
                for name, info in servers.items()
            }

            # 逐个获取完成的结果 (as_completed 是乱序的，谁先完给谁)
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    delay = future.result()
                    yield name, delay
                except Exception as e:
                    logger.error(f"Ping 服务器 {name} 时发生未捕获异常: {e}")
                    yield name, None

    def _ping_single(self, name: str, host: str) -> Optional[int]:
        """单个 Ping 任务包装器"""
        # 这里可以添加重试逻辑等
        return ping_host(host)
