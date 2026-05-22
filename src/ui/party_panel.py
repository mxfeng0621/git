"""队伍面板 — 4人状态条 + 策略标签"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QSizePolicy,
)
from PySide6.QtCore import Qt

from utils.constants import StrategyType


class MemberSlot(QFrame):
    """单个队员槽位"""

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self.setFrameStyle(QFrame.Box)
        self.setMinimumHeight(90)
        self.setStyleSheet("MemberSlot { background: #16213e; border: 1px solid #4a3f35; "
                           "border-radius: 4px; padding: 4px; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)

        # 名字 + 等级
        top = QHBoxLayout()
        self.name_label = QLabel(f"队员 {index + 1}")
        self.name_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #d4c5a9;")
        top.addWidget(self.name_label)

        self.level_label = QLabel("Lv.1")
        self.level_label.setStyleSheet("font-size: 11px; color: #8b7d6b;")
        self.level_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        top.addWidget(self.level_label)
        layout.addLayout(top)

        # 种族职业
        self.class_label = QLabel("—")
        self.class_label.setStyleSheet("font-size: 11px; color: #8b7d6b;")
        layout.addWidget(self.class_label)

        # HP条
        hp_row = QHBoxLayout()
        hp_row.addWidget(QLabel("HP", styleSheet="font-size:10px; color:#c0392b;"))
        self.hp_bar = QProgressBar()
        self.hp_bar.setObjectName("hp_bar")
        self.hp_bar.setRange(0, 100)
        self.hp_bar.setValue(100)
        self.hp_bar.setTextVisible(True)
        self.hp_bar.setFormat("%v/%m")
        self.hp_bar.setFixedHeight(16)
        self.hp_bar.setStyleSheet(
            "QProgressBar#hp_bar { border: 1px solid #4a3f35; border-radius: 2px; "
            "background: #0f0f23; font-size: 9px; color: #d4c5a9; } "
            "QProgressBar#hp_bar::chunk { background: #c0392b; border-radius: 1px; }"
        )
        hp_row.addWidget(self.hp_bar)
        layout.addLayout(hp_row)

        # MP条
        mp_row = QHBoxLayout()
        mp_row.addWidget(QLabel("MP", styleSheet="font-size:10px; color:#2980b9;"))
        self.mp_bar = QProgressBar()
        self.mp_bar.setObjectName("mp_bar")
        self.mp_bar.setRange(0, 100)
        self.mp_bar.setValue(100)
        self.mp_bar.setTextVisible(True)
        self.mp_bar.setFormat("%v/%m")
        self.mp_bar.setFixedHeight(14)
        self.mp_bar.setStyleSheet(
            "QProgressBar#mp_bar { border: 1px solid #4a3f35; border-radius: 2px; "
            "background: #0f0f23; font-size: 9px; color: #d4c5a9; } "
            "QProgressBar#mp_bar::chunk { background: #2980b9; border-radius: 1px; }"
        )
        mp_row.addWidget(self.mp_bar)
        layout.addLayout(mp_row)

        # 策略标签
        self.strategy_label = QLabel("—")
        self.strategy_label.setStyleSheet(
            "font-size: 10px; color: #c9a96e; background: #0f0f23; "
            "border-radius: 2px; padding: 1px 4px;"
        )
        self.strategy_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.strategy_label)

    def set_character(self, name: str, level: int, race_name: str, class_name: str,
                      hp_cur: int, hp_max: int, mp_cur: int, mp_max: int,
                      strategy: str = "") -> None:
        self.name_label.setText(name)
        self.level_label.setText(f"Lv.{level}")
        self.class_label.setText(f"{race_name} · {class_name}")
        self.hp_bar.setRange(0, hp_max)
        self.hp_bar.setValue(hp_cur)
        self.hp_bar.setFormat(f"{hp_cur}/{hp_max}")
        self.mp_bar.setRange(0, mp_max)
        self.mp_bar.setValue(mp_cur)
        self.mp_bar.setFormat(f"{mp_cur}/{mp_max}")
        if strategy:
            self.strategy_label.setText(strategy)
        self.setVisible(True)

    def set_empty(self) -> None:
        self.name_label.setText(f"队员 {self.index + 1}")
        self.level_label.setText("—")
        self.class_label.setText("（空）")
        self.hp_bar.setRange(0, 1)
        self.hp_bar.setValue(0)
        self.hp_bar.setFormat("—/—")
        self.mp_bar.setRange(0, 1)
        self.mp_bar.setValue(0)
        self.mp_bar.setFormat("—/—")
        self.strategy_label.setText("—")

    def update_hp_mp(self, hp_cur: int, hp_max: int, mp_cur: int, mp_max: int) -> None:
        self.hp_bar.setRange(0, hp_max)
        self.hp_bar.setValue(hp_cur)
        self.hp_bar.setFormat(f"{hp_cur}/{hp_max}")
        self.mp_bar.setRange(0, mp_max)
        self.mp_bar.setValue(mp_cur)
        self.mp_bar.setFormat(f"{mp_cur}/{mp_max}")

    def set_strategy(self, strategy: str) -> None:
        self.strategy_label.setText(strategy)


class PartyPanel(QFrame):
    """队伍面板容器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("party_panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        title = QLabel("冒险小队")
        title.setObjectName("title")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #c9a96e;")
        layout.addWidget(title)

        self.slots: list[MemberSlot] = []
        for i in range(4):
            slot = MemberSlot(i)
            slot.set_empty()
            self.slots.append(slot)
            layout.addWidget(slot)

        layout.addStretch()

    def refresh(self, party, combat=None) -> None:
        """从 Party 对象刷新所有槽位"""
        from core.party import Party
        for i, slot in enumerate(self.slots):
            member = party.members[i] if i < len(party.members) else None
            if member:
                strategy = ""
                if combat:
                    strat = combat.get_strategy(i)
                    strategy = strat.value
                slot.set_character(
                    name=member.name,
                    level=member.level,
                    race_name=member.race_name,
                    class_name=member.class_name,
                    hp_cur=member.hp_current,
                    hp_max=member.hp_max,
                    mp_cur=member.mp_current,
                    mp_max=member.mp_max,
                    strategy=strategy,
                )
            else:
                slot.set_empty()
