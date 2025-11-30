import subprocess
import os
import time
import threading
from typing import Generator, Optional
from src.utils.PathUtils import get_resource_path
from src.utils.LogManager import get_logger

logger = get_logger()

class ProcessManager:
    """
    负责管理外部进程 (如 frpc) 的生命周期。
    纯 Python 实现，线程安全。
    """
    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def run_frpc(self, ini_path: str) -> Generator[str, None, None]:
        """
        启动 frpc 进程并生成输出行。
        
        Args:
            ini_path: 配置文件路径
            
        Yields:
            进程的标准输出行 (stdout)
            
        Raises:
            FileNotFoundError: 如果 frpc.exe 未找到
            Exception: 其他启动错误
        """
        self._stop_event.clear()
        
        # Windows 特定的隐藏窗口标志
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creation_flags = subprocess.CREATE_NO_WINDOW
        
        frpc_exe = get_resource_path("frpc.exe")
        if not os.path.exists(frpc_exe):
            raise FileNotFoundError(f"frpc.exe 未找到: {frpc_exe}")

        try:
            with self._lock:
                self._process = subprocess.Popen(
                    [frpc_exe, "-c", ini_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    startupinfo=si,
                    creationflags=creation_flags,
                    bufsize=1  # 行缓冲
                )
            
            logger.info(f"已启动 frpc 进程 (PID: {self._process.pid})")

            # 实时读取输出
            # 注意: Popen.stdout 是一个迭代器，但在 process 结束前会阻塞等待新行
            if self._process.stdout:
                for line in self._process.stdout:
                    if self._stop_event.is_set():
                        break
                    yield line.strip()
                    
        except Exception as e:
            logger.error(f"ProcessManager 运行错误: {e}")
            raise
        finally:
            self._cleanup()

    def stop(self):
        """停止当前运行的进程"""
        self._stop_event.set()
        self._cleanup()

    def _cleanup(self):
        """清理进程资源"""
        with self._lock:
            if self._process:
                try:
                    if self._process.poll() is None:
                        logger.info("正在终止 frpc 进程...")
                        self._process.terminate()
                        
                        # 等待最多1秒
                        deadline = time.time() + 1
                        while time.time() < deadline and self._process.poll() is None:
                            time.sleep(0.1)
                        
                        # 强制杀死
                        if self._process.poll() is None:
                            logger.warning("进程未响应，强制 Kill")
                            self._process.kill()
                except Exception as e:
                    logger.error(f"清理进程时出错: {e}")
                finally:
                    self._process = None
