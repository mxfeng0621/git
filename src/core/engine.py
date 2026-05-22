"""游戏引擎 — 中央调度器"""

from dataclasses import dataclass, field
from typing import Callable

import random

from core.party import Party
from core.character import Character
from core.inventory import Inventory
from core.combat import Combat, MonsterState, CombatEvent
from core.auto_rules import AutoRuleEngine
from core.quest import QuestManager, QuestDef, QuestStatus
from core.dialogue import DialogueManager, DialogueNode
from data.monsters import MonsterTemplate, MONSTERS
from utils.constants import StrategyType, CombatResult, MessageCategory
from services.command_parser import Command, CommandParser, ActionCategory
from world.world_map import WorldMap


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
    world_map: WorldMap = field(default_factory=WorldMap)
    combat: Combat | None = None
    current_scene_id: str = "river_town"
    story_flags: dict[str, bool] = field(default_factory=dict)
    defeated_bosses: set[str] = field(default_factory=set)
    parser: CommandParser = field(default_factory=CommandParser)
    _pending_dialogue: DialogueNode | None = None   # 当前对话节点

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
        if self.combat:
            return ActionResult("战斗中无法移动！先结束战斗或逃跑。",
                                MessageCategory.WARNING)

        if cmd.action == "back":
            # 返回上一场景 — 简化实现：返回河畔镇
            if self.current_scene_id != "river_town":
                return self._travel_to("river_town")
            return ActionResult("你已经在家了。")

        target = cmd.target
        if not target:
            # 列出可去方向
            conns = self.world_map.get_connections(self.current_scene_id)
            if not conns:
                return ActionResult("这里没有路通往其他地方。")
            lines = ["你可以前往："]
            for direction, scene_id in conns.items():
                name = self.world_map.get_name(scene_id)
                lines.append(f"  · {direction} — {name}")
            return ActionResult("\n".join(lines))

        new_scene = self.world_map.move(self.current_scene_id, target)
        if new_scene is None:
            return ActionResult(f"无法从这里前往「{target}」。输入「前往」查看可去方向。",
                                MessageCategory.WARNING)
        return self._travel_to(new_scene)

    def _travel_to(self, scene_id: str) -> ActionResult:
        scene = self.world_map.get(scene_id)
        if not scene:
            return ActionResult("该地点不存在。", MessageCategory.WARNING)

        old_scene = self.current_scene_id
        self.current_scene_id = scene_id

        # 场景进入事件
        result_text = f"【{scene.name}】\n\n{scene.description}"
        events = scene.events

        if "on_enter" in events:
            ev = events["on_enter"]
            if ev["type"] == "combat":
                result_text += "\n\n⚔ 遭遇敌人！"
                self.start_combat(ev["enemy_ids"])

        # 随机遇敌
        if not self.combat and not scene.is_safe and scene.monster_spawns:
            spawn = self.world_map.monster_spawn(scene_id)
            if spawn:
                result_text += "\n\n⚔ 你遭遇了敌人！"
                self.start_combat(spawn)

        # 通知UI
        if self.on_scene_change:
            self.on_scene_change(scene_id)
        if self.on_message:
            self.on_message(result_text, MessageCategory.INFO)

        return ActionResult(result_text)

    # ---- 战斗指令（更新） ----
    def _combat_cmd(self, cmd: Command) -> ActionResult:
        if cmd.action == "flee":
            if self.combat:
                self.combat.result = CombatResult.RETREATED
                self.combat = None
                return ActionResult("你成功逃离了战斗！")
            return ActionResult("当前没有战斗。", MessageCategory.WARNING)
        # 战斗中的策略/集火/使用道具由 _execute_combat 处理
        if self.combat:
            return self._execute_combat(cmd)
        return ActionResult("当前没有战斗。", MessageCategory.WARNING)

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
            return self._do_explore()
        if cmd.action == "talk":
            return self._do_talk(cmd.target)
        if cmd.action == "pickup":
            return self._do_pickup(cmd.target)
        if cmd.action == "rest":
            return self._do_rest()
        if cmd.action == "custom":
            # 可能是一个数字选择（对话选项）
            return self._handle_custom(cmd.target)
        return ActionResult(f"「{cmd.raw}」— 暂未理解。输入「帮助」查看指令。",
                            MessageCategory.WARNING)

    def _do_explore(self) -> ActionResult:
        scene = self.world_map.get(self.current_scene_id)
        if not scene:
            return ActionResult("这里没什么可探索的。")

        events = scene.events
        if "on_search" in events:
            ev = events["on_search"]
            if ev.get("once") and self.story_flags.get(f"searched_{self.current_scene_id}"):
                pass  # 已搜索过
            else:
                self.story_flags[f"searched_{self.current_scene_id}"] = True
                if ev["type"] == "loot":
                    lines = ["你仔细搜索了周围……"]
                    for item in ev["items"]:
                        from core.dice import try_chance
                        if try_chance(item["chance"]):
                            self.inventory.add(item["item_id"])
                            from data.items import ITEMS
                            name = ITEMS.get(item["item_id"]).name if item["item_id"] in ITEMS else item["item_id"]
                            lines.append(f"✨ 发现了 {name}！")
                    if len(lines) == 1:
                        lines.append("没有找到特别的东西。")
                    self.quest_manager.progress("explore", self.current_scene_id, 1)
                    return ActionResult("\n".join(lines), MessageCategory.LOOT)

        # 随机发现
        import random
        if random.random() < 0.2:
            gold = random.randint(3, 15)
            self.inventory.gold += gold
            return ActionResult(f"你搜索了一番，找到了 {gold} 枚金币。",
                                MessageCategory.LOOT)

        self.quest_manager.progress("explore", self.current_scene_id, 1)
        return ActionResult("你仔细搜索了周围……没有发现特别的东西。")

    def _do_talk(self, target: str) -> ActionResult:
        if not target:
            return ActionResult("你想和谁对话？输入「对话 [名字]」。",
                                MessageCategory.WARNING)

        # 找NPC
        scene = self.world_map.get(self.current_scene_id)
        npc_id = None
        npc_name = target

        if scene:
            for nid in scene.npcs:
                from world.story import ALL_DIALOGUES
                if nid in ALL_DIALOGUES:
                    tree_name = ALL_DIALOGUES[nid].npc_name
                    if target in tree_name or target in nid:
                        npc_id = nid
                        npc_name = tree_name
                        break

        if not npc_id:
            return ActionResult(f"这里没有叫「{target}」的人。", MessageCategory.WARNING)

        node = self.dialogue_manager.start(npc_id)
        if not node:
            return ActionResult(f"{npc_name} 现在没什么可说的。")

        self._pending_dialogue = node
        return self._render_dialogue(npc_id, node)

    def _render_dialogue(self, npc_id: str, node: DialogueNode) -> ActionResult:
        lines = [f"—— {node.speaker} ——", "", node.text]

        # 处理节点进入效果
        if node.on_enter:
            self._apply_dialogue_effects(node.on_enter)

        if node.options:
            lines.append("")
            for i, opt in enumerate(node.options, 1):
                lines.append(f"  [{i}] {opt.text}")
            lines.append("")
            lines.append("输入选项编号回复。")
        self._pending_dialogue = node
        self._pending_npc_id = npc_id
        return ActionResult("\n".join(lines))

    def _handle_custom(self, text: str) -> ActionResult:
        """处理对话选项编号"""
        if not self._pending_dialogue:
            return ActionResult(f"「{text}」— 输入「帮助」查看可用指令。",
                                MessageCategory.WARNING)

        if text.isdigit():
            idx = int(text) - 1
            npc_id = getattr(self, '_pending_npc_id', '')
            next_node = self.dialogue_manager.choose(
                npc_id, self._pending_dialogue, idx)

            if next_node is None and idx >= len(self._pending_dialogue.options):
                self._pending_dialogue = None
                return ActionResult("对话结束。")

            # 处理选项效果 (兼容 effects 和 on_enter 两种写法)
            option = self._pending_dialogue.options[idx]
            eff = getattr(option, 'effects', None) or getattr(option, 'on_enter', {})
            self._apply_dialogue_effects(eff)

            if next_node:
                return self._render_dialogue(npc_id, next_node)
            else:
                self._pending_dialogue = None
                return ActionResult("对话结束。")

        # 可能是"离开"
        if text in ("离开", "再见", "结束"):
            self._pending_dialogue = None
            return ActionResult("你结束了对话。")

        return ActionResult("请输入选项编号，或输入「离开」结束对话。",
                            MessageCategory.WARNING)

    def _apply_dialogue_effects(self, effects: dict) -> None:
        if "start_quest" in effects:
            qid = effects["start_quest"]
            self.quest_manager.start(qid)
            from data.quests import ALL_QUESTS
            qdef = next((q for q in ALL_QUESTS if q.quest_id == qid), None)
            if qdef and self.on_message:
                self.on_message(f"📋 新任务：{qdef.name}", MessageCategory.LOOT)

        if "give_item" in effects:
            self.inventory.add(effects["give_item"])
            from data.items import ITEMS
            name = ITEMS.get(effects["give_item"]).name if effects["give_item"] in ITEMS else effects["give_item"]
            if self.on_message:
                self.on_message(f"✨ 获得：{name}", MessageCategory.LOOT)

        if "recruit" in effects:
            from core.character import create_character
            recruit_id = effects["recruit"]
            RECRUITS = {
                "merlin": ("梅林", "elf", "mage",
                           {"str": 8, "dex": 12, "con": 13, "int": 15, "wis": 12, "cha": 13}),
                "shade": ("影刃", "halfling", "rogue",
                          {"str": 10, "dex": 15, "con": 12, "int": 10, "wis": 11, "cha": 14}),
                "holy": ("圣光", "dwarf", "cleric",
                         {"str": 12, "dex": 8, "con": 15, "int": 10, "wis": 14, "cha": 10}),
            }
            if recruit_id in RECRUITS:
                name, race, cls, attrs = RECRUITS[recruit_id]
                char = create_character(name, race, cls, attrs)
                if not isinstance(char, str):
                    self.party.recruit(char)
                    if self.on_message:
                        self.on_message(f"✨ {name} 加入了队伍！", MessageCategory.LOOT)

    def _do_pickup(self, target: str) -> ActionResult:
        from data.items import ITEMS
        for item_id, tmpl in ITEMS.items():
            if target in tmpl.name or target in item_id:
                self.inventory.add(item_id)
                return ActionResult(f"拾取了 {tmpl.name}。", MessageCategory.LOOT)
        return ActionResult(f"这里没有「{target}」可以拾取。", MessageCategory.WARNING)

    def _do_rest(self) -> ActionResult:
        scene = self.world_map.get(self.current_scene_id)
        if scene and not scene.is_safe:
            return ActionResult("这里不安全，不能休息！找个安全的地方吧。",
                                MessageCategory.WARNING)
        self.party.rest_all()
        return ActionResult("队伍在安全的地方休息了。HP/MP 已全部恢复。",
                            MessageCategory.SYSTEM)

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
            return self._show_quests()
        if cmd.action == "map":
            return self._show_map()
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

    def _show_quests(self) -> ActionResult:
        from data.quests import ALL_QUESTS
        active = self.quest_manager.active_quests()
        if not active:
            return ActionResult("当前没有进行中的任务。\n去镇长宅邸或酒馆看看吧。")

        lines = ["══════ 任务日志 ══════"]
        for qs in active:
            qdef = next((q for q in ALL_QUESTS if q.quest_id == qs.quest_id), None)
            name = qdef.name if qdef else qs.quest_id
            lines.append(f"\n📋 {name}")
            if qdef:
                lines.append(f"   {qdef.description[:60]}…")
            for obj in qs.objectives:
                done = "✓" if obj.is_complete else "○"
                lines.append(f"   {done} {obj.description} ({obj.current_count}/{obj.target_count})")

        completed = [qid for qid in self.quest_manager.completed_ids]
        if completed:
            lines.append(f"\n已完成任务: {len(completed)} 个")

        return ActionResult("\n".join(lines))

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

    def _show_map(self) -> str:
        scene = self.world_map.get(self.current_scene_id)
        lines = [f"══════ 当前位置：{scene.name if scene else self.current_scene_id} ══════",
                 ""]
        if scene:
            lines.append("🌲 世界地图（已知区域）：")
            lines.append("")
            lines.append("  龙脊山脉 [未探索]")
            lines.append("      ↑")
            lines.append("  黑石城堡 [未探索]")
            lines.append("      ↑")
            lines.append("  废弃矿洞 [未探索]")
            lines.append("      ↑")
            lines.append("  森林深处 ← 幽暗森林 → 精灵遗迹")
            lines.append("      ↓           ↙")
            lines.append("  河畔镇 ★←你在这里→ 王国大道 [未解锁]")
            lines.append("")
            lines.append("可前往的方向：")
            for d, sid in scene.connections.items():
                name = self.world_map.get_name(sid)
                lines.append(f"  · {d} → {name}")
        return ActionResult("\n".join(lines))

    def new_game(self) -> ActionResult:
        from core.character import create_character
        from data.quests import ALL_QUESTS
        from world.story import ALL_DIALOGUES

        self.party = Party()
        self.inventory = Inventory()
        self.combat = None
        self.story_flags = {}
        self.defeated_bosses = set()
        self.current_scene_id = "river_town"
        self._pending_dialogue = None
        self._pending_npc_id = ""

        # 初始化任务
        self.quest_manager = QuestManager()
        self.quest_manager.init_from_defs(ALL_QUESTS)

        # 初始化对话
        self.dialogue_manager = DialogueManager()
        for npc_id, tree in ALL_DIALOGUES.items():
            self.dialogue_manager.register(tree)

        # 创建默认主角
        char = create_character("冒险者", "human", "warrior",
                                {"str": 14, "dex": 12, "con": 13, "int": 10, "wis": 10, "cha": 12})
        if isinstance(char, str):
            return ActionResult(f"创建角色失败: {char}", MessageCategory.DANGER)
        self.party.add_member(char, 0)

        # 初始场景文本
        scene = self.world_map.get("river_town")
        text = "新的冒险开始了！\n\n" + (scene.description if scene else "")

        return ActionResult(text + "\n\n输入「帮助」查看可用指令。\n"
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

【移动】前往 [地点/方向]  |  返回  |  地图
【战斗】策略 [队员] [策略名]  |  集火 [目标]  |  逃跑
【交互】探索  |  对话 [NPC名]  |  拾取 [物品]  |  休息
【物品】背包  |  装备 [物品]  |  使用 [物品] [对象]
【信息】状态  |  任务  |  帮助
【系统】存档  |  读档

战斗策略：全力猛攻 / 平衡输出 / 保留法力 / 优先治疗 / 防御牵制
探险提示：在酒馆招募同伴 → 去镇长宅邸接任务 → 出城向北进入森林"""
