from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Header, Depends
from contextlib import asynccontextmanager
import asyncio
from typing import List, Optional
from datetime import datetime
from .models import RoomCreate, RoomDelete, RuleCreate, RuleDelete, ViolationReport, TunnelInfo
from .database import (init_db, upsert_room, delete_room, get_rooms, cleanup_stale_rooms, 
                       check_ip_conflict, update_room_status, update_online_heartbeat, 
                       get_online_count, cleanup_offline_users,
                       add_blacklist_rule, remove_blacklist_rule, get_blacklist_rules,
                       add_whitelist_rule, remove_whitelist_rule, get_whitelist_rules,
                       get_access_logs, upsert_tunnel, cleanup_stale_tunnels, get_active_tunnels,
                       get_online_users_list)
from .utils import get_effective_ip, mask_ip
from .logger import logger
from .security import RateLimitMiddleware
from .moderation import moderator
from .minecraft_pinger import get_server_motd, get_server_status

ADMIN_KEY = "mcf-admin-8888"

async def verify_admin(x_admin_key: str = Header(None)):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid Admin Key")

# 后台清理任务
async def cleanup_task():
    while True:
        try:
            # 每60秒清理一次超时10秒的房间（与 database 默认值一致）
            deleted_rooms = cleanup_stale_rooms(timeout_seconds=10)
            if deleted_rooms > 0:
                logger.info(f"Cleaned up {deleted_rooms} stale rooms")
            
            # 清理超时的在线用户（15秒超时）
            offline = cleanup_offline_users(timeout_seconds=15)
            if offline > 0:
                logger.info(f"Cleaned up {offline} offline users")
                
            # 清理超时的隧道（40秒超时）
            deleted_tunnels = cleanup_stale_tunnels(timeout_seconds=40)
            if deleted_tunnels > 0:
                logger.info(f"Cleaned up {deleted_tunnels} stale tunnels")
                
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        await asyncio.sleep(60)

# 版本探测任务
async def version_detection_task():
    """后台任务：定期探测所有房间的真实版本和MOTD，并更新数据库"""
    while True:
        try:
            rooms = get_rooms(limit=500)
            for room in rooms:
                try:
                    # 获取服务器真实状态
                    status = await get_server_status(room.server_addr, room.remote_port)

                    if status:
                        version = status.get("version", "")
                        description = status.get("description", "")

                        # 更新数据库中的版本和MOTD
                        update_room_status(room.full_room_code, version, description)

                        # 同时检查MOTD敏感词
                        bad_word = moderator.check_text(description)
                        if bad_word:
                            logger.warning(f"VERSION_DETECT VIOLATION: Room {room.full_room_code} MOTD contains '{bad_word}'. Deleting.")
                            delete_room(room.remote_port, room.node_id)

                except Exception as e:
                    # 单个房间探测失败不影响其他房间
                    pass

                # 避免过快请求，每个房间间隔0.5秒
                await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"Version detection task error: {e}")

        # 每30秒执行一轮扫描
        await asyncio.sleep(30)

async def audit_room_task(host: str, port: int, full_room_code: str, remote_port: int, node_id: int):
    """后台任务：审核房间 MOTD"""
    try:
        # 1. 探测 MOTD
        # 注意：这里我们使用服务端视角去 ping 房间的 server_addr
        # 如果 server_addr 是 FRP 的公网入口，这通常是可行的
        motd = await get_server_motd(host, port)
        
        if not motd:
            return

        # 2. 敏感词匹配
        bad_word = moderator.check_text(motd)
        if bad_word:
            logger.warning(f"AUDIT VIOLATION: Room {full_room_code} has bad word '{bad_word}' in MOTD. Deleting.")
            # 3. 违规删除
            delete_room(remote_port, node_id)
            
    except Exception as e:
        logger.error(f"Audit task failed for {full_room_code}: {e}")

async def robust_get_server_status(host: str, port: int, retries: int = 3) -> Optional[dict]:
    """
    Robust server status check with progressive timeout strategy.
    Tries 3 times with increasing timeouts (2s, 3s, 5s) to handle network congestion
    while avoiding overly long blocking.
    """
    timeouts = [2.0, 3.0, 5.0]
    
    for i, timeout in enumerate(timeouts):
        status = await get_server_status(host, port, timeout=timeout)
        if status:
            return status
            
        # Exponential backoff for retry interval: 0.5s, 1.0s, etc.
        if i < len(timeouts) - 1:
            sleep_time = 0.5 * (2 ** i)
            await asyncio.sleep(sleep_time)
            
    return None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    init_db()
    logger.info("Database initialized (data.db)")
    
    # 加载敏感词规则
    moderator.load_rules()
    
    # 启动后台清理任务
    cleanup = asyncio.create_task(cleanup_task())
    logger.info("Background cleanup task started")
    
    # 启动版本探测任务
    version_detect = asyncio.create_task(version_detection_task())
    logger.info("Version detection task started")

    yield
    
    # 关闭时取消任务
    cleanup.cancel()
    version_detect.cancel()
    logger.info("Server shutting down...")

app = FastAPI(lifespan=lifespan)

# 注册限流中间件：每IP每分钟限制60次请求
app.add_middleware(RateLimitMiddleware, limit=60, window=60)

@app.post("/api/tunnel/validate")
async def validate_tunnel(tunnel: TunnelInfo, request: Request):
    """
    Validate a generic tunnel (mapping).
    Client sends heartbeat here. Server performs robust check.
    If check fails multiple times (handled by robust_get_server_status), 
    commands client to stop.
    """
    client_ip = get_effective_ip(request)
    
    # Perform robust check (5 retries)
    status = await robust_get_server_status(tunnel.server_addr, tunnel.remote_port)
    
    if not status:
        logger.warning(f"Tunnel validation failed for {client_ip} -> {tunnel.server_addr}:{tunnel.remote_port}")
        return {
            "success": False, 
            "command": "stop", 
            "reason": "Server validation failed (unstable connection or invalid server)"
        }
    
    # Validation passed: Update tunnel heartbeat
    try:
        upsert_tunnel(client_ip, tunnel.server_addr, tunnel.remote_port)
    except Exception as e:
        logger.error(f"Failed to upsert tunnel: {e}")

    return {
        "success": True, 
        "command": "keep-alive"
    }

@app.post("/api/lobby/rooms")
async def create_or_update_room(room: RoomCreate, request: Request, background_tasks: BackgroundTasks):
    """创建或更新房间信息 (心跳)"""
    client_ip = get_effective_ip(request)
    
    # 简单的合规性检查
    if len(room.room_name) > 50 or len(room.description) > 200:
        logger.warning(f"Validation failed for IP {client_ip}: Text too long")
        raise HTTPException(status_code=422, detail="Text too long")
        
    # 防多开检查
    if check_ip_conflict(client_ip, room.full_room_code):
        logger.warning(f"Blocked multi-instance attempt from {client_ip}")
        return {"success": False, "message": "禁止多开，此IP已被占用"}
    
    # 敏感词审查 (MOTD & 房间名) - 静态检查
    bad_word = moderator.check_text(room.room_name)
    if bad_word:
        logger.warning(f"Blocked sensitive content from {client_ip}: '{bad_word}' in name")
        return {"success": False, "message": f"房间名包含敏感词: {bad_word}"}
        
    bad_word = moderator.check_text(room.description)
    if bad_word:
        logger.warning(f"Blocked sensitive content from {client_ip}: '{bad_word}' in description")
        return {"success": False, "message": f"简介包含敏感词: {bad_word}"}

    # Minecraft 服务器可访问性验证 (Robust Check)
    status = await robust_get_server_status(room.server_addr, room.remote_port)
    if not status:
        logger.warning(f"Validation failed for {room.server_addr}:{room.remote_port}. Not a valid Minecraft server.")
        return {"success": False, "message": "Validation failed"}

    try:
        upsert_room(room, client_ip)
        
        # 触发后台动态审核 (MOTD)
        # 只有当房间是公开的时才需要审核
        if room.is_public:
            background_tasks.add_task(
                audit_room_task, 
                room.server_addr, 
                room.remote_port, 
                room.full_room_code,
                room.remote_port, # 这里的参数传递有点冗余，audit_task 需要 remote_port 用于 delete
                room.node_id
            )

        return {"success": True, "message": "Room updated"}
    except Exception as e:
        logger.error(f"Error updating room from {client_ip}: {e}")
        return {"success": False, "message": str(e)}

@app.delete("/api/lobby/rooms")
async def remove_room(room: RoomDelete):
    """移除房间"""
    try:
        delete_room(room.remote_port, room.node_id)
        logger.info(f"Room removed: {room.remote_port}_{room.node_id}")
        return {"success": True, "message": "Room removed"}
    except Exception as e:
        logger.error(f"Error removing room: {e}")
        return {"success": False, "message": str(e)}

@app.get("/api/lobby/rooms")
async def list_rooms():
    """获取房间列表，返回脱敏的房主IP"""
    rooms = get_rooms()
    # 将房间列表转为字典并脱敏IP
    rooms_data = []
    for room in rooms:
        room_dict = {
            "full_room_code": room.full_room_code,
            "remote_port": room.remote_port,
            "node_id": room.node_id,
            "room_name": room.room_name,
            "game_version": room.game_version,
            "player_count": room.player_count,
            "max_players": room.max_players,
            "description": room.description,
            "is_public": room.is_public,
            "host_player": room.host_player,
            "server_addr": room.server_addr,
            "host_ip": mask_ip(room.client_ip),  # 脱敏后的房主IP
            "updated_at": room.updated_at
        }
        rooms_data.append(room_dict)
    return {"success": True, "rooms": rooms_data}

@app.post("/api/lobby/heartbeat")
async def user_heartbeat(request: Request):
    """用户在线心跳，用于统计在线人数"""
    client_ip = get_effective_ip(request)
    try:
        update_online_heartbeat(client_ip)
        return {"success": True}
    except Exception as e:
        logger.error(f"Heartbeat error from {client_ip}: {e}")
        return {"success": False}

@app.get("/api/lobby/online")
async def get_online():
    """获取当前在线用户数量"""
    try:
        count = get_online_count(timeout_seconds=15)
        return {"success": True, "online_count": count}
    except Exception as e:
        logger.error(f"Get online count error: {e}")
        return {"success": False, "online_count": 0}

@app.get("/")
async def root():
    return {"message": "MinecraftFRP Lobby Server is running"}

# --- Admin APIs ---

@app.get("/api/admin/access_logs", dependencies=[Depends(verify_admin)])
async def api_get_access_logs():
    return {"success": True, "logs": get_access_logs()}

@app.get("/api/admin/online_users", dependencies=[Depends(verify_admin)])
async def api_get_online_users():
    """获取所有活跃隧道（在线用户）信息"""
    return {"success": True, "users": get_active_tunnels()}

@app.get("/api/admin/online_app_users", dependencies=[Depends(verify_admin)])
async def api_get_online_app_users():
    """获取所有软件在线用户（大厅心跳）"""
    return {"success": True, "users": get_online_users_list()}

@app.get("/api/admin/blacklist", dependencies=[Depends(verify_admin)])
async def api_get_blacklist():
    return {"success": True, "rules": get_blacklist_rules()}

@app.post("/api/admin/blacklist", dependencies=[Depends(verify_admin)])
async def api_add_blacklist(rule: RuleCreate):
    try:
        add_blacklist_rule(rule.rule, rule.reason)
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.delete("/api/admin/blacklist", dependencies=[Depends(verify_admin)])
async def api_remove_blacklist(rule: RuleDelete):
    remove_blacklist_rule(rule.rule)
    return {"success": True}

@app.get("/api/admin/whitelist", dependencies=[Depends(verify_admin)])
async def api_get_whitelist():
    return {"success": True, "rules": get_whitelist_rules()}

@app.post("/api/admin/whitelist", dependencies=[Depends(verify_admin)])
async def api_add_whitelist(rule: RuleCreate):
    try:
        add_whitelist_rule(rule.rule, rule.reason, rule.duration_minutes)
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.delete("/api/admin/whitelist", dependencies=[Depends(verify_admin)])
async def api_remove_whitelist(rule: RuleDelete):
    remove_whitelist_rule(rule.rule)
    return {"success": True}

# --- Client APIs ---

@app.get("/api/check_access")
async def check_access(request: Request):
    """Client startup check. Logic is handled by Middleware.
    If we reach here, it means we passed the Middleware checks (Whitelist/Blacklist/Geo)."""
    return {"success": True, "message": "Access Granted"}

@app.post("/api/report_violation")
async def report_violation(report: ViolationReport, request: Request):
    client_ip = get_effective_ip(request)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    reason = f"封禁于{now_str} {client_ip} 因为是非家庭宽带 (自动上报)"
    
    logger.warning(f"Self-reported violation from {client_ip}: {reason}")
    # Add to blacklist rules
    add_blacklist_rule(client_ip, reason)
    return {"success": True}
