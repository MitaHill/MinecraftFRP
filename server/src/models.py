from pydantic import BaseModel
from typing import Optional

class RoomBase(BaseModel):
    remote_port: int
    node_id: int
    room_name: str
    game_version: Optional[str] = "未知版本"
    player_count: int = 0
    max_players: int = 20
    description: Optional[str] = "欢迎来玩！"
    is_public: bool = True
    host_player: str
    server_addr: str
    full_room_code: str  # 幂等键: "{remote_port}_{node_id}"

class RoomCreate(RoomBase):
    pass

class RoomDelete(BaseModel):
    remote_port: int
    node_id: int

class RoomInfo(RoomBase):
    updated_at: float
    client_ip: str  # 记录客户端真实IP

class RuleCreate(BaseModel):
    rule: str # CIDR, Range, or List
    reason: Optional[str] = "Admin ban"
    duration_minutes: Optional[int] = 0 # 0 for infinite (blacklist default), or whitelist duration

class RuleDelete(BaseModel):
    rule: str

class ViolationReport(BaseModel):
    traceroute_hops: list[str]
    reason: str
