from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager
import asyncio
from .models import RoomCreate, RoomDelete
from .database import init_db, upsert_room, delete_room, get_rooms, cleanup_stale_rooms, check_ip_conflict
from .utils import get_effective_ip
from .logger import logger
from .security import RateLimitMiddleware
from .moderation import moderator
from .minecraft_pinger import get_server_motd

# 后台清理任务
async def cleanup_task():
    while True:
        try:
            # 每60秒清理一次超时10秒的房间（与 database 默认值一致）
            deleted = cleanup_stale_rooms(timeout_seconds=10)
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} stale rooms")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        await asyncio.sleep(60)

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    init_db()
    logger.info("Database initialized (data.db)")
    
    # 加载敏感词规则
    moderator.load_rules()
    
    # 启动后台清理任务
    task = asyncio.create_task(cleanup_task())
    logger.info("Background cleanup task started")
    
    yield
    
    # 关闭时取消任务
    task.cancel()
    logger.info("Server shutting down...")

app = FastAPI(lifespan=lifespan)

# 注册限流中间件：每IP每分钟限制60次请求
app.add_middleware(RateLimitMiddleware, limit=60, window=60)

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
    """获取房间列表"""
    return {"success": True, "rooms": get_rooms()}

@app.get("/")
async def root():
    return {"message": "MinecraftFRP Lobby Server is running"}
