"""场景视图 — 背景插图 + 怪物悬浮层 + 半透明文字面板"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QProgressBar,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter


class MonsterFloat(QFrame):
    """怪物悬浮卡片 — 战斗中浮在文字面板上方"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self.setStyleSheet(
            "MonsterFloat { background: rgba(22,33,62,0.92); "
            "border: 2px solid #8b0000; border-radius: 10px; }"
        )
        self.setVisible(False)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(12, 6, 12, 6)
        self._layout.setSpacing(16)
        self._layout.addStretch()

        self._enemy_widgets: list[QFrame] = []

    def set_enemies(self, enemies: list[dict]) -> None:
        # 清除旧
        for w in self._enemy_widgets:
            self._layout.removeWidget(w)
            w.deleteLater()
        self._enemy_widgets.clear()

        for i, enemy in enumerate(enemies):
            card = QFrame()
            card.setFixedSize(170, 66)
            card.setStyleSheet(
                "QFrame { background: rgba(15,15,35,0.8); border: 1px solid #8b0000; "
                "border-radius: 8px; }"
            )
            cv = QVBoxLayout(card)
            cv.setContentsMargins(8, 4, 8, 4)
            cv.setSpacing(2)

            name = QLabel(f"{enemy['name']} [{enemy.get('tier', '')}]")
            name.setStyleSheet("font-size: 13px; font-weight: bold; color: #e63946;")

            bar = QProgressBar()
            bar.setRange(0, enemy["hp_max"])
            bar.setValue(enemy["hp_current"])
            bar.setFormat(f"HP {enemy['hp_current']}/{enemy['hp_max']}")
            bar.setFixedHeight(18)
            bar.setStyleSheet(
                "QProgressBar { border: 1px solid #4a3f35; border-radius: 2px; "
                "background: #0f0f23; font-size: 10px; color: #d4c5a9; } "
                "QProgressBar::chunk { background: #c0392b; border-radius: 1px; }"
            )

            cv.addWidget(name)
            cv.addWidget(bar)

            self._layout.addWidget(card)
            self._enemy_widgets.append(card)

        self._layout.addStretch()
        self.setVisible(len(enemies) > 0)

    def clear(self) -> None:
        self.set_enemies([])


class SceneView(QFrame):
    """全幅背景图 + 怪物悬浮层 + 半透明文字面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("scene_view")
        self.setMinimumWidth(400)
        self.setStyleSheet("SceneView { background: #0f0f23; border-radius: 6px; }")

        self._bg_pixmap: QPixmap | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 怪物悬浮层（战斗中）
        self.monster_float = MonsterFloat(self)
        layout.addWidget(self.monster_float)

        # 文字面板
        self.text_panel = QTextEdit()
        self.text_panel.setReadOnly(True)
        self.text_panel.setStyleSheet(
            "QTextEdit {"
            "  background: rgba(15, 15, 35, 0.85);"
            "  color: #d4c5a9;"
            "  border: 1px solid rgba(201, 169, 110, 0.3);"
            "  border-radius: 6px;"
            "  font-size: 14px;"
            "  padding: 12px;"
            "  selection-background-color: #c9a96e;"
            "  selection-color: #1a1a2e;"
            "}"
        )
        self.text_panel.setPlaceholderText("你的冒险从这里开始…\n\n点击「新游戏」或输入指令。")
        self.text_panel.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        layout.addWidget(self.text_panel, stretch=1)

        # 场景标题浮动标签
        self.scene_title = QLabel("", self)
        self.scene_title.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #c9a96e; "
            "background: rgba(15, 15, 35, 0.7); border-radius: 4px; padding: 4px 12px;"
        )
        self.scene_title.setVisible(False)

    def set_scene(self, scene_name: str, description: str) -> None:
        self.scene_title.setText(scene_name)
        self.scene_title.setVisible(True)
        self.scene_title.adjustSize()
        self.scene_title.move(16, 12)
        self.text_panel.setPlainText(description)

    def set_background(self, path: str) -> None:
        self._bg_pixmap = QPixmap(path)
        if self._bg_pixmap.isNull():
            self._bg_pixmap = None
        self.update()

    def append_text(self, text: str) -> None:
        self.text_panel.append(text)

    def set_text(self, text: str) -> None:
        self.text_panel.setPlainText(text)

    def paintEvent(self, event):
        if self._bg_pixmap:
            painter = QPainter(self)
            scaled = self._bg_pixmap.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation,
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            painter.end()
        super().paintEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.scene_title.isVisible():
            self.scene_title.move(16, 12)
