import sqlite3
import time
import json
import threading
from typing import List, Optional
from .models import RoomCreate, RoomInfo
from .logger import logger

DB_PATH = "data.db"

def get_db_connection():
    """获取数据库连接，启用 WAL 模式"""
    conn = sqlite3.connect(DB_PATH)
    # 开启 WAL 模式以提升并发性能
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # 创建房间表
    c.execute('''CREATE TABLE IF NOT EXISTS rooms
                 (full_room_code TEXT PRIMARY KEY,
                  remote_port INTEGER,
                  node_id INTEGER,
                  room_name TEXT,
                  game_version TEXT,
                  player_count INTEGER,
                  max_players INTEGER,
                  description TEXT,
                  is_public INTEGER,
                  host_player TEXT,
                  server_addr TEXT,
                  updated_at REAL,
                  client_ip TEXT)''')
    # 创建索引以便快速清理
    c.execute('''CREATE INDEX IF NOT EXISTS idx_updated_at ON rooms (updated_at)''')
    
    # 创建黑名单表
    c.execute('''CREATE TABLE IF NOT EXISTS blacklist
                 (ip_address TEXT PRIMARY KEY,
                  banned_until REAL,
                  reason TEXT,
                  created_at REAL)''')
    
    # 创建在线用户心跳表
    c.execute('''CREATE TABLE IF NOT EXISTS online_users
                 (client_ip TEXT PRIMARY KEY,
                  last_heartbeat REAL)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_last_heartbeat ON online_users (last_heartbeat)''')
    
    # 创建黑名单规则表 (管理员手动添加)
    c.execute('''CREATE TABLE IF NOT EXISTS blacklist_rules
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  rule TEXT UNIQUE,
                  reason TEXT,
                  created_at REAL)''')

    # 创建白名单规则表 (管理员手动添加)
    c.execute('''CREATE TABLE IF NOT EXISTS whitelist_rules
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  rule TEXT UNIQUE,
                  description TEXT,
                  expires_at REAL,
                  created_at REAL)''')

    # 创建访问日志表 (记录所有上线过的IP)
    c.execute('''CREATE TABLE IF NOT EXISTS access_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  client_ip TEXT,
                  timestamp REAL,
                  action TEXT)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_access_logs_ip ON access_logs (client_ip)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_access_logs_ts ON access_logs (timestamp)''')

    # 创建活跃隧道表 (记录所有正在进行 Tunnel Validation 的客户端)
    c.execute('''CREATE TABLE IF NOT EXISTS active_tunnels
                 (client_ip TEXT,
                  server_addr TEXT,
                  remote_port INTEGER,
                  last_heartbeat REAL,
                  PRIMARY KEY (server_addr, remote_port))''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_tunnel_heartbeat ON active_tunnels (last_heartbeat)''')

    conn.commit()
    conn.close()

def upsert_tunnel(client_ip: str, server_addr: str, remote_port: int):
    """更新活跃隧道心跳"""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        now = time.time()
        c.execute("INSERT OR REPLACE INTO active_tunnels (client_ip, server_addr, remote_port, last_heartbeat) VALUES (?, ?, ?, ?)", 
                  (client_ip, server_addr, remote_port, now))
        conn.commit()
    finally:
        conn.close()

def cleanup_stale_tunnels(timeout_seconds: int = 40) -> int:
    """清理超时的活跃隧道 (默认40秒，客户端每15秒发一次)"""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        threshold = time.time() - timeout_seconds
        c.execute("DELETE FROM active_tunnels WHERE last_heartbeat < ?", (threshold,))
        deleted = c.rowcount
        conn.commit()
        return deleted
    finally:
        conn.close()

def get_active_tunnels() -> List[dict]:
    """获取所有活跃隧道信息"""
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM active_tunnels ORDER BY last_heartbeat DESC")
        rows = c.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def log_access(client_ip: str, action: str = "connect"):
    """记录访问日志"""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        now = time.time()
        # 简单的去重逻辑：如果该IP在最近5分钟内有相同操作，则不记录
        threshold = now - 300
        c.execute("SELECT id FROM access_logs WHERE client_ip = ? AND action = ? AND timestamp > ?", (client_ip, action, threshold))
        if not c.fetchone():
            c.execute("INSERT INTO access_logs (client_ip, timestamp, action) VALUES (?, ?, ?)", (client_ip, now, action))
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to log access: {e}")
    finally:
        conn.close()

def add_blacklist_rule(rule: str, reason: str):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        now = time.time()
        c.execute("INSERT OR REPLACE INTO blacklist_rules (rule, reason, created_at) VALUES (?, ?, ?)", (rule, reason, now))
        conn.commit()
    finally:
        conn.close()

def remove_blacklist_rule(rule: str):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM blacklist_rules WHERE rule = ?", (rule,))
        conn.commit()
    finally:
        conn.close()

def get_blacklist_rules():
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM blacklist_rules ORDER BY created_at DESC")
        return [dict(row) for row in c.fetchall()]
    finally:
        conn.close()

def add_whitelist_rule(rule: str, description: str, duration_minutes: int = 0):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        now = time.time()
        expires_at = (now + duration_minutes * 60) if duration_minutes > 0 else 0
        c.execute("INSERT OR REPLACE INTO whitelist_rules (rule, description, expires_at, created_at) VALUES (?, ?, ?, ?)", (rule, description, expires_at, now))
        conn.commit()
    finally:
        conn.close()

def remove_whitelist_rule(rule: str):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM whitelist_rules WHERE rule = ?", (rule,))
        conn.commit()
    finally:
        conn.close()

def get_whitelist_rules():
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM whitelist_rules ORDER BY created_at DESC")
        return [dict(row) for row in c.fetchall()]
    finally:
        conn.close()

def get_access_logs(limit: int = 100):
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM access_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
        return [dict(row) for row in c.fetchall()]
    finally:
        conn.close()

def update_online_heartbeat(client_ip: str):
    """更新在线用户心跳时间"""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        now = time.time()
        c.execute("INSERT OR REPLACE INTO online_users VALUES (?, ?)", (client_ip, now))
        conn.commit()
    finally:
        conn.close()

def get_online_count(timeout_seconds: int = 15) -> int:
    """获取在线用户数量（超过timeout_seconds未心跳的视为离线）"""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        threshold = time.time() - timeout_seconds
        c.execute("SELECT COUNT(*) FROM online_users WHERE last_heartbeat >= ?", (threshold,))
        count = c.fetchone()[0]
    finally:
        conn.close()
    return count

def cleanup_offline_users(timeout_seconds: int = 15) -> int:
    """清理超时的离线用户"""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        threshold = time.time() - timeout_seconds
        c.execute("DELETE FROM online_users WHERE last_heartbeat < ?", (threshold,))
        deleted = c.rowcount
        conn.commit()
    finally:
        conn.close()
    return deleted

def ban_ip(ip: str, duration_minutes: int = 10, reason: str = "Rate limit exceeded"):
    """封禁 IP 指定时长"""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        now = time.time()
        banned_until = now + (duration_minutes * 60)
        c.execute("INSERT OR REPLACE INTO blacklist VALUES (?, ?, ?, ?)",
                  (ip, banned_until, reason, now))
        conn.commit()
    finally:
        conn.close()

def is_ip_banned(ip: str) -> bool:
    """检查 IP 是否被封禁，如果封禁过期则自动解封"""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT banned_until FROM blacklist WHERE ip_address = ?", (ip,))
        row = c.fetchone()
        
        is_banned = False
        if row:
            banned_until = row[0]
            if time.time() < banned_until:
                is_banned = True
            else:
                # 封禁已过期，移除记录
                c.execute("DELETE FROM blacklist WHERE ip_address = ?", (ip,))
                conn.commit()
    finally:
        conn.close()
    return is_banned

def check_ip_conflict(client_ip: str, full_room_code: str) -> bool:
    """检查同一IP是否已开设其他房间（防多开）"""
    existing_room_code = None
    conn = get_db_connection()
    c = conn.cursor()
    try:
        # 查找 IP 相同但房间号不同的记录
        c.execute("SELECT full_room_code FROM rooms WHERE client_ip = ? AND full_room_code != ?", (client_ip, full_room_code))
        row = c.fetchone()
        if row:
            existing_room_code = row[0]
    finally:
        conn.close()
    
    if existing_room_code:
        logger.warning(f"Conflict found for IP {client_ip}: Requesting {full_room_code}, but {existing_room_code} already exists.")
        return True
    
    # logger.info(f"No conflict for IP {client_ip} ({full_room_code})") # Debug log
    return False

def upsert_room(room: RoomCreate, client_ip: str):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        now = time.time()
        
        # 客户端默认值列表（这些值应该被服务端探测结果覆盖）
        CLIENT_DEFAULT_VERSIONS = ("未知版本", "1.20.1", "")
        
        # 先检查房间是否已存在，如果存在则保留已探测的 game_version 和 description
        c.execute("SELECT game_version, description FROM rooms WHERE full_room_code = ?", (room.full_room_code,))
        existing = c.fetchone()

        if existing:
            # 房间已存在，保留服务端探测的版本和描述（如果有效）
            existing_version, existing_desc = existing

            # 版本优先级逻辑：
            if existing_version and existing_version not in CLIENT_DEFAULT_VERSIONS:
                # 已有有效的探测版本，保留它
                game_version = existing_version
            elif room.game_version in CLIENT_DEFAULT_VERSIONS:
                # 客户端发的也是默认值，保持现有（可能是等待探测中）
                game_version = existing_version or room.game_version
            else:
                # 客户端发来了有效版本，使用它
                game_version = room.game_version

            # 描述同理：保留非空的现有描述
            description = existing_desc if existing_desc else room.description

            # 更新房间信息，但保留探测到的版本和描述
            c.execute('''UPDATE rooms SET 
                         remote_port = ?, node_id = ?, room_name = ?, game_version = ?,
                         player_count = ?, max_players = ?, description = ?, is_public = ?,
                         host_player = ?, server_addr = ?, updated_at = ?, client_ip = ?
                         WHERE full_room_code = ?''',
                      (room.remote_port, room.node_id, room.room_name, game_version,
                       room.player_count, room.max_players, description, 1 if room.is_public else 0,
                       room.host_player, room.server_addr, now, client_ip, room.full_room_code))
        else:
            # 新房间，直接插入
            c.execute('''INSERT INTO rooms VALUES 
                         (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (room.full_room_code, room.remote_port, room.node_id,
                       room.room_name, room.game_version, room.player_count,
                       room.max_players, room.description, 1 if room.is_public else 0,
                       room.host_player, room.server_addr, now, client_ip))

        conn.commit()
    finally:
        conn.close()

def delete_room(remote_port: int, node_id: int):
    full_room_code = f"{remote_port}_{node_id}"
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM rooms WHERE full_room_code = ?", (full_room_code,))
        conn.commit()
    finally:
        conn.close()

def get_rooms(limit: int = 100) -> List[RoomInfo]:
    rooms = []
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        # 简单的获取所有公开房间，按更新时间倒序
        c.execute("SELECT * FROM rooms WHERE is_public = 1 ORDER BY updated_at DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        
        # 必须在连接关闭前处理数据
        for row in rows:
            rooms.append(RoomInfo(
                full_room_code=row['full_room_code'],
                remote_port=row['remote_port'],
                node_id=row['node_id'],
                room_name=row['room_name'],
                game_version=row['game_version'],
                player_count=row['player_count'],
                max_players=row['max_players'],
                description=row['description'],
                is_public=bool(row['is_public']),
                host_player=row['host_player'],
                server_addr=row['server_addr'],
                updated_at=row['updated_at'],
                client_ip=row['client_ip']
            ))
    finally:
        conn.close()
    
    return rooms

def update_room_status(full_room_code: str, version: str, description: str):
    """更新房间的探测信息（版本和MOTD）"""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("UPDATE rooms SET game_version = ?, description = ? WHERE full_room_code = ?", 
                  (version, description, full_room_code))
        conn.commit()
    finally:
        conn.close()

def cleanup_stale_rooms(timeout_seconds: int = 10):
    """清理超时的房间"""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        threshold = time.time() - timeout_seconds
        c.execute("DELETE FROM rooms WHERE updated_at < ?", (threshold,))
        deleted_count = c.rowcount
        conn.commit()
    finally:
        conn.close()
    return deleted_count

