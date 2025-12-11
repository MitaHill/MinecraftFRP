import sqlite3
import time
import json
from typing import List, Optional
from .models import RoomCreate, RoomInfo
from .logger import logger

DB_PATH = "data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
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
    
    conn.commit()
    conn.close()

def ban_ip(ip: str, duration_minutes: int = 10, reason: str = "Rate limit exceeded"):
    """封禁 IP 指定时长"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = time.time()
    banned_until = now + (duration_minutes * 60)
    
    c.execute("INSERT OR REPLACE INTO blacklist VALUES (?, ?, ?, ?)",
              (ip, banned_until, reason, now))
    conn.commit()
    conn.close()

def is_ip_banned(ip: str) -> bool:
    """检查 IP 是否被封禁，如果封禁过期则自动解封"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
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
            
    conn.close()
    return is_banned

def check_ip_conflict(client_ip: str, full_room_code: str) -> bool:
    """检查同一IP是否已开设其他房间（防多开）"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 查找 IP 相同但房间号不同的记录
    c.execute("SELECT full_room_code FROM rooms WHERE client_ip = ? AND full_room_code != ?", (client_ip, full_room_code))
    row = c.fetchone()
    
    conn.close()
    
    if row:
        logger.warning(f"Conflict found for IP {client_ip}: Requesting {full_room_code}, but {row[0]} already exists.")
        return True
    
    # logger.info(f"No conflict for IP {client_ip} ({full_room_code})") # Debug log
    return False

def upsert_room(room: RoomCreate, client_ip: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = time.time()
    
    # 使用 REPLACE INTO 或 INSERT OR REPLACE 实现 upsert
    c.execute('''INSERT OR REPLACE INTO rooms VALUES 
                 (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (room.full_room_code, room.remote_port, room.node_id,
               room.room_name, room.game_version, room.player_count,
               room.max_players, room.description, 1 if room.is_public else 0,
               room.host_player, room.server_addr, now, client_ip))
    
    conn.commit()
    conn.close()

def delete_room(remote_port: int, node_id: int):
    full_room_code = f"{remote_port}_{node_id}"
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM rooms WHERE full_room_code = ?", (full_room_code,))
    conn.commit()
    conn.close()

def get_rooms(limit: int = 100) -> List[RoomInfo]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # 简单的获取所有公开房间，按更新时间倒序
    c.execute("SELECT * FROM rooms WHERE is_public = 1 ORDER BY updated_at DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    
    rooms = []
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
    return rooms

def update_room_status(full_room_code: str, version: str, description: str):
    """更新房间的探测信息（版本和MOTD）"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE rooms SET game_version = ?, description = ? WHERE full_room_code = ?", 
              (version, description, full_room_code))
    conn.commit()
    conn.close()

def cleanup_stale_rooms(timeout_seconds: int = 10):
    """清理超时的房间"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    threshold = time.time() - timeout_seconds
    c.execute("DELETE FROM rooms WHERE updated_at < ?", (threshold,))
    deleted_count = c.rowcount
    conn.commit()
    conn.close()
    return deleted_count
