import os
import time
import logging
from PySide6.QtCore import QThread, QMutex

logger = logging.getLogger("MinecraftFRP")

class LogTrimmer(QThread):
    def __init__(self, log_file_path, max_size_config, interval=3):
        super().__init__()
        self.log_file_path = log_file_path
        self.max_size = self._parse_size(max_size_config)
        self.interval = interval
        self.running = True
        # 注意：此 Mutex 仅用于线程内部同步，无法阻止其他进程/线程访问文件
        self.mutex = QMutex()

    def _parse_size(self, size_config):
        """解析大小配置，支持 '1MB', '500KB', 整数(字节)"""
        if isinstance(size_config, int):
            return size_config
        
        if isinstance(size_config, str):
            s = size_config.upper().strip()
            try:
                if s.endswith('KB'):
                    return int(float(s[:-2]) * 1024)
                elif s.endswith('MB'):
                    return int(float(s[:-2]) * 1024 * 1024)
                elif s.endswith('GB'):
                    return int(float(s[:-2]) * 1024 * 1024 * 1024)
                elif s.endswith('B'):
                    return int(float(s[:-1]))
                else:
                    return int(s)
            except ValueError:
                pass
        
        # 默认 1MB
        return 1024 * 1024

    def run(self):
        logger.info(f"LogTrimmer started. Max size: {self.max_size} bytes, Check interval: {self.interval}s")
        while self.running:
            self.trim_log()
            # 使用 QThread.sleep 或者 time.sleep
            # 这里简单实现等待逻辑，支持随时中断
            for _ in range(self.interval * 10): # 0.1s check
                if not self.running:
                    return
                time.sleep(0.1)

    def stop(self):
        self.running = False
        self.wait()

    def trim_log(self):
        try:
            if not os.path.exists(self.log_file_path):
                return

            current_size = os.path.getsize(self.log_file_path)
            if current_size <= self.max_size:
                return

            # 尝试进行裁剪
            try:
                with open(self.log_file_path, 'rb') as f:
                    # 为了效率，只读取最后 max_size 的数据
                    # 注意：我们需要多读一点以确保找到完整的行
                    read_size = self.max_size + 1024 
                    if current_size > read_size:
                        f.seek(current_size - read_size)
                    else:
                        f.seek(0)
                    
                    content = f.read()

                # 如果内容超过 max_size，截取
                if len(content) > self.max_size:
                    # 从尾部截取 max_size
                    new_content = content[-self.max_size:]
                    
                    # 寻找第一个换行符，丢弃不完整的行
                    first_newline = new_content.find(b'\n')
                    if first_newline != -1 and first_newline < len(new_content) - 1:
                        new_content = new_content[first_newline + 1:]
                    
                    # 写入回文件 (这会清空原文件并写入新内容)
                    with open(self.log_file_path, 'wb') as f:
                        f.write(new_content)
                    
                    # logger.debug(f"Log trimmed: {current_size} -> {len(new_content)}")
                    # 不要在裁剪成功后立即记录日志，否则可能触发循环（虽然文件刚关闭应该没事）

            except PermissionError:
                # 文件被 LogManager 或其他程序占用，跳过本次
                pass
            except Exception as e:
                logger.warning(f"Log trim error: {e}")

        except Exception as e:
            logger.error(f"LogTrimmer critical error: {e}")
