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
        clear_btn = QPushButton("Clear Logs")
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
        self.rule_input.setPlaceholderText("CIDR (1.2.3.0/24), Range (1.1.1.1-1.1.1.5), IP")
        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("Reason / Description")
        
        if self.mode == "whitelist":
            self.reason_input.setPlaceholderText("Description")
        
        add_btn = QPushButton(f"Add to {self.mode.title()}")
        add_btn.clicked.connect(self.add_rule)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        
        h.addWidget(QLabel("Rule:"))
        h.addWidget(self.rule_input)
        h.addWidget(QLabel("Info:"))
        h.addWidget(self.reason_input)
        h.addWidget(add_btn)
        h.addWidget(refresh_btn)
        layout.addLayout(h)
        
        # Table
        self.table = QTableWidget()
        cols = ["Rule", "Info", "Created At"]
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
            logger.info(f"Refreshing {self.mode} rules...")
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
            logger.info(f"Loaded {len(rules)} {self.mode} rules.")
        except Exception as e:
            logger.error(f"Failed to refresh {self.mode} rules: {e}")
            QMessageBox.warning(self, "Error", f"Failed to refresh: {e}")

    def add_rule(self):
        rule = self.rule_input.text().strip()
        reason = self.reason_input.text().strip()
        if not rule: return
        
        try:
            logger.info(f"Adding {self.mode} rule: {rule} ({reason})")
            if self.mode == "blacklist":
                AdminClient.add_blacklist(rule, reason)
            else:
                AdminClient.add_whitelist(rule, reason)
            self.rule_input.clear()
            self.reason_input.clear()
            self.refresh()
            logger.info(f"Successfully added rule: {rule}")
            QMessageBox.information(self, "Success", "Rule added.")
        except Exception as e:
            logger.error(f"Failed to add rule {rule}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add rule: {e}")

    def show_context_menu(self, pos):
        menu = QMenu(self)
        delete_action = QAction("Delete Rule", self)
        delete_action.triggered.connect(self.delete_selected)
        menu.addAction(delete_action)
        menu.exec(self.table.mapToGlobal(pos))
        
    def delete_selected(self):
        row = self.table.currentRow()
        if row < 0: return
        rule = self.table.item(row, 0).text()
        
        if QMessageBox.question(self, "Confirm", f"Delete rule {rule}?") != QMessageBox.Yes:
            return
            
        try:
            logger.info(f"Deleting {self.mode} rule: {rule}")
            if self.mode == "blacklist":
                AdminClient.remove_blacklist(rule)
            else:
                AdminClient.remove_whitelist(rule)
            self.refresh()
            logger.info(f"Successfully deleted rule: {rule}")
        except Exception as e:
            logger.error(f"Failed to delete rule {rule}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to delete: {e}")

class AccessLogsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        refresh_btn = QPushButton("Refresh Logs")
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn)
        
        self.table = QTableWidget()
        cols = ["IP", "Time", "Action"]
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
            QMessageBox.warning(self, "Error", f"Failed to fetch logs: {e}")

class AdminMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MinecraftFRP Admin Console")
        self.resize(1000, 700)
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Tabs
        self.blacklist_tab = RulesWidget("blacklist")
        self.whitelist_tab = RulesWidget("whitelist")
        self.logs_tab = AccessLogsWidget()
        self.local_log_tab = LocalLogWidget()
        
        self.tabs.addTab(self.blacklist_tab, "Blacklist (Block)")
        self.tabs.addTab(self.whitelist_tab, "Whitelist (Allow)")
        self.tabs.addTab(self.logs_tab, "Access Logs")
        self.tabs.addTab(self.local_log_tab, "Operation Logs")
        
        # Legacy Server Manager Tab
        self.server_tab = QWidget()
        v = QVBoxLayout(self.server_tab)
        lbl = QLabel("Manage Server List using legacy SSH tool")
        lbl.setAlignment(Qt.AlignCenter)
        btn = QPushButton("Open Server Manager")
        btn.clicked.connect(self.open_server_manager)
        v.addWidget(lbl)
        v.addWidget(btn)
        self.tabs.addTab(self.server_tab, "Server Nodes (SSH)")
        
        # Initial Refresh
        self.blacklist_tab.refresh()
        self.whitelist_tab.refresh()
        
    def open_server_manager(self):
        dialog = ServerManagementDialog(self)
        dialog.exec()
