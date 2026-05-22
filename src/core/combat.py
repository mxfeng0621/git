"""战斗引擎 — 策略驱动自动回合"""

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from core.dice import roll, try_chance, ability_modifier
from data.monsters import MonsterTemplate, MONSTERS, MonsterTier
from utils.constants import StrategyType, CombatResult

if TYPE_CHECKING:
    from core.character import Character
    from core.party import Party
    from core.inventory import Inventory
    from core.auto_rules import AutoRuleEngine


class CombatAction(Enum):
    ATTACK = "普攻"
    SKILL = "技能"
    HEAL = "治疗"
    DEFEND = "防御"
    ITEM = "道具"


@dataclass
class CombatEvent:
    actor_name: str
    action: str
    target_name: str
    damage: int = 0
    healing: int = 0
    is_critical: bool = False
    is_kill: bool = False
    text: str = ""

    def to_log_line(self) -> str:
        base = f"{self.actor_name}  {self.action} → {self.target_name}"
        if self.damage > 0:
            crit = "！暴击！" if self.is_critical else ""
            kill = " ✓击杀" if self.is_kill else ""
            return f"{base}，-{self.damage}HP{crit}{kill}"
        if self.healing > 0:
            return f"{base}，+{self.healing}HP"
        return base


@dataclass
class MonsterState:
    template: MonsterTemplate
    hp_current: int
    mp_current: int = 0
    temp_buffs: dict = field(default_factory=dict)    # {"atk_buff": 10, ...}
    temp_debuffs: dict = field(default_factory=dict)  # {"slow": 1, "dot": 3, ...}
    phase2: bool = False

    @property
    def name(self) -> str:
        return self.template.name

    @property
    def is_alive(self) -> bool:
        return self.hp_current > 0

    @property
    def hp_pct(self) -> int:
        return int(self.hp_current / max(self.template.hp, 1) * 100)

    @property
    def tier(self) -> str:
        return self.template.tier.value

    def take_damage(self, amount: int) -> int:
        self.hp_current = max(0, self.hp_current - amount)
        return self.hp_current

    def info_dict(self) -> dict:
        return {
            "name": self.name,
            "hp_current": self.hp_current,
            "hp_max": self.template.hp,
            "hp_pct": self.hp_pct,
            "tier": self.tier,
        }


@dataclass
class Combat:
    party: "Party"
    enemies: list[MonsterState]
    inventory: "Inventory"
    auto_rules: "AutoRuleEngine"
    strategies: dict[int, StrategyType] = field(default_factory=dict)
    round_number: int = 0
    log: list[CombatEvent] = field(default_factory=list)
    result: CombatResult | None = None
    total_xp: int = 0
    total_gold: int = 0
    loot_items: list[str] = field(default_factory=list)

    def __post_init__(self):
        # 默认策略：平衡输出
        for i, m in enumerate(self.party.members):
            if m and m.is_alive:
                self.strategies.setdefault(i, StrategyType.BALANCED)
        # 计算总奖励
        for enemy in self.enemies:
            tmpl = enemy.template
            self.total_xp += tmpl.xp_reward
            self.total_gold += random.randint(tmpl.gold_min, tmpl.gold_max)

    # ---- 策略设定 ----
    def set_strategy(self, member_index: int, strategy: StrategyType) -> None:
        self.strategies[member_index] = strategy

    def get_strategy(self, member_index: int) -> StrategyType:
        return self.strategies.get(member_index, StrategyType.BALANCED)

    # ---- 主循环 ----
    def auto_round(self) -> list[CombatEvent]:
        """执行一个完整回合，返回战斗事件列表"""
        self.round_number += 1
        events: list[CombatEvent] = []
        header = CombatEvent(
            actor_name="——", action="——", target_name="",
            text=f"━━━━ 第 {self.round_number} 回合 ━━━━",
        )

        # 玩家方行动（按敏捷排序）
        player_order = sorted(
            [i for i, m in enumerate(self.party.members) if m and m.is_alive],
            key=lambda i: self.party.members[i].final_attr("dex"), reverse=True,
        )
        for i in player_order:
            member = self.party.members[i]
            if not member.is_alive:
                continue

            # 1) 检查条件规则
            combat_state = self._build_combat_state()
            rule_triggered = self.auto_rules.evaluate(
                i, member, combat_state,
            )
            if rule_triggered:
                event = self._execute_rule(i, member, rule_triggered)
                if event:
                    events.append(event)
                    continue

            # 2) 按策略行动
            strategy = self.get_strategy(i)
            event = self._execute_strategy(i, member, strategy)
            if event:
                events.append(event)

        # 怪物方行动
        for enemy in self.enemies:
            if not enemy.is_alive:
                continue
            event = self._execute_monster(enemy)
            if event:
                events.append(event)

        # 回合后生效处理（dot等）
        dot_events = self._tick_effects()
        events.extend(dot_events)

        # 检查战斗结束
        self.check_end()

        return events

    def _build_combat_state(self) -> dict:
        return {
            "allies": [m for m in self.party.members if m is not None],
            "enemies": [e.info_dict() for e in self.enemies if e.is_alive],
            "round": self.round_number,
        }

    # ---- 条件规则执行 ----
    def _execute_rule(self, idx: int, member: "Character",
                      rule_id: str) -> CombatEvent | None:
        targets = [e for e in self.enemies if e.is_alive]

        if rule_id == "self_heal":
            potion = None
            for pid in ["health_potion_s", "health_potion_m", "health_potion_l"]:
                if self.inventory.count(pid) > 0:
                    potion = pid
                    break
            if potion:
                effect = self.inventory.use_consumable(potion, idx)
                if effect:
                    healed = member.heal(effect["heal_hp"])
                    return CombatEvent(
                        actor_name=member.name,
                        action=f"使用{ITEMS_NAME.get(potion, potion)}",
                        target_name="自己", healing=healed,
                        text=f"{member.name} 自动使用药水，恢复{healed}HP",
                    )

        elif rule_id == "emergency_heal":
            allies = [m for i, m in enumerate(self.party.members) if m and m.is_alive]
            lowest = min(allies, key=lambda a: a.hp_current / max(a.hp_max, 1))
            heal_skill = member.get_skill("heal")
            if heal_skill and member.mp_current >= heal_skill.mp_cost:
                member.spend_mp(heal_skill.mp_cost)
                heal_amt = member.heal_power(2.0)
                lowest.heal(heal_amt)
                return CombatEvent(
                    actor_name=member.name, action="治愈术(急救)",
                    target_name=lowest.name, healing=heal_amt,
                )

        elif rule_id == "mana_saver":
            self.strategies[idx] = StrategyType.CONSERVE_MANA
            return CombatEvent(
                actor_name=member.name, action="切换策略", target_name="",
                text=f"{member.name} 法力不足，切换为保留法力",
            )

        elif rule_id == "finish_off" and targets:
            low = min(targets, key=lambda e: e.hp_pct)
            return self._do_attack(member, low)

        elif rule_id == "boss_burst" and targets:
            boss = next((e for e in targets if e.template.tier == MonsterTier.BOSS), None)
            if boss:
                best_skill = None
                best_dmg = 0
                for s in member.unlocked_skills():
                    if s.mp_cost <= member.mp_current and s.damage_multiplier > best_dmg:
                        best_dmg = s.damage_multiplier
                        best_skill = s
                if best_skill:
                    return self._do_skill(member, best_skill, boss)

        elif rule_id == "group_heal":
            gheal = member.get_skill("group_heal")
            if gheal and member.mp_current >= gheal.mp_cost:
                member.spend_mp(gheal.mp_cost)
                total_heal = 0
                for m in self.party.members:
                    if m and m.is_alive:
                        total_heal += m.heal(member.heal_power(1.5))
                return CombatEvent(
                    actor_name=member.name, action="群体治疗",
                    target_name="全队", healing=total_heal,
                )

        return None

    # ---- 策略执行 ----
    def _execute_strategy(self, idx: int, member: "Character",
                          strategy: StrategyType) -> CombatEvent | None:
        targets = [e for e in self.enemies if e.is_alive]
        if not targets:
            return None

        if strategy == StrategyType.FULL_ASSAULT:
            return self._aggressive_action(member, targets)
        elif strategy == StrategyType.BALANCED:
            return self._balanced_action(member, targets)
        elif strategy == StrategyType.CONSERVE_MANA:
            return self._do_attack(member, random.choice(targets))
        elif strategy == StrategyType.PRIORITY_HEAL:
            return self._healer_action(member, targets)
        elif strategy == StrategyType.DEFEND:
            return self._defend_action(member, targets)
        return None

    def _aggressive_action(self, member, targets) -> CombatEvent:
        skills = [s for s in member.unlocked_skills()
                  if s.mp_cost <= member.mp_current and s.damage_multiplier > 1.0
                  and s.target_type in ("single", "all_enemy") and "taunt" not in s.extra_effects]
        if skills:
            best = max(skills, key=lambda s: s.damage_multiplier)
            return self._do_skill(member, best, random.choice(targets))
        return self._do_attack(member, random.choice(targets))

    def _balanced_action(self, member, targets) -> CombatEvent:
        mp_pct = member.mp_current / max(member.mp_max, 1)
        if mp_pct > 0.3:
            skills = [s for s in member.unlocked_skills()
                      if s.mp_cost <= member.mp_current and s.damage_multiplier >= 0.8
                      and "taunt" not in s.extra_effects
                      and s.target_type in ("single", "all_enemy")]
            if skills and random.random() > 0.5:
                return self._do_skill(member, random.choice(skills),
                                      random.choice(targets))
        return self._do_attack(member, random.choice(targets))

    def _healer_action(self, member, targets) -> CombatEvent:
        injured = [m for i, m in enumerate(self.party.members)
                   if m and m.is_alive and m.hp_current / max(m.hp_max, 1) < 0.6]
        if injured:
            target = min(injured, key=lambda m: m.hp_current / max(m.hp_max, 1))
            heal_skill = member.get_skill("heal")
            if heal_skill and member.mp_current >= heal_skill.mp_cost:
                member.spend_mp(heal_skill.mp_cost)
                healed = target.heal(member.heal_power(2.0))
                return CombatEvent(
                    actor_name=member.name, action="治愈术",
                    target_name=target.name, healing=healed,
                )
        return self._do_attack(member, random.choice(targets)) if targets else None

    def _defend_action(self, member, targets) -> CombatEvent:
        taunt_skill = member.get_skill("taunt")
        if taunt_skill and member.mp_current >= taunt_skill.mp_cost:
            member.spend_mp(taunt_skill.mp_cost)
            return CombatEvent(
                actor_name=member.name, action="挑衅",
                target_name=random.choice(targets).name,
                text=f"{member.name} 使用挑衅，敌人被迫攻击自己！",
            )
        return self._do_attack(member, random.choice(targets))

    def _do_attack(self, member, target) -> CombatEvent:
        weapon = self.inventory.equipment_bonuses(member.slot_index)
        dice = weapon.get("damage_dice", "1d4")
        base_dmg = member.physical_damage(dice)

        # 暴击判定
        crit_chance = 5 + member.attr_mod("dex")
        is_crit = try_chance(crit_chance)
        if is_crit:
            base_dmg = int(base_dmg * 2)

        # 护甲减免
        armor = target.template.armor + target.template.constitution // 3
        dmg = max(1, base_dmg - armor)

        target.take_damage(dmg)
        is_kill = not target.is_alive

        return CombatEvent(
            actor_name=member.name, action="普攻",
            target_name=target.name, damage=dmg,
            is_critical=is_crit, is_kill=is_kill,
        )

    def _do_skill(self, member, skill, target) -> CombatEvent:
        member.spend_mp(skill.mp_cost)
        base = member.spell_damage(10, skill.damage_multiplier)
        armor = target.template.armor

        # 破甲无视
        if "ignore_armor_pct" in skill.extra_effects:
            armor = armor * (1 - skill.extra_effects["ignore_armor_pct"] / 100)

        dmg = max(1, int(base) - int(armor))
        target.take_damage(dmg)

        # 附加效果
        if "slow" in skill.extra_effects:
            target.temp_debuffs["slow"] = skill.extra_effects["slow"]
        if "dot" in skill.extra_effects:
            target.temp_debuffs["dot"] = skill.extra_effects["dot"]

        return CombatEvent(
            actor_name=member.name, action=skill.name,
            target_name=target.name, damage=dmg,
            is_kill=not target.is_alive,
        )

    # ---- 怪物行动 ----
    def _execute_monster(self, enemy: MonsterState) -> CombatEvent | None:
        living = [m for m in self.party.members if m and m.is_alive]
        if not living:
            return None

        behavior = enemy.template.behavior.value
        target = living[0]

        if behavior == "fierce":
            target = min(living, key=lambda m: m.hp_current)
        elif behavior == "tactical":
            front = self.party.front_row()
            front_living = [self.party.get(i) for i in front
                            if self.party.get(i) and self.party.get(i).is_alive]
            target = front_living[0] if front_living else living[0]
            if enemy.hp_pct < 30:
                return CombatEvent(
                    actor_name=enemy.name, action="逃跑", target_name="",
                    text=f"{enemy.name} 受伤过重，逃跑了！",
                )
        elif behavior == "relentless":
            pass  # 攻击最近的（第一个活着的）
        elif behavior == "boss_ai":
            if not enemy.phase2 and enemy.hp_pct < 50:
                enemy.phase2 = True
                if enemy.template.skills:
                    for sk in enemy.template.skills:
                        if "phase2_buff" in sk:
                            enemy.temp_buffs["atk"] = sk["phase2_buff"]
                            return CombatEvent(
                                actor_name=enemy.name, action="狂怒",
                                target_name="", text=f"{enemy.name} 进入狂暴阶段！攻击力+30%",
                            )

        # 怪物攻击
        base_dmg = roll(enemy.template.damage_dice) + ability_modifier(enemy.template.strength)
        atk_buff = enemy.temp_buffs.get("atk", 0)
        base_dmg = int(base_dmg * (1 + atk_buff / 100))
        dmg = max(1, base_dmg - ability_modifier(target.final_attr("con")))
        target.take_damage(dmg)

        return CombatEvent(
            actor_name=enemy.name, action="攻击",
            target_name=target.name, damage=dmg,
            is_kill=not target.is_alive,
        )

    # ---- 持续效果 ----
    def _tick_effects(self) -> list[CombatEvent]:
        events: list[CombatEvent] = []
        for enemy in self.enemies:
            if not enemy.is_alive:
                continue
            dot = enemy.temp_debuffs.get("dot", 0)
            if dot:
                enemy.take_damage(dot)
                events.append(CombatEvent(
                    actor_name="", action="中毒伤害", target_name=enemy.name,
                    damage=dot, text=f"{enemy.name} 受到中毒伤害 {dot} 点",
                ))
        return events

    # ---- 结束判定 ----
    def check_end(self) -> CombatResult | None:
        if all(not e.is_alive for e in self.enemies):
            self.result = CombatResult.VICTORY
            self._calc_loot()
            return self.result
        if self.party.all_dead():
            self.result = CombatResult.DEFEAT
            return self.result
        return None

    def _calc_loot(self) -> None:
        for enemy in self.enemies:
            for loot in enemy.template.loot_table:
                if try_chance(loot["chance"]):
                    self.loot_items.append(loot["item_id"])


# 辅助
ITEMS_NAME: dict[str, str] = {
    "health_potion_s": "小型治疗药水",
    "health_potion_m": "中型治疗药水",
    "health_potion_l": "大型治疗药水",
}
