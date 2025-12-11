"""
MinecraftFRP 安装程序 - 图形界面
v2.0 架构 - 轻量化安装器
"""
import os
import sys
import shutil
import zipfile
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QFileDialog, QProgressBar, QMessageBox,
    QTextBrowser, QCheckBox, QStackedWidget
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont


class InstallThread(QThread):
    """安装线程，执行文件复制操作"""
    progress = Signal(int, str)  # 进度, 消息
    finished = Signal(bool, str)  # 成功/失败, 消息
    
    def __init__(self, source_dir, target_dir, version, create_shortcuts=True):
        super().__init__()
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.version = version
        self.create_shortcuts = create_shortcuts
        
    def run(self):
        try:
            os.makedirs(self.target_dir, exist_ok=True)
            self.progress.emit(10, "创建安装目录...")
            
            self.progress.emit(20, "正在复制程序文件...")
            
            if os.path.isfile(self.source_dir) and self.source_dir.endswith('.zip'):
                with zipfile.ZipFile(self.source_dir, 'r') as zip_ref:
                    files = zip_ref.namelist()
                    total = len(files)
                    for i, file in enumerate(files):
                        zip_ref.extract(file, self.target_dir)
                        progress_pct = 20 + int((i / total) * 50)
                        self.progress.emit(progress_pct, f"解压文件 {i+1}/{total}")
            else:
                total_files = sum([len(files) for _, _, files in os.walk(self.source_dir)])
                copied = 0
                
                for root, dirs, files in os.walk(self.source_dir):
                    rel_path = os.path.relpath(root, self.source_dir)
                    target_path = os.path.join(self.target_dir, rel_path)
                    os.makedirs(target_path, exist_ok=True)
                    
                    for file in files:
                        src_file = os.path.join(root, file)
                        dst_file = os.path.join(target_path, file)
                        shutil.copy2(src_file, dst_file)
                        copied += 1
                        progress_pct = 20 + int((copied / total_files) * 50)
                        self.progress.emit(progress_pct, f"复制文件 {copied}/{total_files}")
            
            self.progress.emit(75, "保存安装信息...")
            self._save_install_info()
            
            if self.create_shortcuts:
                self.progress.emit(85, "创建快捷方式...")
                self._create_shortcuts()
            
            self.progress.emit(95, "完成安装...")
            self.finished.emit(True, "安装成功！")
            
        except Exception as e:
            self.finished.emit(False, f"安装失败：{str(e)}")
    
    def _save_install_info(self):
        """保存安装信息到文档目录"""
        try:
            doc_path = Path.home() / "Documents" / "MitaHillFRP"
            doc_path.mkdir(parents=True, exist_ok=True)
            
            install_info = {
                "version": self.version,
                "install_path": self.target_dir,
                "install_date": str(Path.ctime(Path(self.target_dir)))
            }
            
            with open(doc_path / "install_info.json", 'w', encoding='utf-8') as f:
                json.dump(install_info, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    
    def _create_shortcuts(self):
        """创建桌面和开始菜单快捷方式"""
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            
            launcher_exe = os.path.join(self.target_dir, "Launcher.exe")
            
            # 桌面快捷方式
            desktop = Path.home() / "Desktop"
            desktop_shortcut = desktop / "Minecraft联机工具.lnk"
            shortcut = shell.CreateShortcut(str(desktop_shortcut))
            shortcut.TargetPath = launcher_exe
            shortcut.WorkingDirectory = self.target_dir
            shortcut.IconLocation = launcher_exe
            shortcut.Description = "MinecraftFRP 内网穿透工具"
            shortcut.save()
            
            # 开始菜单快捷方式
            start_menu = Path(os.environ.get('APPDATA')) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
            start_shortcut = start_menu / "Minecraft联机工具.lnk"
            shortcut2 = shell.CreateShortcut(str(start_shortcut))
            shortcut2.TargetPath = launcher_exe
            shortcut2.WorkingDirectory = self.target_dir
            shortcut2.IconLocation = launcher_exe
            shortcut2.Description = "MinecraftFRP 内网穿透工具"
            shortcut2.save()
        except Exception:
            pass


class InstallerWindow(QWidget):
    """安装程序主窗口 - 多页面向导"""
    
    def __init__(self, embedded_data_path=None, version="2.0.0"):
        super().__init__()
        self.embedded_data_path = embedded_data_path or self._detect_embedded_data()
        self.version = version
        self.install_thread = None
        self.current_page = 0
        self.init_ui()
        
    def _detect_embedded_data(self):
        """检测内嵌的安装数据"""
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
            data_path = os.path.join(base_dir, "install_data.zip")
            if os.path.exists(data_path):
                return data_path
        
        dev_data = os.path.join(os.getcwd(), "dist", "MinecraftFRP_package")
        if os.path.exists(dev_data):
            return dev_data
        
        return None
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("MinecraftFRP 安装向导")
        self.setFixedSize(600, 500)
        
        main_layout = QVBoxLayout()
        
        # 页面堆叠
        self.pages = QStackedWidget()
        
        # 欢迎页
        self.pages.addWidget(self._create_welcome_page())
        
        # 协议页
        self.pages.addWidget(self._create_license_page())
        
        # 安装配置页
        self.pages.addWidget(self._create_config_page())
        
        # 安装进度页
        self.pages.addWidget(self._create_progress_page())
        
        main_layout.addWidget(self.pages)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.back_btn = QPushButton("上一步")
        self.back_btn.setFixedSize(100, 35)
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setEnabled(False)
        btn_layout.addWidget(self.back_btn)
        
        self.next_btn = QPushButton("下一步")
        self.next_btn.setFixedSize(100, 35)
        self.next_btn.clicked.connect(self.go_next)
        btn_layout.addWidget(self.next_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedSize(100, 35)
        self.cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)
        
        if not self.embedded_data_path:
            QMessageBox.critical(self, "错误", "未找到安装数据！")
            self.next_btn.setEnabled(False)
    
    def _create_welcome_page(self):
        """创建欢迎页"""
        page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("欢迎使用 MinecraftFRP 安装向导")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        desc = QLabel(
            "MinecraftFRP 是一个专为 Minecraft 玩家设计的内网穿透工具。\n\n"
            "主要功能：\n"
            "• 快速端口映射，轻松开启联机\n"
            "• 智能节点选择，自动测速\n"
            "• 联机大厅系统，发现更多房间\n"
            "• 自动更新，保持最新版本\n\n"
            f"版本：{self.version}\n\n"
            "点击"下一步"继续安装。"
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignLeft)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        layout.addStretch()
        page.setLayout(layout)
        return page
    
    def _create_license_page(self):
        """创建协议页"""
        page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("用户许可协议")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 加载协议内容
        license_browser = QTextBrowser()
        license_browser.setOpenExternalLinks(True)
        
        license_path = Path(__file__).parent / "LICENSE.md"
        if license_path.exists():
            with open(license_path, 'r', encoding='utf-8') as f:
                license_browser.setMarkdown(f.read())
        else:
            license_browser.setPlainText("无法加载协议内容")
        
        layout.addWidget(license_browser)
        
        # 同意复选框
        self.agree_checkbox = QCheckBox("我已阅读并同意上述协议，特别是关于 FRPC 可能被杀毒软件误报的说明")
        self.agree_checkbox.stateChanged.connect(self._on_agree_changed)
        layout.addWidget(self.agree_checkbox)
        
        page.setLayout(layout)
        return page
    
    def _create_config_page(self):
        """创建安装配置页"""
        page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("选择安装位置")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        # 检查是否存在旧版本
        doc_path = Path.home() / "Documents" / "MitaHillFRP" / "install_info.json"
        default_path = str(Path.home() / "AppData" / "Local" / "MinecraftFRP")
        
        if doc_path.exists():
            try:
                with open(doc_path, 'r', encoding='utf-8') as f:
                    install_info = json.load(f)
                    old_path = install_info.get("install_path", "")
                    if old_path and os.path.exists(old_path):
                        default_path = old_path
                        
                        info_label = QLabel(
                            f"⚠️ 检测到已安装版本\n"
                            f"当前版本：{install_info.get('version', '未知')}\n"
                            f"安装路径：{old_path}\n\n"
                            "将执行覆盖安装"
                        )
                        info_label.setStyleSheet("color: orange; padding: 10px; background: #333; border-radius: 5px;")
                        layout.addWidget(info_label)
                        layout.addSpacing(10)
            except Exception:
                pass
        
        path_label = QLabel("安装位置：")
        layout.addWidget(path_label)
        
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setText(default_path)
        path_layout.addWidget(self.path_input)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_path)
        browse_btn.setFixedWidth(80)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)
        
        layout.addSpacing(20)
        
        # 快捷方式选项
        self.desktop_checkbox = QCheckBox("创建桌面快捷方式")
        self.desktop_checkbox.setChecked(True)
        layout.addWidget(self.desktop_checkbox)
        
        layout.addStretch()
        page.setLayout(layout)
        return page
    
    def _create_progress_page(self):
        """创建安装进度页"""
        page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("正在安装")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("准备安装...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        page.setLayout(layout)
        return page
    
    def _on_agree_changed(self, state):
        """协议同意状态改变"""
        # 在协议页时，只有同意才能下一步
        if self.current_page == 1:
            self.next_btn.setEnabled(state == Qt.CheckState.Checked.value)
    
    def go_back(self):
        """上一步"""
        if self.current_page > 0:
            self.current_page -= 1
            self.pages.setCurrentIndex(self.current_page)
            self._update_buttons()
    
    def go_next(self):
        """下一步"""
        # 协议页检查
        if self.current_page == 1 and not self.agree_checkbox.isChecked():
            QMessageBox.warning(self, "警告", "请先阅读并同意用户许可协议")
            return
        
        # 最后一页开始安装
        if self.current_page == 2:
            self.start_install()
            return
        
        if self.current_page < self.pages.count() - 1:
            self.current_page += 1
            self.pages.setCurrentIndex(self.current_page)
            self._update_buttons()
    
    def _update_buttons(self):
        """更新按钮状态"""
        self.back_btn.setEnabled(self.current_page > 0 and self.current_page < 3)
        
        if self.current_page == 1:
            self.next_btn.setEnabled(self.agree_checkbox.isChecked())
        elif self.current_page == 2:
            self.next_btn.setText("开始安装")
        elif self.current_page == 3:
            self.next_btn.setVisible(False)
            self.back_btn.setVisible(False)
            self.cancel_btn.setVisible(False)
        else:
            self.next_btn.setText("下一步")
            self.next_btn.setEnabled(True)
    
    def browse_path(self):
        """浏览安装路径"""
        path = QFileDialog.getExistingDirectory(self, "选择安装位置", str(Path(self.path_input.text()).parent))
        if path:
            full_path = os.path.join(path, "MinecraftFRP")
            self.path_input.setText(full_path)
    
    def start_install(self):
        """开始安装"""
        install_path = self.path_input.text().strip()
        
        if not install_path:
            QMessageBox.warning(self, "警告", "请选择安装位置")
            return
        
        # 切换到安装进度页
        self.current_page = 3
        self.pages.setCurrentIndex(self.current_page)
        self._update_buttons()
        
        # 启动安装线程
        self.install_thread = InstallThread(
            self.embedded_data_path, 
            install_path,
            self.version,
            self.desktop_checkbox.isChecked()
        )
        self.install_thread.progress.connect(self.on_progress)
        self.install_thread.finished.connect(self.on_finished)
        self.install_thread.start()
    
    def on_progress(self, value, message):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def on_finished(self, success, message):
        """安装完成"""
        self.progress_bar.setValue(100)
        
        if success:
            reply = QMessageBox.information(
                self, "安装完成", 
                f"{message}\n\n程序已安装到：\n{self.path_input.text()}\n\n是否立即启动？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                launcher_path = os.path.join(self.path_input.text(), "Launcher.exe")
                if os.path.exists(launcher_path):
                    import subprocess
                    subprocess.Popen([launcher_path])
            
            self.close()
        else:
            QMessageBox.critical(self, "安装失败", message)
            self.close()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = InstallerWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
