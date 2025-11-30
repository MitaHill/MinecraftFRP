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
        while not self._stop_requested:
            try:
                port = self._poll_minecraft_lan()
                if port and port != self.last_port:
                    self.last_port = port
                    self.port_found.emit(port)
            except Exception as e:
                logger.error(f"LAN轮询器出错: {e}")

            for _ in range(3):
                if self._stop_requested:
                    break
                time.sleep(0.1)

        self.terminated.emit()

    def _poll_minecraft_lan(self):
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(0.5)

            try:
                sock.bind(('', MCAST_PORT))
            except OSError as e:
                logger.error(f"绑定端口失败: {e}")
                return None

            mreq = struct.pack("=4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                port_match = PORT_RE.search(data)
                if port_match:
                    return port_match.group(1).decode()
            except socket.timeout:
                pass
            except Exception as e:
                logger.error(f"接收LAN广播时出错: {e}")

            return None

        except Exception as e:
            logger.error(f"创建LAN轮询器套接字时出错: {e}")
            return None
        finally:
            if sock:
                try:
                    sock.close()
                except:
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