"""全局 QSS 样式表 — 中古奇幻暗色调主题"""

MAIN_STYLE = """
/* ===== 全局 ===== */
QWidget {
    background-color: #1a1a2e;
    color: #d4c5a9;
    font-family: "Microsoft YaHei", "SimHei", sans-serif;
    font-size: 14px;
}

/* ===== 菜单栏 ===== */
QMenuBar {
    background-color: #16213e;
    color: #d4c5a9;
    padding: 2px;
    border-bottom: 2px solid #c9a96e;
}
QMenuBar::item:selected {
    background-color: #c9a96e;
    color: #1a1a2e;
}
QMenu {
    background-color: #16213e;
    color: #d4c5a9;
    border: 1px solid #c9a96e;
}
QMenu::item:selected {
    background-color: #c9a96e;
    color: #1a1a2e;
}

/* ===== 面板 ===== */
QLabel {
    background: transparent;
    color: #d4c5a9;
}
QLabel#title {
    font-size: 18px;
    font-weight: bold;
    color: #c9a96e;
}
QLabel#subtitle {
    font-size: 13px;
    color: #8b7d6b;
}

/* ===== 按钮 ===== */
QPushButton {
    background-color: #0f3460;
    color: #d4c5a9;
    border: 1px solid #c9a96e;
    border-radius: 4px;
    padding: 6px 14px;
    font-size: 14px;
}
QPushButton:hover {
    background-color: #1a4a7a;
}
QPushButton:pressed {
    background-color: #c9a96e;
    color: #1a1a2e;
}
QPushButton#danger {
    background-color: #8b0000;
    border-color: #ff4444;
}
QPushButton#primary {
    background-color: #2d5a27;
    border-color: #4caf50;
}

/* ===== 输入框 ===== */
QLineEdit {
    background-color: #0f0f23;
    color: #e8d5b0;
    border: 2px solid #4a3f35;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 15px;
    selection-background-color: #c9a96e;
    selection-color: #1a1a2e;
}
QLineEdit:focus {
    border-color: #c9a96e;
}

/* ===== 文本区域/日志 ===== */
QTextEdit, QPlainTextEdit {
    background-color: #0f0f23;
    color: #c0b090;
    border: 1px solid #4a3f35;
    border-radius: 4px;
    font-family: "Microsoft YaHei", "SimHei", monospace;
    font-size: 13px;
    padding: 6px;
}
QTextEdit:focus {
    border-color: #c9a96e;
}

/* ===== 滚动条 ===== */
QScrollBar:vertical {
    background-color: #16213e;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background-color: #4a3f35;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background-color: #c9a96e;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ===== 进度条(HP/MP) ===== */
QProgressBar {
    border: 1px solid #4a3f35;
    border-radius: 3px;
    text-align: center;
    font-size: 11px;
    background-color: #0f0f23;
    height: 16px;
}
QProgressBar::chunk {
    border-radius: 2px;
}
QProgressBar#hp_bar::chunk {
    background-color: #c0392b;
}
QProgressBar#mp_bar::chunk {
    background-color: #2980b9;
}

/* ===== 标签页 ===== */
QTabWidget::pane {
    border: 1px solid #4a3f35;
    background-color: #1a1a2e;
}
QTabBar::tab {
    background-color: #16213e;
    color: #8b7d6b;
    padding: 6px 16px;
    border: 1px solid #4a3f35;
    border-bottom: none;
}
QTabBar::tab:selected {
    background-color: #1a1a2e;
    color: #c9a96e;
    border-bottom: 2px solid #c9a96e;
}

/* ===== 弹窗 ===== */
QDialog {
    background-color: #1a1a2e;
    border: 2px solid #c9a96e;
}

/* ===== 列表控件 ===== */
QListWidget, QTableWidget {
    background-color: #0f0f23;
    color: #d4c5a9;
    border: 1px solid #4a3f35;
    alternate-background-color: #16213e;
}
QListWidget::item:selected, QTableWidget::item:selected {
    background-color: #c9a96e;
    color: #1a1a2e;
}

/* ===== 分组框 ===== */
QGroupBox {
    border: 1px solid #4a3f35;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 10px;
    color: #c9a96e;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
}
"""
