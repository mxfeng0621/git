"""主窗口 — 骨架布局"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QSplitter,
    QMenuBar, QMenu, QMessageBox, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from app.styles import MAIN_STYLE


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("龙焰传说 — DND文字冒险")
        self.resize(1280, 800)
        self.setMinimumSize(960, 600)
        self.setStyleSheet(MAIN_STYLE)

        # 引擎
        from core.engine import GameEngine
        self.engine = GameEngine()
        self.engine.on_message = self._engine_message

        self._build_menu_bar()
        self._build_central()
        self._build_status_bar()
        self._build_status_bar()

    # ---------- 菜单栏 ----------
    def _build_menu_bar(self) -> None:
        bar = self.menuBar()

        game_menu = bar.addMenu("游戏(&G)")
        game_menu.addAction(QAction("新游戏(&N)", self, triggered=self._on_new_game))
        game_menu.addAction(QAction("存档(&S)", self, triggered=self._on_save))
        game_menu.addAction(QAction("读档(&L)", self, triggered=self._on_load))
        game_menu.addSeparator()
        game_menu.addAction(QAction("退出(&Q)", self, triggered=self.close))

        help_menu = bar.addMenu("帮助(&H)")
        help_menu.addAction(QAction("关于(&A)", self, triggered=self._on_about))

    # ---------- 中央区域 ----------
    def _build_central(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(4)

        # ---- 上部：队伍面板 + 场景视图 + 操作区 ----
        top_splitter = QSplitter(Qt.Horizontal)

        # 队伍面板
        self.party_panel = self._build_party_panel()
        top_splitter.addWidget(self.party_panel)

        # 场景视图
        self.scene_view = self._build_scene_view()
        top_splitter.addWidget(self.scene_view)

        # 操作区
        self.action_panel = self._build_action_panel()
        top_splitter.addWidget(self.action_panel)

        top_splitter.setSizes([240, 640, 200])
        root.addWidget(top_splitter, stretch=3)

        # ---- 下部：消息日志 + 命令输入 ----
        bottom_splitter = QSplitter(Qt.Vertical)

        self.log_panel = self._build_log_panel()
        bottom_splitter.addWidget(self.log_panel)

        self.cmd_input = self._build_command_input()
        bottom_splitter.addWidget(self.cmd_input)

        bottom_splitter.setSizes([200, 40])
        root.addWidget(bottom_splitter, stretch=1)

    # ---------- 面板组件 ----------
    def _build_party_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("party_panel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)

        title = QLabel("冒险小队")
        title.setObjectName("title")
        layout.addWidget(title)

        # 4个成员占位
        for i in range(4):
            slot = QFrame()
            slot.setFrameStyle(QFrame.Box)
            slot_layout = QVBoxLayout(slot)
            slot_layout.setContentsMargins(4, 2, 4, 2)

            name = QLabel(f"队员 {i + 1}")
            name.setStyleSheet("font-weight: bold;")
            slot_layout.addWidget(name)

            cls = QLabel("—")
            cls.setObjectName("subtitle")
            slot_layout.addWidget(cls)

            hp = QLabel("HP: —/—  MP: —/—")
            hp.setStyleSheet("font-size: 11px;")
            slot_layout.addWidget(hp)

            layout.addWidget(slot)

        layout.addStretch()
        return frame

    def _build_scene_view(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("scene_view")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)

        # 插图占位
        img_placeholder = QLabel()
        img_placeholder.setFixedHeight(220)
        img_placeholder.setAlignment(Qt.AlignCenter)
        img_placeholder.setText("[ 场景插图 ]")
        img_placeholder.setStyleSheet(
            "background-color: #0f0f23; border: 1px dashed #4a3f35; "
            "color: #4a3f35; font-size: 16px;"
        )
        layout.addWidget(img_placeholder)

        # 场景描述
        self.scene_text = QTextEdit()
        self.scene_text.setReadOnly(True)
        self.scene_text.setMaximumHeight(160)
        self.scene_text.setPlainText(
            "欢迎来到龙焰传说。\n\n"
            "一个基于龙与地下城规则的文字冒险世界等待着你。\n"
            "点击「游戏 → 新游戏」开始你的冒险，或「读档」继续之前的旅程。"
        )
        layout.addWidget(self.scene_text)

        return frame

    def _build_action_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("action_panel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        title = QLabel("操作")
        title.setObjectName("title")
        layout.addWidget(title)

        for text in ("探索", "休息", "背包", "地图", "任务", "策略"):
            btn = QPushButton(text)
            btn.setEnabled(False)
            layout.addWidget(btn)

        layout.addStretch()
        return frame

    def _build_log_panel(self) -> QTextEdit:
        log = QTextEdit()
        log.setReadOnly(True)
        log.setPlaceholderText("消息日志…")
        log.append("[系统] 游戏启动完毕。")
        return log

    def _build_command_input(self) -> QLineEdit:
        inp = QLineEdit()
        inp.setPlaceholderText("输入指令…（例如：帮助）")
        inp.returnPressed.connect(lambda: self._on_command(inp))
        return inp

    # ---------- 状态栏 ----------
    def _build_status_bar(self) -> None:
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")

    # ---------- 槽函数 ----------
    def _on_new_game(self) -> None:
        result = self.engine.new_game()
        self.log_panel.append(f"[系统] {result.text}")

    def _on_save(self) -> None:
        result = self.engine.save_game(1)
        self.log_panel.append(f"[系统] {result.text}")

    def _on_load(self) -> None:
        result = self.engine.load_game(1)
        self.log_panel.append(f"[系统] {result.text}")

    def _on_about(self) -> None:
        QMessageBox.about(self, "关于龙焰传说",
                          "龙焰传说 v0.3\n\n"
                          "基于 D&D 规则的文字冒险游戏。\n"
                          "PySide6 + SQLite 构建。")

    def _engine_message(self, text: str, category) -> None:
        self.log_panel.append(f"[{category.value}] {text}")

    def _on_command(self, inp: QLineEdit) -> None:
        text = inp.text().strip()
        if not text:
            return
        self.log_panel.append(f"> {text}")
        inp.clear()
        cmd = self.engine.parser.parse(text)
        result = self.engine.execute(cmd)
        if result.text:
            for line in result.text.split("\n"):
                self.log_panel.append(line)
        if result.combat_events:
            for ev in result.combat_events:
                line = ev.to_log_line()
                if line.strip():
                    self.log_panel.append(f"  {line}")
