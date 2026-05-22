"""角色创建弹窗 — 属性、种族、职业、HP/MP分配"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QButtonGroup, QRadioButton, QLineEdit,
    QGroupBox, QWidget, QScrollArea,
)
from PySide6.QtCore import Qt, Signal

from data.classes import CLASSES
from data.races import RACES
from core.character import validate_point_buy, create_character, Character
from utils.constants import POINT_BUY_COST, TOTAL_POINTS

class CharacterCreateDialog(QDialog):
    character_created = Signal(Character)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("创建你的冒险者")
        self.resize(520, 580)
        self.setStyleSheet(
            "QDialog { background: #16213e; } "
            "QGroupBox { color: #c9a96e; font-weight: bold; border: 1px solid #3a3f55; "
            "border-radius: 6px; margin-top: 10px; padding-top: 14px; } "
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }"
        )

        layout = QVBoxLayout(self)

        # 滚动
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        self._form = QVBoxLayout(inner)

        # ---- 姓名 ----
        name_box = QGroupBox("姓名")
        nl = QVBoxLayout(name_box)
        self.name_input = QLineEdit("冒险者")
        self.name_input.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #4a3f35; "
            "border-radius: 4px; padding: 6px 10px; font-size: 14px; }"
        )
        nl.addWidget(self.name_input)
        self._form.addWidget(name_box)

        # ---- 种族 ----
        race_box = QGroupBox("选择种族")
        rl = QVBoxLayout(race_box)
        self.race_group = QButtonGroup(self)
        self._race_btns = {}
        for rid, rd in RACES.items():
            btn = QRadioButton(f"{rd.name}  {rd.description[:40]}…")
            btn.race_id = rid
            btn.setStyleSheet(
                "QRadioButton { color: #d4c5a9; font-size: 12px; padding: 4px 0; } "
                "QRadioButton::indicator { width: 14px; height: 14px; }"
            )
            self.race_group.addButton(btn)
            rl.addWidget(btn)
            self._race_btns[rid] = btn
        self._race_btns["human"].setChecked(True)
        self._form.addWidget(race_box)

        # ---- 职业 ----
        class_box = QGroupBox("选择职业")
        cl = QVBoxLayout(class_box)
        self.class_group = QButtonGroup(self)
        self._class_btns = {}
        for cid, cd in CLASSES.items():
            btn = QRadioButton(f"{cd.name} — {cd.description}")
            btn.class_id = cid
            btn.setStyleSheet(
                "QRadioButton { color: #d4c5a9; font-size: 12px; padding: 4px 0; } "
                "QRadioButton::indicator { width: 14px; height: 14px; }"
            )
            self.class_group.addButton(btn)
            cl.addWidget(btn)
            self._class_btns[cid] = btn
        self._class_btns["warrior"].setChecked(True)
        self._form.addWidget(class_box)

        # ---- 属性购点 ----
        attr_box = QGroupBox("属性分配 (27点购点制)")
        al = QVBoxLayout(attr_box)

        self._attr_spins = {}
        for attr_name, attr_cn in [("str","力量"),("dex","敏捷"),("con","体质"),
                                    ("int","智力"),("wis","感知"),("cha","魅力")]:
            row = QHBoxLayout()
            lbl = QLabel(f"{attr_cn}:")
            lbl.setStyleSheet("color: #d4c5a9; min-width: 50px;")
            row.addWidget(lbl)
            sp = QSpinBox()
            sp.setRange(8, 15)
            sp.setValue(10)
            sp.setStyleSheet(
                "QSpinBox { background: #0f0f23; color: #d4c5a9; border: 1px solid #4a3f35; "
                "border-radius: 3px; padding: 2px 6px; }"
            )
            sp.valueChanged.connect(self._update_point_info)
            row.addWidget(sp)
            self._attr_spins[attr_name] = sp
            al.addLayout(row)

        self._point_info = QLabel("已用: 12/27 点")
        self._point_info.setStyleSheet("font-size: 12px; color: #c9a96e; font-weight: bold;")
        al.addWidget(self._point_info)

        # 预设
        pre_row = QHBoxLayout()
        pre_row.addWidget(QLabel("预设配点:"))
        for name, attrs in [
            ("战士", {"str":15,"dex":12,"con":14,"int":8,"wis":10,"cha":13}),
            ("法师", {"str":8,"dex":12,"con":13,"int":15,"wis":12,"cha":13}),
            ("盗贼", {"str":10,"dex":15,"con":12,"int":10,"wis":11,"cha":14}),
            ("牧师", {"str":12,"dex":8,"con":15,"int":10,"wis":14,"cha":10}),
        ]:
            btn = QPushButton(name)
            btn.setStyleSheet(
                "QPushButton { background: rgba(201,169,110,0.1); color: #c9a96e; "
                "border: 1px solid #4a3f35; border-radius: 3px; padding: 2px 8px; font-size: 11px; } "
                "QPushButton:hover { background: rgba(201,169,110,0.3); }"
            )
            btn.clicked.connect(lambda checked, a=attrs: self._set_preset(a))
            pre_row.addWidget(btn)
        pre_row.addStretch()
        al.addLayout(pre_row)
        self._form.addWidget(attr_box)

        # ---- 确认 ----
        scroll.setWidget(inner)
        layout.addWidget(scroll)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self.create_btn = QPushButton("⚔ 开始冒险！")
        self.create_btn.setStyleSheet(
            "QPushButton { background: #c9a96e; color: #1a1a2e; font-size: 15px; "
            "font-weight: bold; border: none; border-radius: 6px; padding: 10px 24px; } "
            "QPushButton:hover { background: #d4b87a; }"
        )
        self.create_btn.clicked.connect(self._on_create)
        btn_row.addWidget(self.create_btn)
        layout.addLayout(btn_row)

    def _set_preset(self, attrs: dict) -> None:
        for attr_name, value in attrs.items():
            if attr_name in self._attr_spins:
                self._attr_spins[attr_name].setValue(value)

    def _update_point_info(self) -> None:
        total = sum(POINT_BUY_COST[s.value()] for s in self._attr_spins.values())
        color = "#27ae60" if total <= TOTAL_POINTS else "#e63946"
        self._point_info.setText(f"已用: {total}/{TOTAL_POINTS} 点")
        self._point_info.setStyleSheet(
            f"font-size: 12px; color: {color}; font-weight: bold;")

    def _on_create(self) -> None:
        name = self.name_input.text().strip() or "冒险者"

        race_id = "human"
        for rid, btn in self._race_btns.items():
            if btn.isChecked():
                race_id = rid
                break

        class_id = "warrior"
        for cid, btn in self._class_btns.items():
            if btn.isChecked():
                class_id = cid
                break

        attrs = {a: s.value() for a, s in self._attr_spins.items()}
        valid, spent, err = validate_point_buy(attrs)
        if not valid:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "购点错误", err)
            return

        char = create_character(name, race_id, class_id, attrs)
        if isinstance(char, str):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "创建失败", char)
            return

        char.is_main = True
        self.character_created.emit(char)
        self.accept()
