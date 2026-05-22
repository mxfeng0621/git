"""队伍面板 — 底部队员横排卡片（等宽填满+羊皮纸风格+AI预留头像）"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QPainter, QBrush, QColor, QFont, QMouseEvent

from core.party import Party
from core.character import Character

# ---- 羊皮纸风格色板 ----
PARCH_BG = "#2c1810"           # 深木色底
PARCH_CARD = "#3e2216"         # 卡片底色
PARCH_BORDER = "#8b6914"       # 古铜边框
PARCH_GOLD = "#c9a96e"         # 金色文字
PARCH_TEXT = "#e8d5b0"         # 奶油色正文
PARCH_ACCENT = "#a0522d"       # 赤陶色强调

CLASS_COLORS = {
    "warrior": "#c0392b", "mage": "#8e44ad", "rogue": "#27ae60",
    "cleric": "#d4ac0d", "ranger": "#2e86c1",
}
CLASS_SYMBOLS = {"warrior": "⚔️", "mage": "🔮", "rogue": "🗡️", "cleric": "✨", "ranger": "🏹"}
RACE_SYMBOLS = {"human": "🧑", "elf": "🧝", "dwarf": "🧔", "halfling": "👤"}


class PortraitWidget(QLabel):
    """圆形头像 — emoji + 职业色边框"""

    def __init__(self, size: int = 56, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self._icon = ""
        self._color = PARCH_BORDER
        self._draw()

    def set_placeholder(self, race_id: str, class_id: str) -> None:
        self._icon = RACE_SYMBOLS.get(race_id, "🧑")
        self._color = CLASS_COLORS.get(class_id, PARCH_BORDER)
        self._draw()

    def _draw(self) -> None:
        pix = QPixmap(self._size, self._size)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)

        # 外圈职业色
        p.setBrush(QBrush(QColor(PARCH_CARD)))
        p.setPen(QColor(self._color))
        p.drawEllipse(2, 2, self._size - 4, self._size - 4)

        # 内圈装饰
        p.setPen(QColor(PARCH_BORDER))
        p.drawEllipse(6, 6, self._size - 12, self._size - 12)

        # emoji
        if self._icon:
            p.setFont(QFont("Segoe UI Emoji", self._size // 3 + 2))
            p.setPen(QColor(PARCH_TEXT))
            p.drawText(0, 0, self._size, self._size, Qt.AlignCenter, self._icon)

        p.end()
        self.setPixmap(pix)


class MemberCard(QWidget):
    """单队员卡片 — 羊皮纸风格"""
    clicked = Signal(int)

    def __init__(self, index: int = 0, parent=None):
        super().__init__(parent)
        self._index = index
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(160)
        self.setMaximumHeight(175)
        self.setCursor(Qt.PointingHandCursor)

        self.setStyleSheet(f"""
            MemberCard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {PARCH_CARD}, stop:1 #2a180e);
                border: 1px solid {PARCH_BORDER};
                border-radius: 8px;
                margin: 2px 4px;
            }}
            MemberCard:hover {{
                border: 2px solid {PARCH_GOLD};
                margin: 1px 3px;
            }}
        """)

        main = QHBoxLayout(self)
        main.setContentsMargins(12, 10, 14, 10)
        main.setSpacing(12)

        # === 左: 头像 ===
        self.portrait = PortraitWidget(56)
        main.addWidget(self.portrait)

        # === 中: 信息 ===
        center = QVBoxLayout()
        center.setSpacing(2)

        # 名字 + 等级
        top_row = QHBoxLayout()
        self.name_lbl = QLabel("(空)")
        self.name_lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {PARCH_TEXT};")
        top_row.addWidget(self.name_lbl)
        top_row.addStretch()
        self.level_lbl = QLabel("")
        self.level_lbl.setStyleSheet(f"font-size: 12px; color: {PARCH_GOLD}; font-weight: bold;")
        top_row.addWidget(self.level_lbl)
        center.addLayout(top_row)

        # 种族职业
        self.class_lbl = QLabel("")
        self.class_lbl.setStyleSheet(f"font-size: 11px; color: #9a8468;")
        center.addWidget(self.class_lbl)

        center.addSpacing(4)

        # HP条
        self.hp_bar = QProgressBar()
        self.hp_bar.setFixedHeight(14)
        self.hp_bar.setTextVisible(True)
        self.hp_bar.setFormat("HP %v/%m")
        self.hp_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {PARCH_BORDER}; border-radius: 3px;
                background: #1a0f08; font-size: 10px; color: {PARCH_TEXT};
            }}
            QProgressBar::chunk {{ background: #8b0000; border-radius: 2px; }}
        """)
        center.addWidget(self.hp_bar)

        # MP条
        self.mp_bar = QProgressBar()
        self.mp_bar.setFixedHeight(12)
        self.mp_bar.setTextVisible(True)
        self.mp_bar.setFormat("MP %v/%m")
        self.mp_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {PARCH_BORDER}; border-radius: 3px;
                background: #1a0f08; font-size: 10px; color: {PARCH_TEXT};
            }}
            QProgressBar::chunk {{ background: #1a5276; border-radius: 2px; }}
        """)
        center.addWidget(self.mp_bar)

        # 策略标签
        self.strat_lbl = QLabel("")
        self.strat_lbl.setStyleSheet(f"font-size: 10px; color: {PARCH_GOLD};")
        center.addWidget(self.strat_lbl)

        main.addLayout(center, stretch=1)

        # === 右: 职业图标 ===
        self.class_icon = QLabel("")
        self.class_icon.setFixedWidth(36)
        self.class_icon.setStyleSheet(f"font-size: 28px; color: {PARCH_GOLD};")
        self.class_icon.setAlignment(Qt.AlignCenter)
        main.addWidget(self.class_icon)

    def set_member(self, char: Character | None, strategy: str = "") -> None:
        if char is None:
            self.name_lbl.setText("(空位)")
            self.level_lbl.setText("")
            self.class_lbl.setText("招募同伴加入")
            self.class_icon.setText("❓")
            self.hp_bar.setVisible(False)
            self.mp_bar.setVisible(False)
            self.strat_lbl.setText("")
            self.portrait._icon = ""
            self.portrait._draw()
            self.setStyleSheet(self.styleSheet().replace(
                f"border: 2px solid {PARCH_GOLD}", ""))
            return

        self.name_lbl.setText(char.name)
        self.level_lbl.setText(f"Lv.{char.level}")
        self.class_lbl.setText(f"{char.race_name} · {char.class_name}")
        self.class_icon.setText(CLASS_SYMBOLS.get(char.class_id, "⚔️"))

        self.hp_bar.setVisible(True)
        self.hp_bar.setRange(0, char.hp_max)
        self.hp_bar.setValue(char.hp_current)
        self.hp_bar.setFormat(f"HP {char.hp_current}/{char.hp_max}")

        # HP颜色: 绿/黄/红
        pct = char.hp_current / max(char.hp_max, 1)
        hp_color = "#27ae60" if pct > 0.6 else ("#d4ac0d" if pct > 0.3 else "#8b0000")
        self.hp_bar.setStyleSheet(self.hp_bar.styleSheet().split(
            "QProgressBar::chunk")[0] +
            f"QProgressBar::chunk {{ background: {hp_color}; border-radius: 2px; }}")

        self.mp_bar.setVisible(True)
        self.mp_bar.setRange(0, char.mp_max)
        self.mp_bar.setValue(char.mp_current)
        self.mp_bar.setFormat(f"MP {char.mp_current}/{char.mp_max}")

        self.strat_lbl.setText(f"🎯 {strategy}" if strategy else "")
        self.portrait.set_placeholder(char.race_id, char.class_id)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.clicked.emit(self._index)
        super().mousePressEvent(event)


class PartyPanel(QWidget):
    """底部队员横排 — 等宽填满"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(175)
        self.setMaximumHeight(190)
        self.setStyleSheet("PartyPanel { background: transparent; }")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 2, 2)
        layout.setSpacing(0)
        self.cards = [MemberCard(i) for i in range(4)]
        for c in self.cards:
            layout.addWidget(c, stretch=1)

    def refresh(self, party: Party, combat=None) -> None:
        for i, card in enumerate(self.cards):
            char = party.get(i)
            strat = combat.get_strategy(i).value if combat and char else ""
            card.set_member(char, strat)
