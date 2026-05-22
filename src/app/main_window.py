"""主窗口 — 完整UI集成"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSplitter, QMessageBox, QFrame, QStackedWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from app.styles import MAIN_STYLE
from core.engine import GameEngine
from core.combat import Combat, CombatEvent
from services.save_service import list_saves, delete_save
from ui.party_panel import PartyPanel
from ui.scene_view import SceneView
from ui.log_panel import LogPanel
from ui.command_input import CommandInput
from ui.inventory_dialog import InventoryDialog
from ui.combat_widget import CombatWidget
from utils.constants import StrategyType, CombatResult, MessageCategory

SCENE_NAMES = {
    "river_town": "河畔镇",
    "dark_forest": "幽暗森林",
    "abandoned_mine": "废弃矿洞",
    "black_castle": "黑石城堡",
    "dragon_peak": "龙脊山脉",
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("龙焰传说 — DND文字冒险")
        self.resize(1280, 800)
        self.setMinimumSize(960, 600)
        self.setStyleSheet(MAIN_STYLE)

        self.engine = GameEngine()
        self._setup_engine_callbacks()

        self._build_menu_bar()
        self._build_central()
        self._build_status_bar()

        self._log_system("欢迎来到龙焰传说！点击「游戏 → 新游戏」开始冒险。")

    # ========== 引擎回调 ==========
    def _setup_engine_callbacks(self) -> None:
        self.engine.on_message = lambda text, cat: self.log_panel.log(text, cat)
        self.engine.on_scene_change = lambda scene_id: self._on_scene_changed(scene_id)
        self.engine.on_combat_start = lambda c: self._on_combat_started(c)
        self.engine.on_combat_round = lambda events: self._on_combat_round(events)
        self.engine.on_combat_end = lambda result, loot, xp, gold: \
            self._on_combat_ended(result, loot, xp, gold)

    # ========== 菜单栏 ==========
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

    # ========== 中央区域 ==========
    def _build_central(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(4)

        # ---- 上部 ----
        top_splitter = QSplitter(Qt.Horizontal)

        self.party_panel = PartyPanel()
        top_splitter.addWidget(self.party_panel)

        self.scene_view = SceneView()
        top_splitter.addWidget(self.scene_view)

        # 右侧：操作按钮 + 战斗面板（切换）
        self.right_stack = QStackedWidget()

        self.action_panel = self._build_action_panel()
        self.right_stack.addWidget(self.action_panel)      # index 0

        self.combat_widget = CombatWidget()
        self.combat_widget.strategy_changed.connect(self._on_strategy_changed)
        self.combat_widget.round_requested.connect(self._on_combat_round_manual)
        self.combat_widget.flee_requested.connect(self._on_flee)
        self.combat_widget.hide()
        self.right_stack.addWidget(self.combat_widget)     # index 1

        self.right_stack.setCurrentIndex(0)
        top_splitter.addWidget(self.right_stack)

        top_splitter.setSizes([220, 680, 180])
        root.addWidget(top_splitter, stretch=3)

        # ---- 下部 ----
        bottom_splitter = QSplitter(Qt.Vertical)

        self.log_panel = LogPanel()
        bottom_splitter.addWidget(self.log_panel)

        self.cmd_input = CommandInput()
        self.cmd_input.command_entered.connect(self._on_command)
        bottom_splitter.addWidget(self.cmd_input)

        bottom_splitter.setSizes([220, 42])
        root.addWidget(bottom_splitter, stretch=1)

    def _build_action_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("action_panel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        title = QLabel("操作")
        title.setObjectName("title")
        layout.addWidget(title)

        buttons = [
            ("探索", self._on_explore),
            ("休息", self._on_rest),
            ("背包", self._on_inventory),
            ("地图", self._on_map),
            ("任务", self._on_quests),
            ("状态", self._on_status),
        ]
        for text, slot in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            layout.addWidget(btn)

        layout.addStretch()
        return frame

    # ========== 状态栏 / 信息栏 ==========
    def _build_status_bar(self) -> None:
        bar = self.statusBar()
        bar.setStyleSheet(
            "QStatusBar { background: #16213e; border-top: 1px solid #c9a96e; "
            "padding: 2px 8px; font-size: 12px; }"
        )

        # 场景
        self.bar_scene = QLabel("河畔镇")
        self.bar_scene.setStyleSheet("color: #c9a96e; font-weight: bold; padding: 0 10px;")
        bar.addWidget(self.bar_scene)

        bar.addWidget(self._bar_sep())

        # 金币
        self.bar_gold = QLabel("0 G")
        self.bar_gold.setStyleSheet("color: #f0a500; font-weight: bold; padding: 0 10px;")
        bar.addWidget(self.bar_gold)

        bar.addWidget(self._bar_sep())

        # 队伍
        self.bar_party = QLabel("0/4 人")
        self.bar_party.setStyleSheet("color: #8ecae6; padding: 0 10px;")
        bar.addWidget(self.bar_party)

        bar.addWidget(self._bar_sep())

        # 存档状态
        self.bar_save = QLabel("未保存")
        self.bar_save.setStyleSheet("color: #6c757d; padding: 0 10px;")
        bar.addWidget(self.bar_save)

        bar.addPermanentWidget(QLabel(""))  # 弹簧

        # 提示
        self.bar_hint = QLabel("输入「帮助」查看指令")
        self.bar_hint.setStyleSheet("color: #4a3f35; padding: 0 10px;")
        bar.addPermanentWidget(self.bar_hint)

    def _bar_sep(self) -> QLabel:
        sep = QLabel("│")
        sep.setStyleSheet("color: #4a3f35; padding: 0 2px;")
        return sep

    def refresh_info_bar(self) -> None:
        """刷新信息栏"""
        inv = self.engine.inventory
        party = self.engine.party

        # 场景名
        scene_name = SCENE_NAMES.get(self.engine.current_scene_id,
                                     self.engine.current_scene_id)
        self.bar_scene.setText(f"📍 {scene_name}")

        # 金币
        self.bar_gold.setText(f"💰 {inv.gold} G")

        # 队伍
        count = party.active_count()
        self.bar_party.setText(f"👥 {count}/4 人")

        # 存档状态
        from services.save_service import list_saves
        saves = list_saves()
        self.bar_save.setText("💾 已存档" if saves else "未保存")

    # ========== 菜单槽 ==========
    def _on_new_game(self) -> None:
        result = self.engine.new_game()
        self.log_panel.log_system(result.text)
        self.party_panel.refresh(self.engine.party)
        self._show_explore_mode()
        self.refresh_info_bar()

    def _on_save(self) -> None:
        result = self.engine.save_game(1, "快速存档")
        self.log_panel.log_system(result.text)
        self.refresh_info_bar()

    def _on_load(self) -> None:
        saves = list_saves()
        if not saves:
            self.log_panel.log_system("没有可用的存档。")
            return
        result = self.engine.load_game(1)
        self.log_panel.log_system(result.text)
        self.party_panel.refresh(self.engine.party)
        self._show_explore_mode()
        self.refresh_info_bar()

    def _on_about(self) -> None:
        QMessageBox.about(self, "关于龙焰传说",
                          "龙焰传说 v0.4\n\n"
                          "基于 D&D 规则的文字冒险游戏。\n"
                          "PySide6 + SQLite 构建。")

    # ========== 按钮槽 ==========
    def _on_explore(self) -> None:
        self.log_panel.log_command("探索")
        self._execute_text("探索")

    def _on_rest(self) -> None:
        self.log_panel.log_command("休息")
        self._execute_text("休息")

    def _on_inventory(self) -> None:
        dlg = InventoryDialog(self.engine, self)
        dlg.item_used.connect(self._on_item_used)
        dlg.item_equipped.connect(self._on_item_equipped)
        dlg.item_unequipped.connect(self._on_item_unequipped)
        dlg.item_discarded.connect(self._on_item_discarded)
        dlg.refresh()
        dlg.exec()
        self.party_panel.refresh(self.engine.party)

    def _on_map(self) -> None:
        self._execute_text("地图")

    def _on_quests(self) -> None:
        self._execute_text("任务")

    def _on_status(self) -> None:
        self._execute_text("状态")

    # ========== 物品操作 ==========
    def _on_item_used(self, item_id: str, target_idx: int) -> None:
        from data.items import ITEMS
        from services.command_parser import ITEM_ALIASES
        name = ITEMS.get(item_id).name if item_id in ITEMS else item_id
        cmd = f"使用 {name} {target_idx + 1}"
        self._execute_text(cmd)

    def _on_item_equipped(self, item_id: str, target_idx: int) -> None:
        if self.engine.inventory.equip(item_id, target_idx):
            tmpl = self.engine.inventory.items[-1].template
            name = tmpl.name if tmpl else item_id
            member = self.engine.party.get(target_idx)
            self.log_panel.log_loot(f"{member.name} 装备了 {name}")
            self.party_panel.refresh(self.engine.party)

    def _on_item_unequipped(self, item_id: str, target_idx: int) -> None:
        if self.engine.inventory.unequip(item_id, target_idx):
            from data.items import ITEMS
            name = ITEMS.get(item_id).name if item_id in ITEMS else item_id
            self.log_panel.log_system(f"卸下了 {name}")

    def _on_item_discarded(self, item_id: str) -> None:
        if self.engine.inventory.remove(item_id, 1):
            from data.items import ITEMS
            name = ITEMS.get(item_id).name if item_id in ITEMS else item_id
            self.log_panel.log_system(f"丢弃了 {name}")

    # ========== 命令执行 ==========
    def _on_command(self, text: str) -> None:
        self.log_panel.log_command(text)
        self._execute_text(text)

    def _execute_text(self, text: str) -> None:
        cmd = self.engine.parser.parse(text)
        result = self.engine.execute(cmd)
        if result.text:
            self.log_panel.log(result.text, result.category)
        # 战斗事件
        if result.combat_events:
            for ev in result.combat_events:
                line = ev.to_log_line()
                if line.strip():
                    self.log_panel.log_combat(f"  {line}")
        # 更新面板
        self.party_panel.refresh(self.engine.party, self.engine.combat)
        if self.engine.combat and self.engine.combat.result is None:
            self._update_combat_enemies()
        self.refresh_info_bar()

    # ========== 战斗回调 ==========
    def _on_combat_started(self, combat: Combat) -> None:
        self._show_combat_mode(combat)
        self.log_panel.log_danger(
            f"⚔ 遭遇敌人！{', '.join(e.name for e in combat.enemies)}")

    def _on_combat_round(self, events: list[CombatEvent]) -> None:
        for ev in events:
            line = ev.to_log_line()
            if line.strip():
                self.log_panel.log_combat(f"  {line}")
        if self.engine.combat:
            self._update_combat_enemies()
        self.party_panel.refresh(self.engine.party, self.engine.combat)

    def _on_combat_round_manual(self) -> None:
        """手动触发回合"""
        if not self.engine.combat:
            return
        events = self.engine.combat.auto_round()
        self._on_combat_round(events)
        result = self.engine.combat.check_end()
        if result:
            self.engine._finish_combat(result)
            # _finish_combat 已经通过 on_combat_end 回调处理了 UI

    def _on_combat_ended(self, result: CombatResult, loot: list[str],
                         xp: int, gold: int) -> None:
        if result == CombatResult.VICTORY:
            text = f"⚔ 战斗胜利！获得 {xp} 经验，{gold} 金币。"
            if loot:
                text += f"\n战利品：{', '.join(loot)}"
            self.log_panel.log_loot(text)
        elif result == CombatResult.DEFEAT:
            self.log_panel.log_danger("💀 全军覆没…请读取存档。")
        else:
            self.log_panel.log_system("你逃离了战斗。")

        self._show_explore_mode()
        self.party_panel.refresh(self.engine.party)

    def _on_strategy_changed(self, idx: int, name: str) -> None:
        if self.engine.combat:
            for s in StrategyType:
                if s.value == name:
                    self.engine.combat.set_strategy(idx, s)
                    member = self.engine.party.get(idx)
                    if member:
                        self.log_panel.log_combat(f"{member.name} 策略→{name}")
                    break
            self.party_panel.refresh(self.engine.party, self.engine.combat)

    def _on_flee(self) -> None:
        if self.engine.combat:
            self.engine.combat.result = CombatResult.RETREATED
            self.log_panel.log_system("你逃离了战斗。")
            self._show_explore_mode()

    def _update_combat_enemies(self) -> None:
        if self.engine.combat:
            enemies = [e.info_dict() for e in self.engine.combat.enemies if e.is_alive]
            self.combat_widget.set_enemies(enemies)

    # ========== 模式切换 ==========
    def _show_combat_mode(self, combat: Combat) -> None:
        self.right_stack.setCurrentIndex(1)
        self.combat_widget.show()
        enemies = [e.info_dict() for e in combat.enemies]
        self.combat_widget.set_enemies(enemies)
        # 同步当前策略到下拉框
        for i, m in enumerate(self.engine.party.members):
            if m:
                s = combat.get_strategy(i)
                self.combat_widget.set_strategy(i, s.value)

    def _show_explore_mode(self) -> None:
        self.right_stack.setCurrentIndex(0)
        self.combat_widget.hide()
        self.refresh_info_bar()

    def _on_scene_changed(self, scene_id: str) -> None:
        self.refresh_info_bar()

    def _log_system(self, text: str) -> None:
        self.log_panel.log_system(text)
