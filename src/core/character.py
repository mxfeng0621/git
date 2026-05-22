"""角色数据模型"""

from dataclasses import dataclass, field
from data.classes import CLASSES, ClassData, SkillDef
from data.races import RACES, RacialData
from utils.constants import ATTR_MIN, ATTR_MAX, LEVEL_CAP, POINT_BUY_COST, TOTAL_POINTS
from core.dice import ability_modifier


@dataclass
class Character:
    name: str
    race_id: str
    class_id: str
    level: int = 1
    xp: int = 0
    attributes: dict[str, int] = field(default_factory=lambda: {
        "str": 8, "dex": 8, "con": 8, "int": 8, "wis": 8, "cha": 8,
    })
    hp_current: int = 0
    hp_max: int = 0
    mp_current: int = 0
    mp_max: int = 0
    is_main: bool = False
    slot_index: int = 0
    affinity: dict[str, int] = field(default_factory=dict)  # npc_id → 好感值(0-100)

    def __post_init__(self):
        if self.hp_max == 0:
            self.recalc_stats()
            self.hp_current = self.hp_max
            self.mp_current = self.mp_max

    # ---- 模板引用 ----
    @property
    def class_data(self) -> ClassData:
        return CLASSES[self.class_id]

    @property
    def race_data(self) -> RacialData:
        return RACES[self.race_id]

    @property
    def class_name(self) -> str:
        return self.class_data.name

    @property
    def race_name(self) -> str:
        return self.race_data.name

    # ---- 含种族加成的最终属性 ----
    def final_attr(self, attr: str) -> int:
        base = self.attributes.get(attr, 8)
        racial_bonus = self.race_data.attr_bonus.get(attr, 0)
        return min(base + racial_bonus, ATTR_MAX + self.race_data.attr_bonus.get(attr, 0))

    def attr_mod(self, attr: str) -> int:
        return ability_modifier(self.final_attr(attr))

    # ---- 血量/法力重算 ----
    def recalc_stats(self) -> None:
        cd = self.class_data
        con_mod = self.attr_mod("con")
        wis_mod = self.attr_mod("wis")
        self.hp_max = 20 + (cd.hp_per_level + con_mod) * self.level
        self.mp_max = 10 + (cd.mp_per_level + max(wis_mod, 0)) * self.level

    # ---- 经验与升级 ----
    def xp_to_next(self) -> int:
        return self.level * 1000

    def add_xp(self, amount: int) -> bool:
        """返回是否升级"""
        if self.level >= LEVEL_CAP:
            return False
        self.xp += amount
        leveled = False
        while self.xp >= self.xp_to_next() and self.level < LEVEL_CAP:
            self.xp -= self.xp_to_next()
            self.level += 1
            leveled = True
        if leveled:
            self.recalc_stats()
            self.hp_current = self.hp_max
            self.mp_current = self.mp_max
        return leveled

    # ---- 已解锁技能 ----
    def unlocked_skills(self) -> list[SkillDef]:
        skills: list[SkillDef] = []
        for lv, skill_list in self.class_data.skill_table.items():
            if self.level >= lv:
                skills.extend(skill_list)
        return skills

    def get_skill(self, skill_id: str) -> SkillDef | None:
        for s in self.unlocked_skills():
            if s.skill_id == skill_id:
                return s
        return None

    # ---- 伤害/治疗计算 ----
    def physical_damage(self, weapon_dice: str = "1d4") -> int:
        from core.dice import roll
        base = roll(weapon_dice)
        return max(1, base + self.attr_mod("str"))

    def spell_damage(self, base_damage: int, multiplier: float = 1.0) -> int:
        dmg = base_damage + self.attr_mod("int")
        return max(1, int(dmg * multiplier))

    def heal_power(self, mult: float = 1.0) -> int:
        return max(1, int(self.final_attr("wis") * mult))

    # ---- 生存状态 ----
    @property
    def is_alive(self) -> bool:
        return self.hp_current > 0

    def take_damage(self, amount: int) -> int:
        self.hp_current = max(0, self.hp_current - amount)
        return self.hp_current

    def heal(self, amount: int) -> int:
        self.hp_current = min(self.hp_max, self.hp_current + amount)
        return self.hp_current

    def spend_mp(self, amount: int) -> bool:
        if self.mp_current >= amount:
            self.mp_current -= amount
            return True
        return False

    def restore_mp(self, amount: int) -> int:
        self.mp_current = min(self.mp_max, self.mp_current + amount)
        return self.mp_current

    def rest(self) -> None:
        """长休：HP/MP回满"""
        self.hp_current = self.hp_max
        self.mp_current = self.mp_max


# ---- 购点工具 ----
def validate_point_buy(attributes: dict[str, int]) -> tuple[bool, int, str]:
    """返回 (合法, 已花费点数, 错误信息)"""
    total = 0
    for attr in ["str", "dex", "con", "int", "wis", "cha"]:
        val = attributes.get(attr, 8)
        if val < ATTR_MIN or val > ATTR_MAX:
            return False, 0, f"{attr} 必须在 {ATTR_MIN}-{ATTR_MAX} 之间"
        total += POINT_BUY_COST[val]
    if total > TOTAL_POINTS:
        return False, total, f"花费 {total} 点，超出上限 {TOTAL_POINTS}"
    return True, total, ""


def create_character(name: str, race_id: str, class_id: str,
                     attributes: dict[str, int]) -> Character | str:
    """工厂函数，返回 Character 或错误信息字符串"""
    if race_id not in RACES:
        return f"未知种族: {race_id}"
    if class_id not in CLASSES:
        return f"未知职业: {class_id}"
    valid, spent, err = validate_point_buy(attributes)
    if not valid:
        return err
    return Character(name=name, race_id=race_id, class_id=class_id, attributes=attributes)
