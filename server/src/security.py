import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict, deque
from .utils import get_effective_ip
from .database import is_ip_banned, ban_ip
from .logger import logger

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int = 60, window: int = 60):
        """
        :param limit: 时间窗口内的最大请求数 (默认 60)
        :param window: 时间窗口大小（秒） (默认 60秒)
        """
        super().__init__(app)
        self.limit = limit
        self.window = window
        # 使用 deque 存储请求时间戳，键为 IP
        self.request_history = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        # 1. 获取真实 IP
        client_ip = get_effective_ip(request)
        
        # 2. 检查数据库黑名单 (持久化)
        if is_ip_banned(client_ip):
            logger.warning(f"Blocked banned IP: {client_ip}")
            return Response("Your IP is banned due to excessive requests.", status_code=403)

        # 3. 内存流速限制 (Sliding Window)
        now = time.time()
        history = self.request_history[client_ip]
        
        # 移除窗口外的时间戳
        while history and history[0] < now - self.window:
            history.popleft()
            
        # 检查是否超限
        if len(history) >= self.limit:
            # 触发封禁：写入数据库，封禁10分钟
            logger.warning(f"IP {client_ip} exceeded rate limit ({self.limit}/{self.window}s). Banning for 10 min.")
            ban_ip(client_ip, duration_minutes=10)
            
            # 清理内存（既然已被持久化封禁，内存中无需再保留历史）
            del self.request_history[client_ip]
            
            return Response("Rate limit exceeded. You are banned for 10 minutes.", status_code=403)
        
        # 记录本次请求
        history.append(now)
        
        # 4. 放行
        response = await call_next(request)
        return response
