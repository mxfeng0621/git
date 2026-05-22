"""主窗口 — NPC对话树 + 任务列表 + 场景互动 + 两级地图 + AI聊天预留"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QMessageBox, QFrame,
    QScrollArea, QInputDialog,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from app.styles import MAIN_STYLE
from core.engine import GameEngine
from core.combat import Combat, CombatEvent
from core.dialogue import DialogueNode
from services.save_service import list_saves
from ui.party_panel import PartyPanel
from ui.scene_view import SceneView
from ui.command_input import CommandInput
from ui.member_detail_dialog import MemberDetailDialog
from ui.world_map_dialog import WorldMapDialog
from ui.character_create_dialog import CharacterCreateDialog
from utils.constants import CombatResult, StrategyType

SCENE_NAMES = {
    "river_town": "河畔镇", "river_inn": "醉龙酒馆", "river_smith": "铁匠铺",
    "river_shop": "杂货商店", "river_hall": "镇长宅邸",
    "dark_forest": "幽暗森林", "forest_deep": "森林深处",
    "goblin_camp": "地精营地", "elf_ruins": "精灵遗迹",
    "abandoned_mine": "废弃矿洞",
}


# ═══════════════════════════════════════════
# NPC — 点击展开对话树实际选项
# ═══════════════════════════════════════════
class NpcEntry(QFrame):
    option_clicked = Signal(str, str, int)  # npc_id, next_node_id, option_index

    def __init__(self, npc_id: str, npc_name: str, greeting_node: DialogueNode | None,
                 parent=None):
        super().__init__(parent)
        self._npc_id = npc_id
        self._npc_name = npc_name
        self._greeting = greeting_node
        self.setStyleSheet(
            "NpcEntry { background: rgba(142,202,230,0.08); border: 1px solid #3a5360; "
            "border-radius: 5px; margin: 1px 0; }"
        )
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._toggle = QPushButton(f"  🗣 {npc_name}")
        self._toggle.setCheckable(True)
        self._toggle.setFixedHeight(28)
        self._toggle.setStyleSheet(
            "QPushButton { text-align: left; background: transparent; "
            "color: #8ecae6; border: none; font-size: 12px; padding: 2px 6px; } "
            "QPushButton:hover { background: rgba(142,202,230,0.2); color: #fff; } "
            "QPushButton:checked { background: rgba(142,202,230,0.25); color: #fff; }"
        )
        self._toggle.clicked.connect(self._on_toggle)
        self._layout.addWidget(self._toggle)

        self._opts_frame = QFrame()
        self._opts_frame.setVisible(False)
        self._opts_frame.setStyleSheet("QFrame { background: transparent; border: none; }")
        self._opts_layout = QVBoxLayout(self._opts_frame)
        self._opts_layout.setContentsMargins(8, 2, 8, 6)
        self._opts_layout.setSpacing(2)
        self._layout.addWidget(self._opts_frame)

        self._populate_options()

    def _populate_options(self) -> None:
        if self._greeting and self._greeting.options:
            for i, opt in enumerate(self._greeting.options):
                icon = "📋" if "start_quest" in str(opt.effects) else \
                    "👥" if "recruit" in str(opt.effects) else \
                    "🎁" if "give_item" in str(opt.effects) else "💬"
                btn = QPushButton(f"  {icon} {opt.text}")
                btn.setFixedHeight(26)
                btn.setStyleSheet(
                    "QPushButton { text-align: left; background: rgba(15,15,35,0.8); "
                    "color: #d4c5a9; border: 1px solid #3a3f55; border-radius: 3px; "
                    "font-size: 11px; padding: 2px 8px; } "
                    "QPushButton:hover { background: rgba(201,169,110,0.3); }"
                )
                btn.clicked.connect(
                    lambda checked, idx=i: self.option_clicked.emit(
                        self._npc_id, self._greeting.options[idx].next_id, idx))
                self._opts_layout.addWidget(btn)

    def _on_toggle(self) -> None:
        self._opts_frame.setVisible(self._toggle.isChecked())

    def collapse(self) -> None:
        self._toggle.setChecked(False)
        self._opts_frame.setVisible(False)


# ═══════════════════════════════════════════
# 任务列表项
# ═══════════════════════════════════════════
class QuestItem(QFrame):
    def __init__(self, quest_id: str, name: str, description: str,
                 objectives: list[str], parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "QuestItem { background: rgba(201,169,110,0.06); border: 1px solid #4a3f35; "
            "border-radius: 4px; margin: 1px 0; }"
        )
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        self._toggle = QPushButton(f"  📋 {name}")
        self._toggle.setCheckable(True)
        self._toggle.setFixedHeight(24)
        self._toggle.setStyleSheet(
            "QPushButton { text-align: left; background: transparent; color: #c9a96e; "
            "border: none; font-size: 11px; padding: 2px 6px; } "
            "QPushButton:hover { background: rgba(201,169,110,0.15); } "
            "QPushButton:checked { background: rgba(201,169,110,0.2); }"
        )
        self._toggle.clicked.connect(self._on_toggle)
        vbox.addWidget(self._toggle)

        self._detail = QFrame()
        self._detail.setVisible(False)
        dl = QVBoxLayout(self._detail)
        dl.setContentsMargins(8, 2, 8, 6)
        dl.setSpacing(2)

        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet("font-size: 10px; color: #8a8fa0;")
        desc_lbl.setWordWrap(True)
        dl.addWidget(desc_lbl)

        for obj in objectives:
            ol = QLabel(f"  ○ {obj}")
            ol.setStyleSheet("font-size: 10px; color: #c0b090;")
            dl.addWidget(ol)

        vbox.addWidget(self._detail)

    def _on_toggle(self) -> None:
        self._detail.setVisible(self._toggle.isChecked())


# ═══════════════════════════════════════════
# 左侧信息栏
# ═══════════════════════════════════════════
class InfoPanel(QFrame):
    npc_option = Signal(str, str, int)  # npc_id, next_id, option_index
    map_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(185)
        self.setStyleSheet(
            "InfoPanel { background: rgba(22,33,62,0.85); border: 1px solid #3a3f55; "
            "border-radius: 8px; }"
        )
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        self._layout = QVBoxLayout(inner)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(5)

        # 标题
        t = QLabel("冒险信息")
        t.setStyleSheet("font-size: 14px; font-weight: bold; color: #c9a96e;")
        self._layout.addWidget(t)

        self.scene_lbl = QLabel("📍 河畔镇")
        self.scene_lbl.setStyleSheet("font-size: 13px; color: #c9a96e; font-weight: bold;")
        self.scene_lbl.setWordWrap(True)
        self._layout.addWidget(self.scene_lbl)
        self._layout.addWidget(self._sep())

        self.gold_lbl = QLabel("💰 0 G")
        self.gold_lbl.setStyleSheet("font-size: 13px; color: #f0a500; font-weight: bold;")
        self._layout.addWidget(self.gold_lbl)
        self._layout.addWidget(self._sep())

        self.party_lbl = QLabel("👥 1/4")
        self.party_lbl.setStyleSheet("font-size: 12px; color: #8ecae6;")
        self._layout.addWidget(self.party_lbl)

        self.save_lbl = QLabel("💾 未保存")
        self.save_lbl.setStyleSheet("font-size: 12px; color: #6c757d;")
        self._layout.addWidget(self.save_lbl)
        self._layout.addWidget(self._sep())

        # NPC
        npc_title = QLabel("📍 在场NPC")
        npc_title.setStyleSheet("font-size: 12px; color: #8ecae6; font-weight: bold;")
        self._layout.addWidget(npc_title)
        self._npc_layout = QVBoxLayout()
        self._npc_layout.setSpacing(2)
        self._layout.addLayout(self._npc_layout)
        self._npc_widgets: list[NpcEntry] = []

        self._layout.addWidget(self._sep())

        # 地图按钮
        map_btn = QPushButton("  🗺 世界地图")
        map_btn.setFixedHeight(28)
        map_btn.setStyleSheet(
            "QPushButton { text-align: left; background: rgba(142,202,230,0.1); "
            "color: #8ecae6; border: 1px solid #3a5360; border-radius: 4px; "
            "font-size: 12px; } "
            "QPushButton:hover { background: rgba(142,202,230,0.25); }"
        )
        map_btn.clicked.connect(self.map_requested.emit)
        self._layout.addWidget(map_btn)

        self._layout.addWidget(self._sep())

        # 任务列表
        self._quest_label = QLabel("📜 任务日志")
        self._quest_label.setStyleSheet("font-size: 12px; color: #8ecae6; font-weight: bold;")
        self._layout.addWidget(self._quest_label)
        self._quest_layout = QVBoxLayout()
        self._quest_layout.setSpacing(2)
        self._layout.addLayout(self._quest_layout)
        self._quest_widgets: list[QuestItem] = []

        self._layout.addStretch()

        scroll.setWidget(inner)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _sep(self) -> QFrame:
        s = QFrame()
        s.setFrameShape(QFrame.HLine)
        s.setStyleSheet("QFrame { color: #3a3f55; }")
        return s

    def set_npcs(self, npc_data: list[dict]) -> None:
        for w in self._npc_widgets:
            self._npc_layout.removeWidget(w)
            w.deleteLater()
        self._npc_widgets.clear()
        for nd in npc_data:
            entry = NpcEntry(nd["id"], nd["name"], nd.get("greeting"))
            entry.option_clicked.connect(self.npc_option.emit)
            self._npc_layout.addWidget(entry)
            self._npc_widgets.append(entry)

    def set_quests(self, quests: list[dict]) -> None:
        for w in self._quest_widgets:
            self._quest_layout.removeWidget(w)
            w.deleteLater()
        self._quest_widgets.clear()
        for q in quests:
            item = QuestItem(q["id"], q["name"], q["description"], q["objectives"])
            self._quest_layout.addWidget(item)
            self._quest_widgets.append(item)

    def refresh(self, scene_name: str, gold: int, party_count: int,
                has_save: bool) -> None:
        self.scene_lbl.setText(f"📍 {scene_name}")
        self.gold_lbl.setText(f"💰 {gold} G")
        self.party_lbl.setText(f"👥 {party_count}/4")
        self.save_lbl.setText("💾 已存档" if has_save else "💾 未保存")


# ═══════════════════════════════════════════
# 右侧场景互动
# ═══════════════════════════════════════════
class SceneInteractionPanel(QFrame):
    travel_clicked = Signal(str)
    interact_clicked = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(195)
        self.setStyleSheet(
            "SceneInteractionPanel { background: rgba(22,33,62,0.85); "
            "border: 1px solid #3a3f55; border-radius: 8px; }"
        )
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        self._layout = QVBoxLayout(inner)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(6)

        scroll.setWidget(inner)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def set_scene(self, scene: dict) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        title = QLabel(f"📍 {scene.get('name', '')}")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #c9a96e;")
        title.setWordWrap(True)
        self._layout.addWidget(title)

        desc = scene.get("description", "")[:100]
        if desc:
            d = QLabel(desc + ("…" if len(scene.get("description", "")) > 100 else ""))
            d.setStyleSheet("font-size: 11px; color: #8a8fa0;")
            d.setWordWrap(True)
            self._layout.addWidget(d)

        self._layout.addWidget(self._sep())

        exits = scene.get("exits", {})
        if exits:
            self._layout.addWidget(self._lbl("🚶 可前往", "#8ecae6"))
            for direction, target_name in exits.items():
                btn = QPushButton(f"  → {direction} · {target_name}")
                btn.setFixedHeight(28)
                btn.setStyleSheet(self._btn_style("#bbd8e8", "#3a5360"))
                btn.clicked.connect(lambda c, d=direction: self.travel_clicked.emit(d))
                self._layout.addWidget(btn)

        interactables = scene.get("interactables", [])
        if interactables:
            self._layout.addWidget(self._sep())
            self._layout.addWidget(self._lbl("🔍 可交互", "#c9a96e"))
            for obj in interactables:
                btn = QPushButton(f"  {obj.get('icon', '')} {obj['label']}")
                btn.setFixedHeight(28)
                btn.setStyleSheet(self._btn_style("#c9a96e", "#4a3f35"))
                btn.clicked.connect(
                    lambda c, o=obj: self.interact_clicked.emit(
                        o.get("action", "look"), o.get("target", "")))
                self._layout.addWidget(btn)

        self._layout.addStretch()

    def _lbl(self, text, color):
        l = QLabel(text)
        l.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {color};")
        return l

    def _btn_style(self, color, border):
        return (
            f"QPushButton {{ text-align: left; background: rgba(15,15,35,0.6); "
            f"color: {color}; border: 1px solid {border}; border-radius: 4px; "
            f"font-size: 12px; }} "
            f"QPushButton:hover {{ background: rgba(201,169,110,0.25); }}"
        )

    def _sep(self):
        s = QFrame()
        s.setFrameShape(QFrame.HLine)
        s.setStyleSheet("QFrame { color: #3a3f55; }")
        return s


# ═══════════════════════════════════════════
# 战斗操作栏
# ═══════════════════════════════════════════
class CombatActionBar(QFrame):
    round_clicked = Signal()
    flee_clicked = Signal()
    strategy_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(170, 158)
        self.setStyleSheet(
            "CombatActionBar { background: rgba(22,33,62,0.9); border: 2px solid #8b0000; "
            "border-radius: 8px; }"
        )
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(4)
        vbox.addWidget(self._lbl("⚔ 战斗", "#e63946"))

        self.round_btn = self._btn("▶ 执行回合", "#2d5a27", "#3a7a35")
        self.round_btn.clicked.connect(self.round_clicked.emit)
        vbox.addWidget(self.round_btn)

        self.flee_btn = self._btn("🏃 逃跑", "#8b0000", "#a00000")
        self.flee_btn.clicked.connect(self.flee_clicked.emit)
        vbox.addWidget(self.flee_btn)

        for sname in ["全力猛攻", "平衡输出", "保留法力", "优先治疗", "防御牵制"]:
            btn = QPushButton(f"🎯 {sname}")
            btn.setFixedHeight(20)
            btn.setStyleSheet(
                "QPushButton { text-align: left; background: rgba(201,169,110,0.1); "
                "color: #c0b090; border: 1px solid #3a3f55; border-radius: 3px; "
                "font-size: 11px; } "
                "QPushButton:hover { background: rgba(201,169,110,0.3); }"
            )
            btn.clicked.connect(lambda c, s=sname: self.strategy_selected.emit(s))
            vbox.addWidget(btn)

    def _lbl(self, t, c):
        l = QLabel(t)
        l.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {c};")
        return l

    def _btn(self, t, bg, hov):
        b = QPushButton(t)
        b.setStyleSheet(
            f"QPushButton {{ background: {bg}; color: #d4c5a9; font-size: 12px; "
            f"font-weight: bold; border: none; border-radius: 4px; padding: 6px; }} "
            f"QPushButton:hover {{ background: {hov}; }}"
        )
        return b


# ═══════════════════════════════════════════
# 主窗口
# ═══════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("龙焰传说 — DND文字冒险")
        self.resize(1360, 860)
        self.setMinimumSize(1100, 720)
        self.setStyleSheet(MAIN_STYLE)

        self.engine = GameEngine()
        self._setup_engine_callbacks()
        self._build_menu_bar()
        self._build_central()

    def _setup_engine_callbacks(self) -> None:
        e = self.engine
        e.on_message = lambda t, c: self.scene_view.append_text(t)
        e.on_scene_change = self._on_scene_changed
        e.on_combat_start = self._on_combat_started
        e.on_combat_round = self._on_combat_round
        e.on_combat_end = lambda r, l, x, g: self._on_combat_ended(r, l, x, g)

    # ========== 菜单 ==========
    def _build_menu_bar(self) -> None:
        bar = self.menuBar()
        game = bar.addMenu("游戏(&G)")
        game.addAction(QAction("新游戏(&N)", self, triggered=self._on_new_game))
        game.addAction(QAction("存档(&S)", self, triggered=self._on_save))
        game.addAction(QAction("读档(&L)", self, triggered=self._on_load))
        game.addSeparator()
        game.addAction(QAction("退出(&Q)", self, triggered=self.close))
        help_menu = bar.addMenu("帮助(&H)")
        help_menu.addAction(QAction("关于(&A)", self, triggered=self._on_about))

    # ========== 布局 ==========
    def _build_central(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(4)

        top = QHBoxLayout()
        top.setSpacing(6)

        self.info_panel = InfoPanel()
        self.info_panel.npc_option.connect(self._on_npc_option)
        self.info_panel.map_requested.connect(self._on_map_dialog)
        top.addWidget(self.info_panel)

        self.scene_view = SceneView()
        top.addWidget(self.scene_view, stretch=1)

        self.scene_interact = SceneInteractionPanel()
        self.scene_interact.travel_clicked.connect(lambda d: self._exec(f"前往 {d}"))
        self.scene_interact.interact_clicked.connect(self._on_scene_interact)
        top.addWidget(self.scene_interact)

        root.addLayout(top, stretch=3)

        # 底部：队员 + 战斗
        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        self.party_panel = PartyPanel()
        for card in self.party_panel.cards:
            card.clicked.connect(self._on_member_card_clicked)
        bottom.addWidget(self.party_panel, stretch=1)

        self.combat_bar = CombatActionBar()
        self.combat_bar.round_clicked.connect(self._on_combat_round_btn)
        self.combat_bar.flee_clicked.connect(self._on_flee)
        self.combat_bar.strategy_selected.connect(self._on_combat_strategy)
        self.combat_bar.setVisible(False)
        bottom.addWidget(self.combat_bar)

        root.addLayout(bottom)

        # 命令输入（AI聊天预留）
        self.cmd_input = CommandInput()
        self.cmd_input.command_entered.connect(self._on_command)
        self.cmd_input.set_placeholder("💬 输入指令…（未来可在此与角色AI对话）")
        root.addWidget(self.cmd_input)

    # ========== NPC操作 ==========
    def _on_npc_option(self, npc_id: str, next_id: str, option_index: int) -> None:
        node = self.engine.dialogue_manager.start(npc_id)
        if not node or not node.options or option_index >= len(node.options):
            return
        opt = node.options[option_index]
        # 处理效果
        self.engine._apply_dialogue_effects(opt.effects or opt.on_enter or {})
        # 显示对话
        self.scene_view.append_text(f"\n—— {node.speaker} ——")
        self.scene_view.append_text(node.text)
        if opt.next_id:
            next_node = self.engine.dialogue_manager.choose(npc_id, node, option_index)
            if next_node:
                self.scene_view.append_text(f"\n—— {next_node.speaker} ——")
                self.scene_view.append_text(next_node.text)
        # 收起所有NPC
        for w in self.info_panel._npc_widgets:
            w.collapse()
        self._after_exec()

    def _on_scene_interact(self, action: str, target: str) -> None:
        if action == "explore":
            self._exec("探索")
        elif action == "look":
            self._exec(f"检查 {target}" if target else "查看周围")
        elif action == "rest":
            self._exec("休息")
        else:
            self._exec(f"{action} {target}".strip())

    # ========== 地图 ==========
    def _on_map_dialog(self) -> None:
        dlg = WorldMapDialog(self.engine.current_scene_id, self)
        dlg.travel_requested.connect(self._on_map_travel)
        dlg.exec()

    def _on_map_travel(self, scene_id: str) -> None:
        self._exec(f"前往 {scene_id}")

    # ========== 命令/执行 ==========
    def _on_command(self, text: str) -> None: self._exec(text)

    def _exec(self, text: str) -> None:
        self.scene_view.append_text(f"\n▸ {text}")
        cmd = self.engine.parser.parse(text)
        result = self.engine.execute(cmd)
        if result.text:
            self.scene_view.append_text(result.text)
        if result.combat_events:
            for ev in result.combat_events:
                line = ev.to_log_line()
                if line.strip():
                    self.scene_view.append_text(f"    {line}")
        self._after_exec()

    def _after_exec(self) -> None:
        self.party_panel.refresh(self.engine.party, self.engine.combat)
        self._refresh_all()
        self._update_combat_ui()
        if self.engine.combat:
            enemies = [e.info_dict() for e in self.engine.combat.enemies if e.is_alive]
            self.scene_view.monster_float.set_enemies(enemies)
        else:
            self.scene_view.monster_float.clear()

    # ========== 队员卡片 ==========
    def _on_member_card_clicked(self, idx: int) -> None:
        member = self.engine.party.get(idx)
        if member is None:
            return
        dlg = MemberDetailDialog(
            self.engine.party, self.engine.inventory,
            self.engine.auto_rules, self.engine.combat, self,
        )
        dlg.member_combo.setCurrentIndex(idx)
        dlg.item_equipped.connect(lambda i, m: self._equip(i, m))
        dlg.item_unequipped.connect(lambda i, m: self._unequip(i, m))
        dlg.item_used.connect(lambda i, m: self._exec(f"使用 {i} {m + 1}"))
        dlg.strategy_changed.connect(lambda s, n: self._set_strategy(s, n))
        dlg.rule_toggled.connect(lambda s, r: self.engine.auto_rules.toggle(s, r))
        dlg.rule_threshold.connect(lambda s, r, v: self.engine.auto_rules.set_threshold(s, r, v))
        dlg.exec()
        self.party_panel.refresh(self.engine.party, self.engine.combat)

    def _equip(self, iid, s): self.engine.inventory.equip(iid, s)
    def _unequip(self, iid, s): self.engine.inventory.unequip(iid, s)

    def _set_strategy(self, slot: int, name: str) -> None:
        if self.engine.combat:
            for s in StrategyType:
                if s.value == name:
                    self.engine.combat.set_strategy(slot, s)
                    break
        self.party_panel.refresh(self.engine.party, self.engine.combat)

    # ========== 战斗 ==========
    def _on_combat_round_btn(self) -> None:
        if not self.engine.combat: return
        events = self.engine.combat.auto_round()
        for ev in events:
            line = ev.to_log_line()
            if line.strip():
                self.scene_view.append_text(f"  {line}")
        r = self.engine.combat.check_end()
        if r: self.engine._finish_combat(r)
        self._after_exec()

    def _on_flee(self) -> None: self._exec("逃跑")

    def _on_combat_strategy(self, name: str) -> None:
        if self.engine.combat:
            for s in StrategyType:
                if s.value == name:
                    for i in range(4):
                        if self.engine.party.get(i):
                            self.engine.combat.set_strategy(i, s)
                    break
            self.party_panel.refresh(self.engine.party, self.engine.combat)

    # ========== 菜单 ==========
    def _on_new_game(self) -> None:
        dlg = CharacterCreateDialog(self)
        self._pending_created_char = None

        def on_created(char):
            self._pending_created_char = char
            self.engine.new_game(char)
            self.scene_view.set_text("新的冒险开始了！\n\n"
                                     "输入「帮助」查看可用指令。\n"
                                     "提示：前往酒馆招募同伴组建4人小队。")
            self.scene_view.append_text(
                f"\n✨ {char.name}（{char.race_name}{char.class_name}）已就绪！"
                f" HP:{char.hp_current}/{char.hp_max} MP:{char.mp_current}/{char.mp_max}")
            self._after_exec()

        dlg.character_created.connect(on_created)
        dlg.exec()

    def _on_save(self) -> None:
        r = self.engine.save_game(1, "快速存档")
        self.scene_view.append_text(r.text)
        self._refresh_all()

    def _on_load(self) -> None:
        saves = list_saves()
        if not saves:
            self.scene_view.append_text("没有可用的存档。")
            return
        r = self.engine.load_game(1)
        self.scene_view.append_text(r.text)
        self._on_scene_changed(self.engine.current_scene_id)

    def _on_about(self) -> None:
        QMessageBox.about(self, "关于龙焰传说",
                          "龙焰传说 v1.0\n\n"
                          "基于 D&D 规则的文字冒险游戏。\nPySide6 + SQLite 构建。")

    # ========== 战斗回调 ==========
    def _on_combat_started(self, c: Combat) -> None:
        self.scene_view.append_text(
            f"\n⚔ 遭遇敌人：{', '.join(e.name for e in c.enemies)}")
        self._update_combat_ui()
        self.scene_view.monster_float.set_enemies(
            [e.info_dict() for e in c.enemies])

    def _on_combat_round(self, events: list[CombatEvent]) -> None:
        for ev in events:
            line = ev.to_log_line()
            if line.strip():
                self.scene_view.append_text(f"    {line}")
        self.party_panel.refresh(self.engine.party, self.engine.combat)
        if self.engine.combat:
            self.scene_view.monster_float.set_enemies(
                [e.info_dict() for e in self.engine.combat.enemies if e.is_alive])

    def _on_combat_ended(self, result: CombatResult, loot: list[str],
                         xp: int, gold: int) -> None:
        if result == CombatResult.VICTORY:
            t = f"⚔ 战斗胜利！获得 {xp} 经验，{gold} 金币。"
            if loot: t += f"\n战利品：{', '.join(loot)}"
            self.scene_view.append_text(t)
        elif result == CombatResult.DEFEAT:
            self.scene_view.append_text("💀 全军覆没…请读取存档。")
        else:
            self.scene_view.append_text("你逃离了战斗。")
        self.scene_view.monster_float.clear()
        self._update_combat_ui()

    def _on_scene_changed(self, scene_id: str) -> None:
        scene = self.engine.world_map.get(scene_id)
        if scene:
            self.scene_view.set_scene(scene.name, scene.description)
        self._refresh_all()

    # ========== UI刷新 ==========
    def _update_combat_ui(self) -> None:
        self.combat_bar.setVisible(self.engine.combat is not None)

    def _refresh_all(self) -> None:
        inv = self.engine.inventory
        party = self.engine.party
        name = SCENE_NAMES.get(self.engine.current_scene_id,
                               self.engine.current_scene_id)
        saves = list_saves()

        # NPC数据
        npc_data = []
        scene = self.engine.world_map.get(self.engine.current_scene_id)
        if scene:
            from world.story import ALL_DIALOGUES
            for nid in scene.npcs:
                tree = ALL_DIALOGUES.get(nid)
                if tree:
                    greeting = self.engine.dialogue_manager.start(nid)
                    npc_data.append({"id": nid, "name": tree.npc_name,
                                     "greeting": greeting})

        self.info_panel.refresh(name, inv.gold, party.active_count(),
                                len(saves) > 0)
        self.info_panel.set_npcs(npc_data)

        # 任务
        quest_data = []
        from data.quests import ALL_QUESTS
        for qs in self.engine.quest_manager.active_quests():
            qdef = next((q for q in ALL_QUESTS if q.quest_id == qs.quest_id), None)
            if qdef:
                objs = []
                for obj in qs.objectives:
                    done = "✓" if obj.is_complete else "○"
                    objs.append(f"{done} {obj.description} ({obj.current_count}/{obj.target_count})")
                quest_data.append({
                    "id": qs.quest_id, "name": qdef.name,
                    "description": qdef.description[:80],
                    "objectives": objs,
                })
        self.info_panel.set_quests(quest_data)

        # 场景互动面板
        if scene:
            exits = {d: SCENE_NAMES.get(sid, sid)
                     for d, sid in scene.connections.items()}
            self.scene_interact.set_scene({
                "name": scene.name,
                "description": scene.description,
                "exits": exits,
                "interactables": scene.interactables,
            })
