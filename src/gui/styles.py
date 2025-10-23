# 主题样式
STYLE = {
    "light": """
QWidget{background:#f8f9fa;font:14px 'Microsoft YaHei';}
QLabel{color:#495057;margin-bottom:8px;}
QPushButton{background:#4CAF50;color:#fff;padding:8px 16px;border:none;border-radius:4px;}
QPushButton:hover{background:#45a049;}
QLineEdit,QTextEdit{background:#fff;border:1px solid #dee2e6;padding:8px;border-radius:4px;}
QComboBox{min-width:150px;}
QTabBar::tab {
    background: white;
    color: black;
    padding: 8px;
    border: 1px solid #dee2e6;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background: #d0d0d0;
    color: black;
    border-bottom: 2px solid #4CAF50;
}
QTabBar::tab:hover {
    background: #f0f0f0;
}
QTabWidget::pane {
    background: #f8f9fa;
}
""",
    "dark": """
QWidget{background:#1e1e1e;font:14px 'Microsoft YaHei';color:#e0e0e0;}
QLabel{color:#b3b3b3;}
QPushButton{background:#fff;color:#333;padding:8px 16px;border:none;border-radius:4px;}
QPushButton:hover{background:#f0f0f0;}
QLineEdit,QTextEdit{background:#2d2d2d;border:1px solid #404040;padding:8px;border-radius:4px;color:#e0e0e0;}
QComboBox{min-width:150px;}
QTabBar::tab {
    background: black;
    color: white;
    padding: 8px;
    border: 1px solid #404040;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background: #444444;
    color: white;
    border-bottom: 2px solid #4CAF50;
}
QTabBar::tab:hover {
    background: #555555;
}
QTabWidget::pane {
    background: #1e1e1e;
}
""",
}