"""游戏引擎 — 中央调度器"""

from dataclasses import dataclass, field
from typing import Callable

from core.party import Party
from core.character import Character
from core.inventory import Inventory
from core.combat import Combat, MonsterState, CombatEvent
from core.auto_rules import AutoRuleEngine
from core.quest import QuestManager, QuestDef, QuestStatus
from core.dialogue import DialogueManager
from data.monsters import MonsterTemplate, MONSTERS
from utils.constants import StrategyType, CombatResult, MessageCategory
from services.command_parser import Command, CommandParser, ActionCategory


@dataclass
class ActionResult:
    text: str
    category: MessageCategory = MessageCategory.INFO
    data: dict = field(default_factory=dict)          # 额外数据
    combat_events: list[CombatEvent] = field(default_factory=list)


@dataclass
class GameEngine:
    party: Party = field(default_factory=Party)
    inventory: Inventory = field(default_factory=Inventory)
    quest_manager: QuestManager = field(default_factory=QuestManager)
    dialogue_manager: DialogueManager = field(default_factory=DialogueManager)
    auto_rules: AutoRuleEngine = field(default_factory=AutoRuleEngine)
    combat: Combat | None = None
    current_scene_id: str = "river_town"
    story_flags: dict[str, bool] = field(default_factory=dict)
    defeated_bosses: set[str] = field(default_factory=set)
    parser: CommandParser = field(default_factory=CommandParser)

    # 回调 — UI层注册
    on_message: Callable[[str, MessageCategory], None] | None = None
    on_scene_change: Callable[[str], None] | None = None
    on_combat_start: Callable[[Combat], None] | None = None
    on_combat_round: Callable[[list[CombatEvent]], None] | None = None
    on_combat_end: Callable[[CombatResult, list[str], int, int], None] | None = None

    # ---- 主入口 ----
    def execute(self, command: Command) -> ActionResult:
        if self.combat is not None:
            return self._execute_combat(command)

        cat, action = command.category, command.action

        if cat == ActionCategory.MOVE:
            return self._move(command)
        elif cat == ActionCategory.COMBAT:
            return self._combat_cmd(command)
        elif cat == ActionCategory.INTERACT:
            return self._interact(command)
        elif cat == ActionCategory.ITEM:
            return self._item_cmd(command)
        elif cat == ActionCategory.INFO:
            return self._info(command)
        elif cat == ActionCategory.SYSTEM:
            return self._system(command)

        return ActionResult("未知命令，输入「帮助」查看可用指令。",
                            MessageCategory.WARNING)

    # ---- 移动 ----
    def _move(self, cmd: Command) -> ActionResult:
        # 占位 — v0.3 scenes 实现后完善
        return ActionResult(f"前往「{cmd.target}」— 场景系统待实现。")

    # ---- 战斗指令 ----
    def _combat_cmd(self, cmd: Command) -> ActionResult:
        if cmd.action == "flee":
            if self.combat:
                self.combat.result = CombatResult.RETREATED
                self.combat = None
                return ActionResult("你成功逃离了战斗！")
            return ActionResult("当前没有战斗。", MessageCategory.WARNING)
        return ActionResult("战斗中不可执行此操作。", MessageCategory.WARNING)

    def _execute_combat(self, cmd: Command) -> ActionResult:
        if cmd.action == "flee":
            self.combat.result = CombatResult.RETREATED
            self.combat = None
            return ActionResult("你成功逃离了战斗！")
        if cmd.action == "strategy":
            return self._set_strategy(cmd)
        # 手动使用道具
        if cmd.action == "use" and cmd.target:
            return self._manual_use_item(cmd)
        # 默认：执行一个自动回合
        events = self.combat.auto_round()
        if self.on_combat_round:
            self.on_combat_round(events)
        result = self.combat.check_end()
        if result:
            return self._finish_combat(result)
        return ActionResult("", data={}, combat_events=events)

    def _set_strategy(self, cmd: Command) -> ActionResult:
        """解析「策略 战士 全力」/「策略 2 保留法力」"""
        parts = cmd.target.split()
        if len(parts) < 2:
            return ActionResult("格式：「策略 队员名/编号 策略名」", MessageCategory.WARNING)
        # 查找队员
        idx = self._find_member_index(parts[0])
        if idx is None:
            return ActionResult(f"找不到队员: {parts[0]}", MessageCategory.WARNING)
        # 匹配策略
        strat_name = parts[1]
        strat = None
        for s in StrategyType:
            if s.value == strat_name or strat_name in s.value:
                strat = s
                break
        if strat is None:
            return ActionResult(f"未知策略: {strat_name}。可用：全力猛攻/平衡输出/保留法力/优先治疗/防御牵制",
                                MessageCategory.WARNING)
        self.combat.set_strategy(idx, strat)
        member = self.party.get(idx)
        return ActionResult(f"{member.name} 切换为「{strat.value}」")

    def _manual_use_item(self, cmd: Command) -> ActionResult:
        if not self.combat:
            return ActionResult("战斗中才能使用道具。", MessageCategory.WARNING)
        parts = cmd.target.split()
        item_name = parts[0]
        target_name = parts[1] if len(parts) > 1 else ""
        # 简单匹配
        from services.command_parser import ITEM_ALIASES
        item_id = ITEM_ALIASES.get(item_name, item_name)
        idx = self._find_member_index(target_name) if target_name else 0
        if idx is None:
            return ActionResult(f"找不到目标: {target_name}", MessageCategory.WARNING)
        effect = self.inventory.use_consumable(item_id, idx)
        if effect is None:
            return ActionResult(f"无法使用 {item_name}", MessageCategory.WARNING)
        member = self.party.get(idx)
        if member and "heal_hp" in effect:
            member.heal(effect["heal_hp"])
            return ActionResult(f"{member.name} 使用了{item_name}，恢复{effect['heal_hp']}HP",
                                MessageCategory.COMBAT)
        return ActionResult(f"使用了{item_name}")

    def _find_member_index(self, identifier: str) -> int | None:
        """根据名字或编号找队员"""
        if identifier.isdigit():
            i = int(identifier) - 1
            if 0 <= i < 4 and self.party.members[i]:
                return i
        for i, m in enumerate(self.party.members):
            if m and m.name == identifier:
                return i
        return None

    # ---- 交互 ----
    def _interact(self, cmd: Command) -> ActionResult:
        if cmd.action == "explore":
            return ActionResult("你仔细搜索了周围…没有发现特别的东西。\n[探索系统待场景数据完成后完善]")
        if cmd.action == "talk":
            return ActionResult(f"与「{cmd.target}」对话 — 对话系统待完善。")
        if cmd.action == "rest":
            self.party.rest_all()
            return ActionResult("队伍在篝火旁休息了一晚。HP/MP 已全部恢复。",
                                MessageCategory.SYSTEM)
        return ActionResult(f"「{cmd.raw}」— 暂未理解。输入「帮助」查看指令。",
                            MessageCategory.WARNING)

    # ---- 物品 ----
    def _item_cmd(self, cmd: Command) -> ActionResult:
        if cmd.action == "use":
            # 探索中使用道具
            parts = cmd.target.split()
            item_name = parts[0]
            target_name = parts[1] if len(parts) > 1 else ""
            from services.command_parser import ITEM_ALIASES
            item_id = ITEM_ALIASES.get(item_name, item_name)
            idx = self._find_member_index(target_name) if target_name else 0
            if idx is None:
                return ActionResult(f"找不到目标: {target_name}", MessageCategory.WARNING)
            effect = self.inventory.use_consumable(item_id, idx)
            if effect:
                member = self.party.get(idx)
                if member and "heal_hp" in effect:
                    member.heal(effect["heal_hp"])
                    return ActionResult(f"{member.name} 使用了{item_name}，恢复{effect['heal_hp']}HP")
            return ActionResult(f"无法使用 {item_name}", MessageCategory.WARNING)
        return ActionResult("物品操作待实现。")

    # ---- 信息 ----
    def _info(self, cmd: Command) -> ActionResult:
        if cmd.action == "help":
            return ActionResult(HELP_TEXT)
        if cmd.action == "status":
            return ActionResult(self._build_status_text())
        if cmd.action == "inventory":
            return ActionResult(self._build_inventory_text())
        if cmd.action == "quests":
            return ActionResult("任务日志待实现。")
        if cmd.action == "map":
            return ActionResult("地图待实现。")
        return ActionResult("未知查询。")

    def _build_status_text(self) -> str:
        lines = ["══════ 队伍状态 ══════"]
        for i, m in enumerate(self.party.members):
            if m:
                strat = self.combat.strategies.get(i, StrategyType.BALANCED).value \
                    if self.combat else "—"
                lines.append(
                    f"[{i + 1}] {m.name}  Lv.{m.level} {m.race_name}{m.class_name}\n"
                    f"    HP: {m.hp_current}/{m.hp_max}  MP: {m.mp_current}/{m.mp_max}\n"
                    f"    力量{m.final_attr('str'):2d} 敏捷{m.final_attr('dex'):2d} "
                    f"体质{m.final_attr('con'):2d} 智力{m.final_attr('int'):2d} "
                    f"感知{m.final_attr('wis'):2d} 魅力{m.final_attr('cha'):2d}"
                )
            else:
                lines.append(f"[{i + 1}] (空)")
        return "\n".join(lines)

    def _build_inventory_text(self) -> str:
        lines = [f"══════ 背包 (金币: {self.inventory.gold}) ══════"]
        items = self.inventory.backpack_items()
        if not items:
            lines.append("  (空)")
        else:
            for item in items:
                tmpl = item.template
                name = tmpl.name if tmpl else item.item_id
                lines.append(f"  {name} ×{item.quantity}")
        return "\n".join(lines)

    # ---- 系统 ----
    def _system(self, cmd: Command) -> ActionResult:
        if cmd.action == "save":
            slot = int(cmd.target) if cmd.target.isdigit() else 1
            return self.save_game(slot)
        if cmd.action == "load":
            slot = int(cmd.target) if cmd.target.isdigit() else 1
            return self.load_game(slot)
        return ActionResult("未知系统指令。")

    def save_game(self, slot: int = 1, slot_name: str = "") -> ActionResult:
        from services.save_service import save_game as do_save
        try:
            save_id = do_save(self, slot, slot_name)
            return ActionResult(f"游戏已保存到存档位 {slot}。",
                                MessageCategory.SYSTEM)
        except Exception as e:
            return ActionResult(f"存档失败: {e}", MessageCategory.DANGER)

    def load_game(self, slot: int = 1) -> ActionResult:
        from services.save_service import load_game as do_load
        try:
            if do_load(self, slot):
                self.combat = None
                return ActionResult(f"已从存档位 {slot} 读取游戏。",
                                    MessageCategory.SYSTEM)
            return ActionResult(f"存档位 {slot} 不存在。", MessageCategory.WARNING)
        except Exception as e:
            return ActionResult(f"读档失败: {e}", MessageCategory.DANGER)

    def new_game(self) -> ActionResult:
        from core.character import create_character
        self.party = Party()
        self.inventory = Inventory()
        self.combat = None
        self.story_flags = {}
        self.defeated_bosses = set()
        self.current_scene_id = "river_town"
        # 创建默认主角
        char = create_character("冒险者", "human", "warrior",
                                {"str": 14, "dex": 12, "con": 13, "int": 10, "wis": 10, "cha": 12})
        if isinstance(char, str):
            return ActionResult(f"创建角色失败: {char}", MessageCategory.DANGER)
        self.party.add_member(char, 0)
        return ActionResult("新的冒险开始了！输入「帮助」查看可用指令。\n"
                            "提示：前往酒馆招募同伴组建4人小队。")

    # ---- 战斗生命周期 ----
    def start_combat(self, enemy_ids: list[str]) -> Combat | None:
        enemies = []
        for eid in enemy_ids:
            tmpl = MONSTERS.get(eid)
            if tmpl:
                enemies.append(MonsterState(template=tmpl, hp_current=tmpl.hp,
                                            mp_current=tmpl.mp))
        if not enemies:
            return None
        # 确保 auto_rules 有所有队员的规则
        member_ids = [i for i, m in enumerate(self.party.members) if m is not None]
        if not self.auto_rules.member_rules:
            self.auto_rules = AutoRuleEngine.create_default(member_ids)

        self.combat = Combat(
            party=self.party,
            enemies=enemies,
            inventory=self.inventory,
            auto_rules=self.auto_rules,
        )
        if self.on_combat_start:
            self.on_combat_start(self.combat)
        return self.combat

    def _finish_combat(self, result: CombatResult) -> ActionResult:
        combat = self.combat
        self.combat = None

        if result == CombatResult.VICTORY:
            # 分配经验
            participants = [i for i, m in enumerate(self.party.members) if m and m.is_alive]
            msgs = self.party.distribute_xp(combat.total_xp, participants)
            self.inventory.gold += combat.total_gold

            # 战利品
            for item_id in combat.loot_items:
                self.inventory.add(item_id)

            text = f"⚔ 战斗胜利！获得 {combat.total_xp} 经验，{combat.total_gold} 金币。"
            if combat.loot_items:
                text += f"\n战利品：{', '.join(combat.loot_items)}"
            if msgs:
                text += "\n" + "\n".join(msgs)

            if self.on_combat_end:
                self.on_combat_end(result, combat.loot_items,
                                   combat.total_xp, combat.total_gold)
            return ActionResult(text, MessageCategory.LOOT)

        elif result == CombatResult.DEFEAT:
            if self.on_combat_end:
                self.on_combat_end(result, [], 0, 0)
            return ActionResult("💀 全军覆没…请读取存档。", MessageCategory.DANGER)

        else:  # RETREATED
            return ActionResult("你狼狈地逃离了战场。", MessageCategory.WARNING)


HELP_TEXT = """══════ 可用指令 ══════

【移动】前往 [地点]  |  返回  |  地图
【战斗】策略 [队员] [策略名]  |  集火 [目标]  |  逃跑
【交互】探索  |  对话 [NPC]  |  检查 [物品]  |  休息
【物品】背包  |  装备 [物品]  |  使用 [物品] [对象]  |  丢弃 [物品]
【信息】状态  |  任务  |  帮助
【系统】存档  |  读档

战斗策略：全力猛攻 / 平衡输出 / 保留法力 / 优先治疗 / 防御牵制"""
