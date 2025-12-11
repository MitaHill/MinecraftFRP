import asyncio
from typing import Optional, Dict
from mcstatus import JavaServer
from .logger import logger

async def get_server_motd(host: str, port: int) -> Optional[str]:
    """
    异步获取 Minecraft Java 版服务器的 MOTD。
    如果连接失败或超时，返回 None。
    """
    status = await get_server_status(host, port)
    if status:
        return status.get("description")
    return None

async def get_server_status(host: str, port: int, timeout: float = 3.0) -> Optional[dict]:
    """
    异步获取 Minecraft 服务器状态 (Version, MOTD, Players)
    """
    try:
        # 在 Executor 中运行同步的 mcstatus 代码
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _get_status_sync, host, port, timeout)
    except Exception as e:
        # logger.debug(f"Ping failed for {host}:{port}: {e}")
        return None

def _get_status_sync(host: str, port: int, timeout: float) -> Optional[dict]:
    try:
        server = JavaServer(host, port, timeout=timeout)
        status = server.status()
        
        # 解析 MOTD (可能是 str, dict 或 list)
        description = status.description
        if isinstance(description, dict):
            description = description.get('text', '')
        elif isinstance(description, list):
            description = "".join([d.get('text', '') for d in description if isinstance(d, dict)])
        
        return {
            "version": status.version.name,
            "description": str(description),
            "players_online": status.players.online,
            "players_max": status.players.max,
            "latency": status.latency
        }
    except Exception:
        return None
