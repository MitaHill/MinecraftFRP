import threading
import time
import json
import urllib.request
import urllib.parse
from urllib.error import URLError, HTTPError
from PySide6.QtCore import QObject, Signal

class HeartbeatManager(QObject):
    """
    管理房间心跳的模块，负责向服务器发送房间状态，并处理房间的发布和删除。
    """
    log_signal = Signal(str, str)

    def __init__(self, server_url, is_frp_running_callback):
        """
        初始化心跳管理器。
        server_url: 服务器 API 地址
        is_frp_running_callback: 检查 FRP 进程状态回调
        """
        super().__init__()
        self.server_url = server_url
        self.is_frp_running_callback = is_frp_running_callback

        self.heartbeat_active = False
        self.heartbeat_thread = None
        self.current_room_info = None # 存储当前正在发送心跳的房间信息

    def _http_request(self, method, data=None):
        """
        私有方法：执行HTTP请求。
        """
        try:
            if method == "GET":
                req = urllib.request.Request(self.server_url)
            else:
                headers = {'Content-Type': 'application/json', 'User-Agent': 'LMFP/1.3.1'}
                json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
                req = urllib.request.Request(self.server_url, data=json_data, headers=headers, method=method)

            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode('utf-8')
                return json.loads(content)
        except URLError as e:
            self.log_signal.emit(f"✗ 网络连接失败: {e.reason}", "red")
            return None
        except HTTPError as e:
            self.log_signal.emit(f"✗ HTTP错误 {e.code}: {e.reason}", "red")
            return None
        except json.JSONDecodeError as e:
            self.log_signal.emit(f"✗ JSON解析失败: {e}", "red")
            return None
        except UnicodeDecodeError as e:
            self.log_signal.emit(f"✗ 字符编码错误: {e}", "red")
            try:
                # 尝试用gbk解码
                if method == "GET":
                    req = urllib.request.Request(self.server_url)
                else:
                    headers = {'Content-Type': 'application/json', 'User-Agent': 'LMFP/1.3.1'}
                    json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
                    req = urllib.request.Request(self.server_url, data=json_data, headers=headers, method=method)
                
                with urllib.request.urlopen(req, timeout=15) as response:
                    content = response.read().decode('gbk')
                    return json.loads(content)
            except Exception:
                self.log_signal.emit("✗ 所有编码方式都失败了", "red")
                return None
        except Exception as e:
            self.log_signal.emit(f"✗ HTTP请求失败: {str(e)}", "red")
            return None

    def submit_room_info(self, room_info, start_heartbeat=True):
        """
        提交房间信息到服务器。可以用于发布房间或作为心跳的初始提交。

        Args:
            room_info (dict): 包含房间信息的字典。
            start_heartbeat (bool): 如果为True，则在提交成功后启动心跳。
        """
        # 合规性检查
        host_player = room_info.get('host_player', '').strip()
        if not host_player:
            self.log_signal.emit("✗ 提交房间信息失败：房主ID不能为空。", "red")
            return

        def submit_thread():
            try:
                full_room_code = room_info.get('full_room_code')
                if not full_room_code:
                    self.log_signal.emit("✗ 提交房间信息失败：缺少full_room_code。", "red")
                    return

                room_parts = full_room_code.split('_')
                if len(room_parts) != 2:
                    self.log_signal.emit("✗ 提交房间信息失败：房间号格式错误。", "red")
                    return

                remote_port = int(room_parts[0])
                node_id = int(room_parts[1])

                submit_data = {
                    'full_room_code': full_room_code,
                    'remote_port': remote_port,
                    'node_id': node_id,
                    'room_name': room_info.get('room_name', '未知房间'),
                    'game_version': room_info.get('game_version', '未知版本'),
                    'player_count': room_info.get('player_count', 1),
                    'max_players': room_info.get('max_players', 20),
                    'description': room_info.get('description', '欢迎来玩！'),
                    'is_public': room_info.get('is_public', True),
                    'host_player': host_player,
                    'server_addr': room_info.get('server_addr', '未知地址')
                }

                # self.log_signal.emit(f"提交房间数据: {json.dumps(submit_data, ensure_ascii=False)}", "blue")
                response = self._http_request("POST", submit_data)
                if response and response.get('success'):
                    if room_info.get('is_public'):
                        self.log_signal.emit("✓ 房间已发布到联机大厅", "green")
                    else:
                        self.log_signal.emit("✓ 私有房间创建成功", "green")
                    
                    if start_heartbeat:
                        self.start_room_heartbeat(room_info)
                else:
                    error_msg = response.get('message', '未知错误') if response else '请求失败'
                    self.log_signal.emit(f"⚠ 房间信息发布失败: {error_msg}", "orange")
            except Exception as e:
                self.log_signal.emit(f"✗ 发布房间信息时出错: {e}", "red")
        
        threading.Thread(target=submit_thread, daemon=True).start()

    def start_room_heartbeat(self, room_info):
        """
        启动房间心跳监控，定期向服务器发送房间状态。
        """
        if self.heartbeat_active:
            self.stop_room_heartbeat() # 停止旧的心跳

        self.current_room_info = room_info
        self.heartbeat_active = True
        
        def heartbeat_loop():
            heartbeat_count = 0
            while self.heartbeat_active:
                try:
                    # 检查FRP进程是否运行，如果FRP停止，则心跳也应停止
                    if not self.is_frp_running_callback():
                        self.log_signal.emit("■ FRP进程未运行，停止发送心跳包", "blue")
                        self.stop_room_heartbeat()
                        break
                    
                    full_room_code = self.current_room_info.get('full_room_code')
                    if not full_room_code:
                        self.log_signal.emit("✗ 心跳发送失败：缺少full_room_code。", "red")
                        self.stop_room_heartbeat()
                        break

                    room_parts = full_room_code.split('_')
                    if len(room_parts) != 2:
                        self.log_signal.emit("✗ 心跳发送失败：房间号格式错误。", "red")
                        self.stop_room_heartbeat()
                        break
                        
                    remote_port = int(room_parts[0])
                    node_id = int(room_parts[1])
                    
                    # 重新构造心跳数据，以防房间信息在外部被修改（虽然此处应该使用self.current_room_info）
                    # 保证每次发送的是最新的房间状态
                    heartbeat_data = {
                        'full_room_code': full_room_code,
                        'remote_port': remote_port,
                        'node_id': node_id,
                        'room_name': self.current_room_info.get('room_name', '未知房间'),
                        'game_version': self.current_room_info.get('game_version', '未知版本'),
                        'player_count': self.current_room_info.get('player_count', 1),
                        'max_players': self.current_room_info.get('max_players', 20),
                        'description': self.current_room_info.get('description', '欢迎来玩！'),
                        'is_public': self.current_room_info.get('is_public', True),
                        'host_player': self.current_room_info.get('host_player', '未知房主'),
                        'server_addr': self.current_room_info.get('server_addr', '未知地址')
                    }
                    
                    response = self._http_request("POST", heartbeat_data)
                    heartbeat_count += 1
                    if response and response.get('success'):
                        self.log_signal.emit(f"心跳发送成功 #{heartbeat_count}（30秒）", "green")
                    else:
                        error_msg = response.get('message', '未知错误') if response else '请求失败'
                        self.log_signal.emit(f"⚠ 房间心跳发送失败 #{heartbeat_count}: {error_msg}", "orange")
                except Exception as e:
                    self.log_signal.emit(f"✗ 心跳发送错误 #{heartbeat_count}: {e}", "red")
                
                # 等待5秒，期间检查心跳状态以便及时停止
                for _ in range(5):
                    if not self.heartbeat_active:
                        break
                    if not self.is_frp_running_callback(): # 再次检查FRP状态
                        self.log_signal.emit("■ 检测到FRP进程已停止，停止心跳包", "blue")
                        self.stop_room_heartbeat()
                        break
                    time.sleep(1)
        
        self.heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        self.log_signal.emit("✓ 房间心跳监控已启动（每30秒一次，自动检测FRP状态）", "green")

    def stop_room_heartbeat(self):
        """
        停止房间心跳监控，并通知服务器删除房间信息。
        """
        if self.heartbeat_active:
            self.heartbeat_active = False
            
            # 避免线程等待自己结束（死锁/RuntimeError）
            if self.heartbeat_thread and self.heartbeat_thread is not threading.current_thread() and self.heartbeat_thread.is_alive():
                self.heartbeat_thread.join(timeout=2)
            
            # 如果有当前房间信息，尝试通知服务器删除
            if self.current_room_info:
                self.log_signal.emit("从联机大厅移除房间信息...", "blue")
                self.delete_room_info(self.current_room_info)
                self.current_room_info = None # 清空当前房间信息
            
            self.log_signal.emit("■ 房间心跳监控已停止", "blue")

    def delete_room_info(self, room_info):
        """
        通知服务器删除指定房间的信息。
        """
        def delete_thread():
            try:
                full_room_code = room_info.get('full_room_code')
                if not full_room_code:
                    self.log_signal.emit("✗ 删除房间信息失败：缺少full_room_code。", "red")
                    return

                room_parts = full_room_code.split('_')
                if len(room_parts) != 2:
                    self.log_signal.emit("✗ 删除房间信息失败：房间号格式错误。", "red")
                    return
                    
                remote_port = int(room_parts[0])
                node_id = int(room_parts[1])
                
                delete_data = {'remote_port': remote_port, 'node_id': node_id}
                # self.log_signal.emit(f"发送删除请求: {json.dumps(delete_data, ensure_ascii=False)}", "blue")
                
                response = self._http_request("DELETE", delete_data)
                if response:
                    if response.get('success'):
                        self.log_signal.emit("✓ 房间信息已从大厅移除", "green")
                    else:
                        error_msg = response.get('message', '未知错误')
                        self.log_signal.emit(f"⚠ 房间信息移除失败: {error_msg}", "orange")
                else:
                    self.log_signal.emit("✗ 删除请求无响应", "red")
            except Exception as e:
                self.log_signal.emit(f"✗ 移除房间信息时出错: {e}", "red")
        
        threading.Thread(target=delete_thread, daemon=True).start()
