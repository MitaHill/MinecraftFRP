from fastapi import Request

def get_effective_ip(request: Request) -> str:
    """
    获取客户端真实IP，兼容 Nginx 反代 (X-Forwarded-For, X-Real-IP)。
    """
    # 优先检查 X-Forwarded-For
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        # 取第一个IP
        return x_forwarded_for.split(",")[0].strip()
    
    # 其次检查 X-Real-IP
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip
        
    # 最后使用直连IP
    return request.client.host or "127.0.0.1"
