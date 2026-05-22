"""队员详情弹窗 — 装备/技能/策略/规则 标签页"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QPushButton, QComboBox, QCheckBox, QSpinBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QWidget, QMessageBox, QScrollArea,
)
from PySide6.QtCore import Signal, Qt

from core.character import Character
from core.party import Party
from core.inventory import Inventory
from core.auto_rules import AutoRuleEngine, BUILTIN_RULES
from utils.constants import StrategyType


class MemberDetailDialog(QDialog):
    item_used = Signal(str, int)       # item_id, member_slot
    item_equipped = Signal(str, int)
    item_unequipped = Signal(str, int)
    item_discarded = Signal(str)
    strategy_changed = Signal(int, str)
    rule_toggled = Signal(int, str)
    rule_threshold = Signal(int, str, int)

    def __init__(self, party: Party, inventory: Inventory,
                 auto_rules: AutoRuleEngine, combat=None, parent=None):
        super().__init__(parent)
        self.party = party
        self.inventory = inventory
        self.auto_rules = auto_rules
        self.combat = combat
        self.setWindowTitle("队员详情")
        self.resize(520, 480)
        self.setStyleSheet(
            "QDialog { background: #16213e; }"
            "QTabWidget::pane { border: 1px solid #3a3f55; background: #16213e; }"
            "QTabBar::tab { background: #0f0f23; color: #8a8fa0; padding: 6px 14px; "
            "border: 1px solid #3a3f55; border-bottom: none; } "
            "QTabBar::tab:selected { background: #16213e; color: #c9a96e; font-weight: bold; }"
        )

        layout = QVBoxLayout(self)

        # 队员选择
        top = QHBoxLayout()
        top.addWidget(QLabel("查看队员："))
        self.member_combo = QComboBox()
        self.member_combo.setStyleSheet(
            "QComboBox { background: #0f0f23; color: #d4c5a9; border: 1px solid #4a3f35; "
            "padding: 4px 8px; } QComboBox::drop-down { border: none; }"
        )
        for i, m in enumerate(party.members):
            if m:
                self.member_combo.addItem(f"[{i + 1}] {m.name}  Lv{m.level} {m.class_name}", i)
        self.member_combo.currentIndexChanged.connect(self._on_member_changed)
        top.addWidget(self.member_combo)
        layout.addLayout(top)

        # 标签页
        self.tabs = QTabWidget()
        self._build_equipment_tab()
        self._build_skills_tab()
        self._build_strategy_tab()
        self._build_rules_tab()
        self._build_background_tab()
        self._build_ai_chat_tab()
        layout.addWidget(self.tabs)

        # 关闭
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet(
            "QPushButton { background: #3a3f55; color: #d4c5a9; border: none; "
            "border-radius: 4px; padding: 6px 20px; } "
            "QPushButton:hover { background: #c9a96e; color: #1a1a2e; }"
        )
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

        self._on_member_changed(0)

    def _current_slot(self) -> int:
        return self.member_combo.currentData()

    def _current_member(self) -> Character | None:
        return self.party.get(self._current_slot())

    # ========== 装备标签页 ==========
    def _build_equipment_tab(self) -> None:
        tab = QWidget()
        vbox = QVBoxLayout(tab)

        # 已装备
        vbox.addWidget(QLabel("已装备："))
        self.equipped_table = QTableWidget(0, 3)
        self.equipped_table.setHorizontalHeaderLabels(["物品", "类型", "操作"])
        self.equipped_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.equipped_table.setStyleSheet(
            "QTableWidget { background: #0f0f23; color: #d4c5a9; border: 1px solid #3a3f55; } "
            "QTableWidget::item { padding: 3px; } "
            "QHeaderView::section { background: #1a1a3e; color: #c9a96e; padding: 3px; }"
        )
        vbox.addWidget(self.equipped_table)

        # 背包可用
        vbox.addWidget(QLabel("背包物品："))
        self.bag_table = QTableWidget(0, 4)
        self.bag_table.setHorizontalHeaderLabels(["物品", "类型", "数量", "操作"])
        self.bag_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.bag_table.setStyleSheet(self.equipped_table.styleSheet())
        vbox.addWidget(self.bag_table)

        self.tabs.addTab(tab, "🎒 装备")

    def _refresh_equipment_tab(self) -> None:
        slot = self._current_slot()
        from data.items import ITEMS, ItemType

        # 已装备
        equipped = self.inventory.equipped_of(slot)
        self.equipped_table.setRowCount(len(equipped))
        for r, eq in enumerate(equipped):
            self.equipped_table.setItem(r, 0, QTableWidgetItem(eq.item_id))
            self.equipped_table.setItem(r, 1, QTableWidgetItem(
                eq.template.item_type.value if eq.template else eq.item_id))
            btn = QPushButton("卸下")
            btn.clicked.connect(lambda checked, eid=eq.item_id, s=slot:
                                self.item_unequipped.emit(eid, s))
            self.equipped_table.setCellWidget(r, 2, btn)

        # 背包
        bp = self.inventory.backpack_items()
        self.bag_table.setRowCount(len(bp))
        for r, item in enumerate(bp):
            tmpl = item.template
            name = tmpl.name if tmpl else item.item_id
            itype = tmpl.item_type.value if tmpl else ""
            self.bag_table.setItem(r, 0, QTableWidgetItem(name))
            self.bag_table.setItem(r, 1, QTableWidgetItem(itype))
            self.bag_table.setItem(r, 2, QTableWidgetItem(str(item.quantity)))

            btn_row = QWidget()
            btn_layout = QHBoxLayout(btn_row)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(4)

            equip_btn = QPushButton("装备")
            equip_btn.clicked.connect(
                lambda checked, iid=item.item_id, s=slot:
                    self.item_equipped.emit(iid, s))
            use_btn = QPushButton("使用")
            use_btn.clicked.connect(
                lambda checked, iid=item.item_id, s=slot:
                    self.item_used.emit(iid, s))
            btn_layout.addWidget(equip_btn)
            btn_layout.addWidget(use_btn)
            self.bag_table.setCellWidget(r, 3, btn_row)

    # ========== 技能标签页 ==========
    def _build_skills_tab(self) -> None:
        tab = QWidget()
        vbox = QVBoxLayout(tab)
        self.skills_label = QLabel("")
        self.skills_label.setWordWrap(True)
        self.skills_label.setStyleSheet("color: #d4c5a9; font-size: 12px; padding: 8px;")
        vbox.addWidget(self.skills_label)
        vbox.addStretch()
        self.tabs.addTab(tab, "📜 技能")

    def _refresh_skills_tab(self) -> None:
        member = self._current_member()
        if not member:
            return
        racial = member.race_data
        lines = [f"—— {member.class_name} 技能 ——"]

        # 从职业升级表中按等级列出技能
        for lv in sorted(member.class_data.skill_table.keys()):
            for s in member.class_data.skill_table[lv]:
                learned = "✓" if member.level >= lv else "🔒"
                lines.append(f"\n{learned} ⚡ {s.name} (需要Lv{lv})")
                lines.append(f"   伤害倍率 ×{s.damage_multiplier}  |  MP消耗 {s.mp_cost}")
                if s.extra_effects:
                    lines.append(f"   附加效果: {s.extra_effects}")

        lines.append(f"\n\n—— 种族天赋 ——")
        lines.append(f"主动: {racial.active_name} — {racial.active_desc}")
        for p in racial.passives:
            lines.append(f"被动: {p.get('name', '')} — {p.get('desc', '')}")

        self.skills_label.setText("\n".join(lines))

    # ========== 策略标签页 ==========
    def _build_strategy_tab(self) -> None:
        tab = QWidget()
        vbox = QVBoxLayout(tab)

        vbox.addWidget(QLabel("战斗策略："))
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([s.value for s in StrategyType])
        self.strategy_combo.currentTextChanged.connect(self._on_strategy)
        vbox.addWidget(self.strategy_combo)

        vbox.addSpacing(12)

        vbox.addWidget(QLabel("行动模式预设："))
        modes = QLabel(
            "· 全力猛攻 — 优先最强技能，不保留法力\n"
            "· 平衡输出 — 技能普攻交替，法力30%时节省\n"
            "· 保留法力 — 仅普攻，不使用法术\n"
            "· 优先治疗 — 队友HP<60%时施放治疗\n"
            "· 防御牵制 — 使用挑衅/闪避，保护队友"
        )
        modes.setStyleSheet("color: #8a8fa0; font-size: 11px;")
        vbox.addWidget(modes)

        vbox.addStretch()
        self.tabs.addTab(tab, "🎯 策略")

    def _on_strategy(self, text: str) -> None:
        self.strategy_changed.emit(self._current_slot(), text)

    # ========== 规则标签页 ==========
    def _build_rules_tab(self) -> None:
        tab = QWidget()
        self.rules_layout = QVBoxLayout(tab)
        self.tabs.addTab(tab, "⚙ 自动规则")

    def _refresh_rules_tab(self) -> None:
        slot = self._current_slot()
        # 清空
        while self.rules_layout.count():
            item = self.rules_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        rules = self.auto_rules.get_rules(slot)
        for rule in rules:
            info = BUILTIN_RULES.get(rule.rule_id, {})
            row = QHBoxLayout()
            cb = QCheckBox(info.get("name", rule.rule_id))
            cb.setChecked(rule.enabled)
            cb.toggled.connect(
                lambda checked, rid=rule.rule_id, s=slot:
                    self.rule_toggled.emit(s, rid))
            row.addWidget(cb)

            threshold_label = QLabel(f"阈值:")
            row.addWidget(threshold_label)

            sp = QSpinBox()
            sp.setRange(1, 99)
            sp.setValue(rule.threshold)
            sp.setSuffix("%")
            sp.valueChanged.connect(
                lambda val, rid=rule.rule_id, s=slot:
                    self.rule_threshold.emit(s, rid, val))
            row.addWidget(sp)

            desc = QLabel(info.get("desc", ""))
            desc.setStyleSheet("color: #6c757d; font-size: 10px;")
            row.addWidget(desc)
            row.addStretch()

            self.rules_layout.addLayout(row)

        self.rules_layout.addStretch()

    # ========== 角色背景标签页 ==========
    def _build_background_tab(self) -> None:
        tab = QWidget()
        vbox = QVBoxLayout(tab)
        self.bg_text = QLabel("")
        self.bg_text.setWordWrap(True)
        self.bg_text.setStyleSheet("color: #d4c5a9; font-size: 12px; padding: 8px;")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.setWidget(self.bg_text)
        vbox.addWidget(scroll)
        self.tabs.addTab(tab, "📖 背景")

    def _refresh_background_tab(self) -> None:
        member = self._current_member()
        if not member:
            return
        cd = member.class_data
        rd = member.race_data

        # 好感度汇总
        aff_lines = []
        if member.affinity:
            aff_lines.append("—— 好感度 ——")
            for npc_id, val in member.affinity.items():
                from world.story import ALL_DIALOGUES
                tree = ALL_DIALOGUES.get(npc_id)
                name = tree.npc_name if tree else npc_id
                bar = "♥" * (val // 20) + "♡" * (5 - val // 20)
                aff_lines.append(f"  {name}: {bar} ({val})")

        text = f"""—— 角色传记 ——

{member.name}，一名{member.race_name}{member.class_name}。
当前等级 Lv.{member.level}，经验值 {member.xp}/{member.xp_to_next()}。

—— 种族背景 ——
{rd.description}

—— 职业介绍 ——
{cd.description}

—— 属性总览 ——
力量: {member.final_attr("str"):>2}  (近战伤害)
敏捷: {member.final_attr("dex"):>2}  (远程/闪避/先手)
体质: {member.final_attr("con"):>2}  (HP上限/防御)
智力: {member.final_attr("int"):>2}  (法术伤害/暴击)
感知: {member.final_attr("wis"):>2}  (MP上限/治疗)
魅力: {member.final_attr("cha"):>2}  (交易/说服)

HP: {member.hp_current}/{member.hp_max}  |  MP: {member.mp_current}/{member.mp_max}

{chr(10).join(aff_lines)}
"""
        self.bg_text.setText(text)

    # ========== AI聊天标签页（预留） ==========
    def _build_ai_chat_tab(self) -> None:
        tab = QWidget()
        vbox = QVBoxLayout(tab)

        placeholder = QLabel(
            "🤖 AI 角色对话\n\n"
            "此功能将在未来版本中开放。\n\n"
            "接入 AI 后，你可以：\n"
            "· 与角色进行自由对话\n"
            "· 了解角色的故事和秘密\n"
            "· 获取冒险建议和提示\n"
            "· 角色会根据好感度和剧情做出不同回应\n\n"
            "敬请期待！"
        )
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setWordWrap(True)
        placeholder.setStyleSheet("color: #6c757d; font-size: 13px; padding: 20px;")
        vbox.addWidget(placeholder)
        vbox.addStretch()
        self.tabs.addTab(tab, "🤖 AI聊天")

    # ========== 切换队员 ==========
    def _on_member_changed(self, _index: int) -> None:
        slot = self._current_slot()
        if slot < 0:
            return
        # 更新策略下拉
        if self.combat:
            s = self.combat.get_strategy(slot)
            self.strategy_combo.setCurrentText(s.value)
        self._refresh_equipment_tab()
        self._refresh_skills_tab()
        self._refresh_rules_tab()
        self._refresh_background_tab()

        # 主角隐藏AI聊天标签
        member = self._current_member()
        for i in range(self.tabs.count()):
            if "AI" in self.tabs.tabText(i):
                self.tabs.setTabVisible(i, not (member and member.is_main))
