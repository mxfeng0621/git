"""条件规则引擎 — 战斗中自动触发规则"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.character import Character

BUILTIN_RULES: dict[str, dict] = {
    "self_heal": {
        "name": "自保喝药",
        "desc": "自身HP低于阈值时自动使用治疗药水",
        "default_threshold": 30,
        "default_enabled": True,
    },
    "emergency_heal": {
        "name": "急救队友",
        "desc": "队友HP低于阈值时牧师施放单体治疗",
        "default_threshold": 20,
        "default_enabled": True,
    },
    "mana_saver": {
        "name": "法力红线",
        "desc": "自身MP低于阈值时切换为保留法力策略",
        "default_threshold": 10,
        "default_enabled": True,
    },
    "finish_off": {
        "name": "优先击杀",
        "desc": "场上有HP低于阈值的敌人时优先补刀",
        "default_threshold": 15,
        "default_enabled": True,
    },
    "boss_burst": {
        "name": "Boss爆发",
        "desc": "出现Boss级敌人时法师使用最强法术",
        "default_threshold": 0,
        "default_enabled": True,
    },
    "group_heal": {
        "name": "群体治疗",
        "desc": "多人HP低于阈值时牧师施放群体治疗",
        "default_threshold": 50,
        "default_enabled": True,
    },
}


@dataclass
class AutoRule:
    rule_id: str
    enabled: bool = True
    threshold: int = 30        # 触发阈值（百分比）


@dataclass
class AutoRuleEngine:
    """每个成员独立一套规则配置"""
    member_rules: dict[int, list[AutoRule]] = field(default_factory=dict)

    @classmethod
    def create_default(cls, member_ids: list[int]) -> "AutoRuleEngine":
        engine = cls()
        for mid in member_ids:
            engine.member_rules[mid] = []
            for rule_id, rule_def in BUILTIN_RULES.items():
                engine.member_rules[mid].append(AutoRule(
                    rule_id=rule_id,
                    enabled=rule_def["default_enabled"],
                    threshold=rule_def["default_threshold"],
                ))
        return engine

    def get_rules(self, member_id: int) -> list[AutoRule]:
        return self.member_rules.get(member_id, [])

    def toggle(self, member_id: int, rule_id: str) -> bool | None:
        rules = self.member_rules.get(member_id)
        if not rules:
            return None
        for r in rules:
            if r.rule_id == rule_id:
                r.enabled = not r.enabled
                return r.enabled
        return None

    def set_threshold(self, member_id: int, rule_id: str, value: int) -> bool:
        rules = self.member_rules.get(member_id)
        if not rules:
            return False
        for r in rules:
            if r.rule_id == rule_id:
                r.threshold = max(1, min(99, value))
                return True
        return False

    def evaluate(self, member_id: int, member: "Character",
                 combat_state: dict) -> str | None:
        """
        按优先级评估所有规则，返回触发的 rule_id，无触发返回 None。
        combat_state 结构见下。
        """
        rules = self.member_rules.get(member_id, [])
        if not rules:
            return None

        hp_pct = member.hp_current / max(member.hp_max, 1) * 100
        mp_pct = member.mp_current / max(member.mp_max, 1) * 100
        allies = combat_state.get("allies", [])
        enemies = combat_state.get("enemies", [])

        for rule in rules:
            if not rule.enabled:
                continue

            if rule.rule_id == "self_heal":
                if hp_pct < rule.threshold:
                    return "self_heal"

            elif rule.rule_id == "emergency_heal":
                if member.class_id == "cleric":
                    for ally in allies:
                        ally_hp_pct = ally.hp_current / max(ally.hp_max, 1) * 100
                        if ally_hp_pct < rule.threshold and ally.is_alive:
                            return "emergency_heal"

            elif rule.rule_id == "mana_saver":
                if mp_pct < rule.threshold:
                    return "mana_saver"

            elif rule.rule_id == "finish_off":
                for enemy in enemies:
                    enemy_hp_pct = enemy.get("hp_pct", 100)
                    if enemy_hp_pct < rule.threshold:
                        return "finish_off"

            elif rule.rule_id == "boss_burst":
                if member.class_id == "mage":
                    for enemy in enemies:
                        if enemy.get("tier") == "boss":
                            return "boss_burst"

            elif rule.rule_id == "group_heal":
                if member.class_id == "cleric":
                    low_count = sum(
                        1 for a in allies
                        if a.hp_current / max(a.hp_max, 1) * 100 < rule.threshold
                    )
                    if low_count >= 3:
                        return "group_heal"

        return None
