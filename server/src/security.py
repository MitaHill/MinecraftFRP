import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict, deque
from .utils import get_effective_ip, is_ip_matched
from .database import (is_ip_banned, ban_ip, get_whitelist_rules, 
                       get_blacklist_rules, log_access)
from .logger import logger

# Simple in-memory cache for rules
_rules_cache = {
    'whitelist': [],
    'blacklist': [],
    'last_update': 0
}

def _refresh_rules_cache():
    """Refresh rules from DB every 60 seconds"""
    now = time.time()
    if now - _rules_cache['last_update'] > 60:
        try:
            # Only extract the rule string for matching
            _rules_cache['whitelist'] = [r['rule'] for r in get_whitelist_rules()]
            _rules_cache['blacklist'] = [r['rule'] for r in get_blacklist_rules()]
            _rules_cache['last_update'] = now
        except Exception as e:
            logger.error(f"Failed to refresh rules cache: {e}")

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
        
        # 0. 记录访问日志 (Fire and forget, potentially slow if sync, but DB is SQLite WAL usually fast enough for low traffic)
        # For high performance, this should be async or sampled. 
        # But for this lobby server, it's likely fine.
        # Check if it's an admin API call to avoid logging too much internal traffic? 
        # No, log everything for security audit.
        try:
            log_access(client_ip, f"{request.method} {request.url.path}")
        except:
            pass

        # Refresh cache if needed
        _refresh_rules_cache()

        # 2. 检查白名单 (Highest Priority)
        if is_ip_matched(client_ip, _rules_cache['whitelist']):
            # Whitelisted IP bypasses all bans and rate limits
            return await call_next(request)

        # 3. 检查黑名单规则 (Admin Bans)
        if is_ip_matched(client_ip, _rules_cache['blacklist']):
            logger.warning(f"Blocked blacklisted IP (Admin Rule): {client_ip}")
            return Response("Access Denied: You are blacklisted by administrator.", status_code=403)

        # 4. 检查自动封禁 (Auto-Ban)
        if is_ip_banned(client_ip):
            logger.warning(f"Blocked banned IP (Auto-Ban): {client_ip}")
            return Response("Your IP is temporarily banned due to excessive requests.", status_code=403)
            
        # 5. TODO: CN IP Check
        # if not is_cn_ip(client_ip):
        #     return Response("Access Denied: Region not allowed.", status_code=403)

        # 6. 内存流速限制 (Sliding Window)
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
        
        # 7. 放行
        response = await call_next(request)
        return response
