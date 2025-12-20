import subprocess
import os
import logging
from typing import Generator
from src.utils.PathUtils import get_resource_path
import platform

logger = logging.getLogger(__name__)

class ProcessManager:
    """
    负责管理外部进程 (如 frpc) 的生命周期。
    """
    def __init__(self):
        self.process = None

    def run_frpc(self, config_or_args) -> Generator[str, None, None]:
        """
        启动 frpc 进程并生成输出行。
        
        Args:
            config_or_args: 
                - 配置文件路径字符串 (.toml 使用 new-frpc.exe)
                - 或者 命令行参数列表 (使用 frpc.exe)
        
        Yields:
            进程的 stdout 输出行。
        """
        exe_name = "frpc.exe"
        command_args = []

        if isinstance(config_or_args, list):
            # 命令行参数模式 (普通节点)
            exe_name = "frpc.exe"
            command_args = [str(arg) for arg in config_or_args]
        elif isinstance(config_or_args, str):
            # 配置文件模式 (特殊节点 或 旧兼容)
            if config_or_args.endswith(".toml"):
                exe_name = "new-frpc.exe"
            else:
                exe_name = "frpc.exe"
            command_args = ["-c", config_or_args]
        else:
             raise ValueError("run_frpc expects a list or a string")

        frpc_exe_path = get_resource_path(f"base/{exe_name}")

        if not os.path.exists(frpc_exe_path):
            raise FileNotFoundError(f"{exe_name} 未找到: {frpc_exe_path}")

        # 构建完整命令行
        command = [str(frpc_exe_path)] + command_args
        
        logger.info(f"正在启动 frpc 进程: {' '.join(command)}")

        # 为 Windows 设置特定的启动标志，以隐藏控制台窗口
        startupinfo = None
        creationflags = 0
        if platform.system().lower() == "windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            creationflags = subprocess.CREATE_NO_WINDOW

        try:
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # 将 stderr 重定向到 stdout
                text=True,
                encoding='utf-8',
                errors='replace',
                startupinfo=startupinfo,
                creationflags=creationflags,
                # bufsize=1, # 开启行缓冲
                # universal_newlines=True # 在 text=True 时已隐含
            )

            # 逐行读取输出
            if self.process.stdout:
                for line in iter(self.process.stdout.readline, ''):
                    yield line.strip()
            
            # 等待进程结束并检查返回码
            self.process.wait()
            if self.process.returncode != 0:
                logger.error(f"frpc 进程异常退出，返回码: {self.process.returncode}")
                # 可以选择抛出异常，让调用者知道
                # raise RuntimeError(f"frpc exited with code {self.process.returncode}")

        except FileNotFoundError:
            logger.error(f"无法启动 frpc: {frpc_exe_path} 未找到或无权限。")
            raise
        except Exception as e:
            logger.error(f"运行 frpc 进程时发生未知错误: {e}", exc_info=True)
            raise RuntimeError(f"Failed to run frpc: {e}")
        finally:
            self.process = None


    def terminate_process(self):
        """终止正在运行的 frpc 进程"""
        if self.process and self.process.poll() is None:
            logger.info("正在终止 frpc 进程...")
            try:
                self.process.terminate()
                self.process.wait(timeout=2) # 等待2秒
            except subprocess.TimeoutExpired:
                logger.warning("终止 frpc 进程超时，强制结束。")
                self.process.kill()
            except Exception as e:
                logger.error(f"终止 frpc 进程时出错: {e}")
            finally:
                self.process = None
                logger.info("frpc 进程已终止。")

    def stop(self):
        """停止进程 (terminate_process 的别名，供外部调用)"""
        self.terminate_process()
