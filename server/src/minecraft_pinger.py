import asyncio
from typing import Optional, Dict
from mcstatus import JavaServer
from .logger import logger

async def get_server_status(host: str, port: int) -> Optional[Dict[str, str]]:
    """
    异步获取 Minecraft Java 版服务器的状态（MOTD 和 版本）。
    如果连接失败或超时，返回 None。
    """
    try:
        # 即使是反代地址，如果服务端在同一内网或公网可达，通常可以直接连接
        server = JavaServer(host, port)
        
        # 异步 ping
        status = await server.async_status()
        
        # 1. 获取 MOTD
        motd = status.description
        if hasattr(motd, "to_plain"):
            motd_text = motd.to_plain()
        else:
            motd_text = str(motd)
            
        # 2. 获取版本
        version_text = status.version.name
        
        return {
            "description": motd_text,
            "version": version_text
        }
        
    except Exception as e:
        # logger.debug(f"Failed to ping MC server {host}:{port} - {e}")
        return None
