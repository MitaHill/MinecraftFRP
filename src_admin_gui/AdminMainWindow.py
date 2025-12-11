from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QTabWidget, QPushButton, QTableWidget, QTableWidgetItem, 
                               QLineEdit, QLabel, QInputDialog, QMessageBox, QHeaderView, QMenu,
                               QPlainTextEdit, QCheckBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont
import logging
from src_admin_gui.AdminClient import AdminClient
from src_admin_gui.ServerManagementDialog import ServerManagementDialog
from src_admin_gui.LogManager import get_logger
from src_admin_gui.QtSignalHandler import QtSignalHandler
from src_admin_gui.OnlineUsersWidget import OnlineUsersWidget

logger = get_logger()

class LocalLogWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_logging()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Tools
        h = QHBoxLayout()
        clear_btn = QPushButton("清空日志 (Clear Logs)")
        clear_btn.clicked.connect(self.clear_logs)
        h.addWidget(clear_btn)
        h.addStretch()
        layout.addLayout(h)
        
        self.log_area = QPlainTextEdit()
        self.log_area.setReadOnly(True)
        # Monospace font for logs
        font = QFont("Consolas", 9)
        if not font.exactMatch():
            font = QFont("Courier New", 9)
        self.log_area.setFont(font)
        layout.addWidget(self.log_area)
        
    def setup_logging(self):
        # Create handler
        self.handler = QtSignalHandler()
        self.handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.handler.log_record.connect(self.append_log)
        
        # Add to root logger to capture everything
        logging.getLogger().addHandler(self.handler)
        # Also ensure our specific logger has it (though root should cover it)
        logger.addHandler(self.handler)
        
    def append_log(self, msg):
        self.log_area.appendPlainText(msg)
        # Auto scroll
        sb = self.log_area.verticalScrollBar()
        sb.setValue(sb.maximum())
        
    def clear_logs(self):
        self.log_area.clear()

class RulesWidget(QWidget):
    def __init__(self, mode="blacklist"):
        super().__init__()
        self.mode = mode
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Controls
        h = QHBoxLayout()
        self.rule_input = QLineEdit()
        self.rule_input.setPlaceholderText("CIDR (1.2.3.0/24), IP范围 (1.1.1.1-1.1.1.5), IP")
        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("封禁原因 / 备注 (Reason)")
        
        if self.mode == "whitelist":
            self.reason_input.setPlaceholderText("备注 (Description)")
        
        btn_text = "添加到黑名单" if self.mode == "blacklist" else "添加到白名单"
        add_btn = QPushButton(btn_text)
        add_btn.clicked.connect(self.add_rule)
        
        refresh_btn = QPushButton("刷新 (Refresh)")
        refresh_btn.clicked.connect(self.refresh)
        
        h.addWidget(QLabel("规则 (Rule):"))
        h.addWidget(self.rule_input)
        h.addWidget(QLabel("信息 (Info):"))
        h.addWidget(self.reason_input)
        h.addWidget(add_btn)
        h.addWidget(refresh_btn)
        layout.addLayout(h)
        
        # Table
        self.table = QTableWidget()
        cols = ["规则 (Rule)", "信息 (Info)", "创建时间 (Created At)"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)
        
        # Context Menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
    def refresh(self):
        try:
            logger.info(f"刷新 {self.mode} 规则...")
            if self.mode == "blacklist":
                rules = AdminClient.get_blacklist()
            else:
                rules = AdminClient.get_whitelist()
                
            self.table.setRowCount(0)
            for r in rules:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(r.get('rule', ''))))
                desc = r.get('reason') if self.mode == 'blacklist' else r.get('description')
                self.table.setItem(row, 1, QTableWidgetItem(str(desc)))
                self.table.setItem(row, 2, QTableWidgetItem(str(r.get('created_at', ''))))
            logger.info(f"加载了 {len(rules)} 条 {self.mode} 规则。")
        except Exception as e:
            logger.error(f"刷新 {self.mode} 规则失败: {e}")
            QMessageBox.warning(self, "错误", f"刷新失败: {e}")

    def add_rule(self):
        rule = self.rule_input.text().strip()
        reason = self.reason_input.text().strip()
        if not rule: return
        
        try:
            logger.info(f"添加 {self.mode} 规则: {rule} ({reason})")
            if self.mode == "blacklist":
                AdminClient.add_blacklist(rule, reason)
            else:
                AdminClient.add_whitelist(rule, reason)
            self.rule_input.clear()
            self.reason_input.clear()
            self.refresh()
            logger.info(f"成功添加规则: {rule}")
            QMessageBox.information(self, "成功", "规则已添加。")
        except Exception as e:
            logger.error(f"添加规则 {rule} 失败: {e}")
            QMessageBox.critical(self, "错误", f"添加规则失败: {e}")

    def show_context_menu(self, pos):
        menu = QMenu(self)
        delete_action = QAction("删除规则 (Delete)", self)
        delete_action.triggered.connect(self.delete_selected)
        menu.addAction(delete_action)
        menu.exec(self.table.mapToGlobal(pos))
        
    def delete_selected(self):
        row = self.table.currentRow()
        if row < 0: return
        rule = self.table.item(row, 0).text()
        
        if QMessageBox.question(self, "确认", f"确定要删除规则 {rule} 吗?") != QMessageBox.Yes:
            return
            
        try:
            logger.info(f"正在删除 {self.mode} 规则: {rule}")
            if self.mode == "blacklist":
                AdminClient.remove_blacklist(rule)
            else:
                AdminClient.remove_whitelist(rule)
            self.refresh()
            logger.info(f"成功删除规则: {rule}")
        except Exception as e:
            logger.error(f"删除规则 {rule} 失败: {e}")
            QMessageBox.critical(self, "错误", f"删除失败: {e}")

class AccessLogsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        refresh_btn = QPushButton("刷新日志 (Refresh Logs)")
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn)
        
        self.table = QTableWidget()
        cols = ["IP地址", "时间 (Time)", "操作 (Action)"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        
    def refresh(self):
        try:
            logs = AdminClient.get_access_logs()
            self.table.setRowCount(0)
            from datetime import datetime
            for log in logs:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(log.get('client_ip', ''))))
                ts = log.get('timestamp', 0)
                time_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                self.table.setItem(row, 1, QTableWidgetItem(time_str))
                self.table.setItem(row, 2, QTableWidgetItem(str(log.get('action', ''))))
        except Exception as e:
            QMessageBox.warning(self, "错误", f"获取日志失败: {e}")

class AdminMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MinecraftFRP 管理控制台 (Admin Console)")
        self.resize(1000, 700)
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Tabs
        self.online_users_tab = OnlineUsersWidget()
        self.blacklist_tab = RulesWidget("blacklist")
        self.whitelist_tab = RulesWidget("whitelist")
        self.logs_tab = AccessLogsWidget()
        self.local_log_tab = LocalLogWidget()
        
        self.tabs.addTab(self.online_users_tab, "在线用户 (Online)")
        self.tabs.addTab(self.blacklist_tab, "黑名单 (Blacklist)")
        self.tabs.addTab(self.whitelist_tab, "白名单 (Whitelist)")
        self.tabs.addTab(self.logs_tab, "访问日志 (Access Logs)")
        self.tabs.addTab(self.local_log_tab, "操作日志 (Local Logs)")
        
        # Legacy Server Manager Tab
        self.server_tab = QWidget()
        v = QVBoxLayout(self.server_tab)
        lbl = QLabel("请使用旧版SSH工具管理服务器列表节点")
        lbl.setAlignment(Qt.AlignCenter)
        btn = QPushButton("打开服务器列表管理器")
        btn.clicked.connect(self.open_server_manager)
        v.addWidget(lbl)
        v.addWidget(btn)
        self.tabs.addTab(self.server_tab, "节点管理 (Nodes)")
        
        # Initial Refresh
        self.blacklist_tab.refresh()
        self.whitelist_tab.refresh()
        self.online_users_tab.refresh()
        
    def open_server_manager(self):
        dialog = ServerManagementDialog(self)
        dialog.exec()
