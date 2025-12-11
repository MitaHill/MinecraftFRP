# 主题样式
STYLE = {
    "light": """
QWidget{background:#f8f9fa;font-size:14px;font-family:'Microsoft YaHei';color:#000;}
QLabel{color:#495057;margin-bottom:8px;}
QPushButton{background:#4CAF50;color:#fff;padding:8px 16px;border:none;border-radius:4px;}
QPushButton:hover{background:#45a049;}
QLineEdit,QTextEdit,QSpinBox{background:#fff;border:1px solid #dee2e6;padding:8px;border-radius:4px;color:#000;selection-background-color:#0078d7;selection-color:#fff;}
QComboBox{
    min-width:150px;
    color: #212529;
    background-color: #ffffff;
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 4px;
}
QComboBox:on{
    border: 1px solid #4CAF50;
}
QComboBox QAbstractItemView {
    color: #212529;
    background-color: #ffffff;
    border: 1px solid #ced4da;
    selection-background-color: #e9ecef;
    selection-color: #212529;
}
QCheckBox{color:#000;spacing:5px;}
QCheckBox::indicator{width:16px;height:16px;border:1px solid #ced4da;border-radius:3px;background-color:#ffffff;}
QCheckBox::indicator:checked{background-color:#4CAF50;border:1px solid #4CAF50;}
QCheckBox::indicator:hover{border:1px solid #adb5bd;}
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
QTableView, QTableWidget {
    background-color: #ffffff;
    border: 1px solid #dee2e6;
    gridline-color: #dee2e6;
    color: #212529;
}
QHeaderView::section {
    background-color: #f1f3f5;
    color: #495057;
    padding: 4px;
    border: 1px solid #dee2e6;
}
QGroupBox {
    border: 1px solid #aaa;
    border-radius: 5px;
    margin-top: 2ex; /* leave space at the top for the title */
    color: #333;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left; /* position at the top center */
    padding: 0 3px;
    color: #333;
}
QGroupBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #ced4da;
    border-radius: 3px;
    background-color: #ffffff;
}
QGroupBox::indicator:checked {
    background-color: #4CAF50;
    border: 1px solid #4CAF50;
}
""",
    "dark": """
QWidget{background:#1e1e1e;font-size:14px;font-family:'Microsoft YaHei';color:#e0e0e0;}
QLabel{color:#b3b3b3;}
QPushButton{background:#333;color:#fff;padding:8px 16px;border:none;border-radius:4px;}
QPushButton:hover{background:#454545;}
QLineEdit,QTextEdit{background:#2d2d2d;border:1px solid #404040;padding:8px;border-radius:4px;color:#e0e0e0;}
QComboBox{min-width:150px;background-color:#2d2d2d;color:#e0e0e0;border:1px solid #404040;border-radius:4px;padding:4px;}
QComboBox:on{border:1px solid #4CAF50;}
QComboBox QAbstractItemView{background-color:#2d2d2d;color:#e0e0e0;border:1px solid #404040;selection-background-color:#454545;}
QCheckBox{color:#e0e0e0;spacing:5px;}
QCheckBox::indicator{width:16px;height:16px;border:1px solid #555;border-radius:3px;background-color:#2d2d2d;}
QCheckBox::indicator:checked{background-color:#4CAF50;border:1px solid #4CAF50;}
QCheckBox::indicator:hover{border:1px solid #777;}
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
QTableView, QTableWidget {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    gridline-color: #404040;
    color: #e0e0e0;
}
QHeaderView::section {
    background-color: #222222;
    color: #b3b3b3;
    padding: 4px;
    border: 1px solid #404040;
}
QGroupBox {
    border: 1px solid #555;
    border-radius: 5px;
    margin-top: 2ex;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 3px;
    color: #ddd;
}
""",
}