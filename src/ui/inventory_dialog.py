"""背包与装备对话框"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QMessageBox,
)
from PySide6.QtCore import Qt, Signal

from data.items import ITEMS, RARITY_NAMES, RARITY_COLORS


class InventoryDialog(QDialog):
    item_used = Signal(str, int)       # item_id, target_member_index
    item_equipped = Signal(str, int)   # item_id, member_index
    item_unequipped = Signal(str, int) # item_id, member_index
    item_discarded = Signal(str)

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setWindowTitle("背包与装备")
        self.resize(700, 500)
        self.setStyleSheet(
            "QDialog { background-color: #1a1a2e; border: 2px solid #c9a96e; }"
        )

        layout = QVBoxLayout(self)

        # 金币
        self.gold_label = QLabel()
        self.gold_label.setStyleSheet("font-size: 14px; color: #f0a500; font-weight: bold;")
        layout.addWidget(self.gold_label)

        # 背包表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["物品名称", "数量", "类型", "稀有度", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setColumnWidth(1, 50)
        self.table.setColumnWidth(2, 60)
        self.table.setColumnWidth(3, 60)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setStyleSheet(
            "QTableWidget { background: #0f0f23; color: #d4c5a9; border: 1px solid #4a3f35; "
            "gridline-color: #2a2a3e; } "
            "QHeaderView::section { background: #16213e; color: #c9a96e; "
            "border: 1px solid #4a3f35; padding: 4px; }"
        )
        layout.addWidget(self.table)

        # 关闭
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def refresh(self) -> None:
        inv = self.engine.inventory
        self.gold_label.setText(f"金币: {inv.gold} G")

        items = inv.backpack_items()
        equipped = []
        for i in range(4):
            equipped.extend(inv.equipped_of(i))

        all_items = items + equipped
        self.table.setRowCount(len(all_items))

        for row, item in enumerate(all_items):
            tmpl = item.template
            name = tmpl.name if tmpl else item.item_id
            r_name = RARITY_NAMES.get(tmpl.rarity, "") if tmpl else ""
            r_color = RARITY_COLORS.get(tmpl.rarity, "#9d9d9d") if tmpl else "#9d9d9d"
            type_name = tmpl.item_type.value if tmpl else ""

            self.table.setItem(row, 0, QTableWidgetItem(name))

            qty = QTableWidgetItem(str(item.quantity))
            qty.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, qty)

            self.table.setItem(row, 2, QTableWidgetItem(type_name))

            rarity_item = QTableWidgetItem(r_name)
            rarity_item.setForeground(Qt.GlobalColor(
                {"#9d9d9d": Qt.gray, "#1eff00": Qt.green, "#0070dd": Qt.blue,
                 "#a335ee": Qt.darkMagenta, "#ff8000": Qt.darkYellow}.get(
                    r_color, Qt.gray)))
            self.table.setItem(row, 3, rarity_item)

            # 操作按钮
            btn_widget = QHBoxLayout()
            btn_widget.setContentsMargins(2, 2, 2, 2)
            btn_widget.setSpacing(2)

            if item.equipped_by > 0:
                label = QLabel(f"装备中(队员{item.equipped_by})")
                label.setStyleSheet("font-size: 11px; color: #c9a96e;")
                unequip_btn = QPushButton("卸下")
                unequip_btn.setFixedSize(40, 22)
                unequip_btn.setStyleSheet("font-size: 10px;")
                unequip_btn.clicked.connect(
                    lambda checked, iid=item.item_id, mid=item.equipped_by:
                    self.item_unequipped.emit(iid, mid))
                btn_widget.addWidget(label)
                btn_widget.addWidget(unequip_btn)
            elif tmpl and tmpl.item_type.value in ("weapon", "armor", "helmet",
                                                     "gloves", "boots", "accessory"):
                equip_btn = QPushButton("装备")
                equip_btn.setFixedSize(40, 22)
                equip_btn.setStyleSheet("font-size: 10px;")
                equip_btn.clicked.connect(
                    lambda checked, iid=item.item_id: self._ask_equip_target(iid))
                btn_widget.addWidget(equip_btn)

                discard_btn = QPushButton("丢弃")
                discard_btn.setFixedSize(40, 22)
                discard_btn.setStyleSheet(
                    "font-size: 10px; background: #8b0000; border-color: #ff4444;")
                discard_btn.clicked.connect(
                    lambda checked, iid=item.item_id: self.item_discarded.emit(iid))
                btn_widget.addWidget(discard_btn)
            elif tmpl and tmpl.item_type.value == "consumable":
                use_btn = QPushButton("使用")
                use_btn.setFixedSize(40, 22)
                use_btn.setStyleSheet(
                    "font-size: 10px; background: #2d5a27; border-color: #4caf50;")
                use_btn.clicked.connect(
                    lambda checked, iid=item.item_id: self._ask_use_target(iid))
                btn_widget.addWidget(use_btn)

            container = QHBoxLayout()
            container.addLayout(btn_widget)
            container.addStretch()
            cell = QHBoxLayout()
            cell.addLayout(container)

    def _ask_equip_target(self, item_id: str) -> None:
        from PySide6.QtWidgets import QInputDialog
        members = [m for m in self.engine.party.members if m is not None]
        names = [f"{i+1}. {m.name}" for i, m in enumerate(members)]
        name, ok = QInputDialog.getItem(self, "选择队员", "装备到哪位队员？", names, 0, False)
        if ok and name:
            idx = int(name.split(".")[0]) - 1
            self.item_equipped.emit(item_id, idx)

    def _ask_use_target(self, item_id: str) -> None:
        from PySide6.QtWidgets import QInputDialog
        members = [m for m in self.engine.party.members if m is not None]
        names = [f"{i+1}. {m.name} (HP:{m.hp_current}/{m.hp_max})"
                 for i, m in enumerate(members)]
        name, ok = QInputDialog.getItem(self, "选择使用对象", "给谁使用？", names, 0, False)
        if ok and name:
            idx = int(name.split(".")[0]) - 1
            self.item_used.emit(item_id, idx)
