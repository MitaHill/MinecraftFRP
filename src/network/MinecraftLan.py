import socket
import struct
import re
import time
import sys
from PySide6.QtCore import QThread, Signal, QMutex, QMutexLocker
from src.utils.LogManager import get_logger

logger = get_logger()

# Minecraft LAN 探测配置
MCAST_GRP = '224.0.2.60'
MCAST_PORT = 4445
BUFFER_SIZE = 1024
MOTD_RE = re.compile(rb'\[MOTD\](.*?)\[/MOTD\]')
PORT_RE = re.compile(rb'\[AD\](\d+)\[/AD\]')

class MinecraftLANPoller(QThread):
    port_found = Signal(str)
    terminated = Signal()

    def __init__(self):
        super().__init__()
        self._stop_requested = False
        self.mutex = QMutex()
        self.last_port = None

    def run(self):
        sock = self._create_socket()
        
        while not self._stop_requested:
            try:
                if sock is None:
                    sock = self._create_socket()
                    if sock is None:
                        # 创建失败，等待后重试
                        time.sleep(2)
                        continue

                try:
                    data, addr = sock.recvfrom(BUFFER_SIZE)
                    port_match = PORT_RE.search(data)
                    if port_match:
                        port = port_match.group(1).decode()
                        if port and port != self.last_port:
                            self.last_port = port
                            self.port_found.emit(port)
                except socket.timeout:
                    pass # 超时正常，继续循环
                except OSError as e:
                    logger.error(f"LAN轮询器Socket错误 (尝试重建): {e}")
                    try:
                        sock.close()
                    except:
                        pass
                    sock = None # 下次循环将重建

            except Exception as e:
                logger.error(f"LAN轮询器未知错误: {e}")
                time.sleep(1)

            # 响应停止请求（即使在timeout期间）
            if self._stop_requested:
                break

        if sock:
            try:
                sock.close()
            except:
                pass
        self.terminated.emit()

    def _create_socket(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # 在Windows上设置较短的超时，以便能较快响应停止信号
            sock.settimeout(1.0) 

            try:
                sock.bind(('', MCAST_PORT))
            except OSError as e:
                logger.error(f"绑定端口失败: {e}")
                sock.close()
                return None

            mreq = struct.pack("=4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            return sock
        except Exception as e:
            logger.error(f"创建LAN轮询器套接字时出错: {e}")
            return None

    def _poll_minecraft_lan(self):
        # 此方法已废弃，逻辑移至 run 和 _create_socket
        pass

    def stop(self):
        with QMutexLocker(self.mutex):
            self._stop_requested = True

def poll_minecraft_lan_once():
    """单次Minecraft LAN探测函数"""
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(2)

        sock.bind(('', MCAST_PORT))
        mreq = struct.pack("=4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        data, _ = sock.recvfrom(BUFFER_SIZE)
        port_match = PORT_RE.search(data)
        if port_match:
            return port_match.group(1).decode()
    except socket.timeout:
        return None
    except Exception as e:
        logger.error(f"UDP查询出错: {e}")
        return None
    finally:
        if sock:
            sock.close()
    return None