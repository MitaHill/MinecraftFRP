import time
from PySide6.QtCore import QThread, Signal
from src.utils.HttpManager import post_json
from src.utils.LogManager import get_logger
from src.config.SecretConfig import SecretConfig

logger = get_logger()

class TunnelMonitor(QThread):
    """
    Independent thread to monitor active tunnel health via Server API.
    Sends heartbeat every 15 seconds.
    If Server says 'stop', emits stop_mapping_signal.
    """
    stop_mapping_signal = Signal(str) # Emits reason for stopping
    
    def __init__(self, server_addr, remote_port):
        super().__init__()
        self.server_addr = server_addr
        self.remote_port = remote_port
        self.is_running = True
        self.api_url = SecretConfig.TUNNEL_VALIDATE_API

    def run(self):
        logger.info(f"TunnelMonitor started for {self.server_addr}:{self.remote_port}")
        
        # Add initial delay to ensure tunnel is fully stable
        # Allow 5 seconds for FRPC to register and server to propagate
        for _ in range(5):
            if not self.is_running: return
            time.sleep(1)
        
        while self.is_running:
            try:
                # 1. Prepare Data
                payload = {
                    "server_addr": self.server_addr,
                    "remote_port": int(self.remote_port)
                }
                
                # 2. Send Heartbeat (Robust check happens on server side)
                # Client timeout 15s to allow server to perform 5 retries (2s * 5 + buffer)
                response = post_json(self.api_url, payload, timeout=15)
                
                if response:
                    command = response.get("command")
                    if command == "stop":
                        reason = response.get("reason", "Server requested stop")
                        logger.warning(f"TunnelMonitor received STOP command: {reason}")
                        self.stop_mapping_signal.emit(reason)
                        break # Exit loop
                
            except Exception as e:
                logger.error(f"TunnelMonitor error: {e}")
                # Network error doesn't mean we stop immediately (could be transient)
                # But if it persists, user might notice. 
                # Strategy: Keep trying until server explicitly says STOP or user stops.
            
            # 3. Sleep 15s
            for _ in range(15):
                if not self.is_running: break
                time.sleep(1)
                
        logger.info("TunnelMonitor stopped")

    def stop(self):
        self.is_running = False
        self.wait()
