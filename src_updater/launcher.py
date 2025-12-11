"""
MinecraftFRP 启动器/更新器 v2.0
作为程序入口，负责检查更新并启动主程序
"""
import sys
import os
import subprocess
import hashlib
import tempfile
import shutil
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, 
    QProgressBar, QTextEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QFont


class UpdateCheckThread(QThread):
    """更新检查线程"""
    log_signal = Signal(str)
    progress_signal = Signal(int, str)
    result_signal = Signal(bool, str, dict)  # 需要更新, 消息, 更新信息
    
    def __init__(self, current_version, version_url, main_exe_path):
        super().__init__()
        self.current_version = current_version
        self.version_url = version_url
        self.main_exe_path = main_exe_path
        
    def run(self):
        """检查更新"""
        try:
            self.log_signal.emit("正在检查更新...")
            self.progress_signal.emit(10, "连接服务器...")
            
            # 导入 HttpManager
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
            from core.HttpManager import HttpManager
            
            http_mgr = HttpManager()
            
            # 获取版本信息
            self.progress_signal.emit(30, "获取版本信息...")
            version_data = http_mgr.get_json(self.version_url)
            
            if not version_data:
                self.result_signal.emit(False, "无法获取版本信息", {})
                return
            
            server_version = version_data.get('version', '0.0.0')
            self.log_signal.emit(f"当前版本: {self.current_version}")
            self.log_signal.emit(f"最新版本: {server_version}")
            
            # 比较版本
            if self._compare_versions(server_version, self.current_version) > 0:
                self.log_signal.emit("发现新版本！")
                self.result_signal.emit(True, f"发现新版本 {server_version}", version_data)
            else:
                self.log_signal.emit("当前已是最新版本")
                self.progress_signal.emit(100, "启动程序...")
                self.result_signal.emit(False, "无需更新", {})
                
        except Exception as e:
            self.log_signal.emit(f"检查更新失败: {str(e)}")
            self.result_signal.emit(False, "检查失败，使用本地版本", {})
    
    def _compare_versions(self, v1, v2):
        """比较版本号，返回 1(v1>v2), 0(相等), -1(v1<v2)"""
        try:
            parts1 = [int(x) for x in v1.split('.')]
            parts2 = [int(x) for x in v2.split('.')]
            
            for p1, p2 in zip(parts1, parts2):
                if p1 > p2:
                    return 1
                elif p1 < p2:
                    return -1
            
            if len(parts1) > len(parts2):
                return 1
            elif len(parts1) < len(parts2):
                return -1
            
            return 0
        except:
            return 0


class UpdateDownloadThread(QThread):
    """更新下载线程"""
    log_signal = Signal(str)
    progress_signal = Signal(int, str)
    result_signal = Signal(bool, str, str)  # 成功, 消息, 文件路径
    
    def __init__(self, download_url, expected_sha256, target_path):
        super().__init__()
        self.download_url = download_url
        self.expected_sha256 = expected_sha256
        self.target_path = target_path
        
    def run(self):
        """下载更新"""
        try:
            self.log_signal.emit("开始下载更新...")
            self.progress_signal.emit(0, "正在下载...")
            
            # 导入 HttpManager
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
            from core.HttpManager import HttpManager
            
            http_mgr = HttpManager()
            
            # 下载文件
            success = http_mgr.download_file(
                self.download_url,
                self.target_path,
                progress_callback=lambda current, total: self.progress_signal.emit(
                    int((current / total) * 90) if total > 0 else 0,
                    f"下载中: {current / (1024*1024):.1f}MB / {total / (1024*1024):.1f}MB"
                )
            )
            
            if not success:
                self.result_signal.emit(False, "下载失败", "")
                return
            
            self.progress_signal.emit(90, "验证文件...")
            
            # 验证 SHA256
            sha256 = self._calculate_sha256(self.target_path)
            if sha256.lower() != self.expected_sha256.lower():
                self.log_signal.emit(f"SHA256 不匹配！")
                self.log_signal.emit(f"预期: {self.expected_sha256}")
                self.log_signal.emit(f"实际: {sha256}")
                self.result_signal.emit(False, "文件校验失败", "")
                return
            
            self.log_signal.emit("文件验证成功")
            self.progress_signal.emit(100, "下载完成")
            self.result_signal.emit(True, "更新下载完成", self.target_path)
            
        except Exception as e:
            self.log_signal.emit(f"下载失败: {str(e)}")
            self.result_signal.emit(False, f"下载出错: {str(e)}", "")
    
    def _calculate_sha256(self, filepath):
        """计算文件 SHA256"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


class LauncherWindow(QWidget):
    """启动器主窗口"""
    
    def __init__(self):
        super().__init__()
        self.base_dir = self._get_base_dir()
        self.main_exe = os.path.join(self.base_dir, "MinecraftFRP.exe")
        self.current_version = self._get_current_version()
        self.version_url = "https://z.clash.ink/chfs/shared/MinecraftFRP/Data/version.json"
        
        self.check_thread = None
        self.download_thread = None
        self.update_info = {}
        
        self.init_ui()
        
        # 自动开始检查更新
        self.check_update()
    
    def _get_base_dir(self):
        """获取程序基础目录"""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    def _get_current_version(self):
        """获取当前版本"""
        try:
            version_file = os.path.join(self.base_dir, "config", "version.json")
            if os.path.exists(version_file):
                import json
                with open(version_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('version', '0.0.0')
        except:
            pass
        return "0.0.0"
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle(f"MinecraftFRP 启动器 v{self.current_version}")
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("MinecraftFRP")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 版本信息
        self.version_label = QLabel(f"当前版本: {self.current_version}")
        self.version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.version_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("正在启动...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 日志区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)
        
        # 按钮区域
        self.start_btn = QPushButton("启动程序")
        self.start_btn.clicked.connect(self.start_main_program)
        self.start_btn.setEnabled(False)
        layout.addWidget(self.start_btn)
        
        self.setLayout(layout)
    
    def append_log(self, message):
        """添加日志"""
        self.log_text.append(message)
    
    def update_progress(self, value, message):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def check_update(self):
        """检查更新"""
        self.append_log("启动器初始化完成")
        
        self.check_thread = UpdateCheckThread(
            self.current_version,
            self.version_url,
            self.main_exe
        )
        self.check_thread.log_signal.connect(self.append_log)
        self.check_thread.progress_signal.connect(self.update_progress)
        self.check_thread.result_signal.connect(self.on_check_result)
        self.check_thread.start()
    
    def on_check_result(self, need_update, message, update_info):
        """更新检查结果"""
        self.append_log(message)
        
        if need_update:
            self.update_info = update_info
            reply = QMessageBox.question(
                self,
                "发现新版本",
                f"{message}\n\n{update_info.get('changelog', '')}\n\n是否现在更新？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.download_update()
            else:
                self.start_main_program()
        else:
            # 无需更新，直接启动
            self.start_main_program()
    
    def download_update(self):
        """下载更新"""
        download_url = self.update_info.get('download_url')
        sha256 = self.update_info.get('sha256')
        
        if not download_url or not sha256:
            QMessageBox.warning(self, "错误", "更新信息不完整")
            self.start_main_program()
            return
        
        temp_file = os.path.join(tempfile.gettempdir(), "MinecraftFRP_Update.exe")
        
        self.download_thread = UpdateDownloadThread(download_url, sha256, temp_file)
        self.download_thread.log_signal.connect(self.append_log)
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.result_signal.connect(self.on_download_result)
        self.download_thread.start()
    
    def on_download_result(self, success, message, file_path):
        """下载结果"""
        self.append_log(message)
        
        if success:
            # 执行文件替换
            self.replace_files(file_path)
        else:
            reply = QMessageBox.question(
                self,
                "更新失败",
                f"{message}\n\n是否继续使用当前版本？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.start_main_program()
            else:
                self.close()
    
    def replace_files(self, new_file):
        """替换文件"""
        try:
            self.append_log("正在替换文件...")
            self.update_progress(0, "替换中...")
            
            # 备份旧文件
            backup_path = self.main_exe + ".bak"
            if os.path.exists(self.main_exe):
                shutil.copy2(self.main_exe, backup_path)
                self.append_log(f"已备份旧版本")
            
            # 替换
            shutil.copy2(new_file, self.main_exe)
            self.append_log("文件替换成功")
            
            # 删除临时文件
            try:
                os.remove(new_file)
            except:
                pass
            
            # 删除备份
            try:
                os.remove(backup_path)
            except:
                pass
            
            self.update_progress(100, "更新完成")
            QMessageBox.information(self, "成功", "更新完成！即将启动新版本")
            
            self.start_main_program()
            
        except Exception as e:
            self.append_log(f"文件替换失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"更新失败: {str(e)}")
            self.start_btn.setEnabled(True)
    
    def start_main_program(self):
        """启动主程序"""
        try:
            if not os.path.exists(self.main_exe):
                QMessageBox.critical(self, "错误", f"未找到主程序：\n{self.main_exe}")
                return
            
            self.append_log("启动主程序...")
            self.update_progress(100, "启动中...")
            
            # 启动主程序（分离进程）
            subprocess.Popen([self.main_exe], cwd=self.base_dir)
            
            # 关闭启动器
            self.close()
            
        except Exception as e:
            self.append_log(f"启动失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"无法启动主程序：\n{str(e)}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = LauncherWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
