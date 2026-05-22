"""战斗界面 — 策略面板 + 敌人信息"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QGroupBox, QProgressBar,
)
from PySide6.QtCore import Qt, Signal

from utils.constants import StrategyType


class CombatWidget(QFrame):
    strategy_changed = Signal(int, str)    # member_index, strategy_name
    round_requested = Signal()             # 请求执行下一回合
    flee_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("combat_widget")
        self.setStyleSheet(
            "CombatWidget { background: #1a1124; border: 2px solid #8b0000; "
            "border-radius: 6px; padding: 8px; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 标题
        title = QLabel("⚔ 战斗中")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e63946;")
        layout.addWidget(title)

        # 敌人信息
        self.enemy_group = QGroupBox("敌方")
        self.enemy_group.setStyleSheet(
            "QGroupBox { color: #e63946; font-weight: bold; border: 1px solid #4a3f35; "
            "border-radius: 4px; margin-top: 8px; padding-top: 12px; }"
        )
        self.enemy_layout = QVBoxLayout(self.enemy_group)
        self.enemy_bars: list[tuple[QLabel, QProgressBar]] = []
        layout.addWidget(self.enemy_group)

        # 策略区
        strat_group = QGroupBox("战斗策略")
        strat_group.setStyleSheet(
            "QGroupBox { color: #c9a96e; font-weight: bold; border: 1px solid #4a3f35; "
            "border-radius: 4px; margin-top: 8px; padding-top: 12px; }"
        )
        strat_layout = QVBoxLayout(strat_group)
        self.strategy_combos: list[QComboBox] = []
        for i in range(4):
            row = QHBoxLayout()
            lbl = QLabel(f"队员 {i+1}")
            lbl.setStyleSheet("font-size: 12px; color: #d4c5a9; min-width: 50px;")
            row.addWidget(lbl)
            combo = QComboBox()
            combo.addItems([s.value for s in StrategyType])
            combo.setCurrentIndex(1)  # 默认平衡输出
            combo.setStyleSheet(
                "QComboBox { background: #0f0f23; color: #d4c5a9; border: 1px solid #4a3f35; "
                "padding: 2px 6px; } QComboBox::drop-down { border: none; } "
                "QComboBox QAbstractItemView { background: #16213e; color: #d4c5a9; "
                "selection-background-color: #c9a96e; }"
            )
            combo.currentTextChanged.connect(
                lambda text, idx=i: self.strategy_changed.emit(idx, text))
            row.addWidget(combo)
            self.strategy_combos.append(combo)
            strat_layout.addLayout(row)
        layout.addWidget(strat_group)

        # 按钮
        btn_row = QHBoxLayout()
        self.round_btn = QPushButton("执行回合 ▶")
        self.round_btn.setObjectName("primary")
        self.round_btn.setStyleSheet(
            "QPushButton#primary { background: #2d5a27; border-color: #4caf50; "
            "color: #d4c5a9; font-size: 14px; font-weight: bold; padding: 8px 16px; } "
            "QPushButton#primary:hover { background: #3a7a35; }"
        )
        self.round_btn.clicked.connect(self.round_requested.emit)

        self.flee_btn = QPushButton("撤退")
        self.flee_btn.setObjectName("danger")
        self.flee_btn.setStyleSheet(
            "QPushButton#danger { background: #8b0000; border-color: #ff4444; "
            "color: #d4c5a9; font-size: 12px; padding: 8px 12px; }"
        )
        self.flee_btn.clicked.connect(self.flee_requested.emit)

        btn_row.addWidget(self.round_btn)
        btn_row.addWidget(self.flee_btn)
        layout.addLayout(btn_row)

    def set_enemies(self, enemies: list[dict]) -> None:
        """设置敌人信息 [{name, hp_current, hp_max, hp_pct, tier}]"""
        # 清除旧的
        for lbl, bar in self.enemy_bars:
            self.enemy_layout.removeWidget(lbl)
            self.enemy_layout.removeWidget(bar)
            lbl.deleteLater()
            bar.deleteLater()
        self.enemy_bars.clear()

        for enemy in enemies:
            row = QHBoxLayout()
            name = QLabel(f"{enemy['name']} [{enemy.get('tier', '')}]")
            name.setStyleSheet("font-size: 12px; color: #e8d5b0; min-width: 100px;")
            row.addWidget(name)
            bar = QProgressBar()
            bar.setRange(0, enemy["hp_max"])
            bar.setValue(enemy["hp_current"])
            bar.setFormat(f"{enemy['hp_current']}/{enemy['hp_max']}")
            bar.setFixedHeight(16)
            bar.setStyleSheet(
                "QProgressBar { border: 1px solid #4a3f35; border-radius: 2px; "
                "background: #0f0f23; font-size: 10px; color: #d4c5a9; } "
                "QProgressBar::chunk { background: #c0392b; border-radius: 1px; }"
            )
            row.addWidget(bar)
            self.enemy_layout.addLayout(row)
            self.enemy_bars.append((name, bar))

    def update_enemy_hp(self, enemy_index: int, hp_cur: int, hp_max: int) -> None:
        if 0 <= enemy_index < len(self.enemy_bars):
            _, bar = self.enemy_bars[enemy_index]
            bar.setRange(0, hp_max)
            bar.setValue(hp_cur)
            bar.setFormat(f"{hp_cur}/{hp_max}")

    def set_strategy(self, member_index: int, strategy_name: str) -> None:
        if 0 <= member_index < len(self.strategy_combos):
            self.strategy_combos[member_index].setCurrentText(strategy_name)
