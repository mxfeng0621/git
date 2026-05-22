"""职业升级表 — 固定技能解锁"""

from dataclasses import dataclass, field


@dataclass
class SkillDef:
    skill_id: str
    name: str
    description: str
    mp_cost: int = 0
    cooldown: int = 0
    damage_multiplier: float = 1.0
    target_type: str = "single"          # single / all_enemy / all_ally / self
    extra_effects: dict = field(default_factory=dict)


@dataclass
class ClassData:
    class_id: str
    name: str
    description: str
    hp_per_level: int
    mp_per_level: int
    primary_attr: str                    # "str" / "dex" / "int" / "wis"
    skill_table: dict[int, list[SkillDef]]


CLASSES: dict[str, ClassData] = {
    "warrior": ClassData(
        class_id="warrior", name="战士", description="前排坦克，物理输出核心。",
        hp_per_level=12, mp_per_level=3, primary_attr="str",
        skill_table={
            1: [
                SkillDef("heavy_armor", "重甲精通", "装备重甲无速度惩罚", target_type="self"),
                SkillDef("taunt", "挑衅", "强制单体敌人攻击自己，持续2回合", target_type="single",
                         extra_effects={"taunt": 2}),
            ],
            3: [SkillDef("heavy_strike", "猛击", "单体120%物理伤害", mp_cost=8,
                         damage_multiplier=1.2)],
            5: [SkillDef("extra_attack", "额外攻击", "每回合可攻击2次", target_type="self")],
            7: [SkillDef("armor_break", "破甲斩", "无视目标50%护甲值", mp_cost=10,
                         damage_multiplier=1.0, extra_effects={"ignore_armor_pct": 50})],
            10: [SkillDef("war_cry", "战吼", "全队攻击力+15%，持续3回合", mp_cost=20,
                          target_type="all_ally", extra_effects={"atk_buff": 15, "duration": 3})],
            13: [SkillDef("whirlwind", "旋风斩", "攻击前排所有敌人，80%伤害", mp_cost=18,
                          target_type="all_enemy", damage_multiplier=0.8)],
            16: [SkillDef("indomitable", "不屈", "HP归零时保留1点HP，每场战斗限1次",
                          target_type="self")],
            20: [SkillDef("war_god", "战神降临", "3回合内攻击力翻倍，每场战斗限1次", mp_cost=40,
                          target_type="self", extra_effects={"atk_buff": 100, "duration": 3})],
        },
    ),
    "mage": ClassData(
        class_id="mage", name="法师", description="后排法术爆发，控场与AOE。",
        hp_per_level=5, mp_per_level=10, primary_attr="int",
        skill_table={
            1: [
                SkillDef("fire_bolt", "火焰箭", "单体火焰伤害", mp_cost=5, damage_multiplier=1.2),
                SkillDef("ice_shard", "冰霜弹", "单体冰伤害+减速1回合", mp_cost=5,
                         extra_effects={"slow": 1}),
            ],
            3: [SkillDef("arcane_missile", "奥术飞弹", "3段随机目标法术伤害", mp_cost=8,
                         target_type="single", damage_multiplier=0.5,
                         extra_effects={"hits": 3})],
            5: [SkillDef("fireball", "火球术", "敌方全体火焰伤害", mp_cost=15,
                         target_type="all_enemy", damage_multiplier=1.0)],
            7: [SkillDef("blink", "闪现", "本回合闪避率+50%", mp_cost=10,
                         target_type="self", extra_effects={"dodge_bonus": 50, "duration": 1})],
            10: [SkillDef("blizzard", "暴风雪", "敌方全体冰伤害+减速2回合", mp_cost=25,
                          target_type="all_enemy", damage_multiplier=0.9,
                          extra_effects={"slow": 2})],
            13: [SkillDef("lightning_chain", "闪电链", "跳跃4个目标的连锁闪电", mp_cost=22,
                          damage_multiplier=0.8, extra_effects={"chain": 4})],
            16: [SkillDef("mana_shield", "法力护盾", "消耗MP抵消等量伤害，持续2回合", mp_cost=30,
                          target_type="self", extra_effects={"mana_shield": True, "duration": 2})],
            20: [SkillDef("meteor", "陨石术", "敌方全体巨额伤害，每场战斗限1次", mp_cost=50,
                          target_type="all_enemy", damage_multiplier=2.5)],
        },
    ),
    "rogue": ClassData(
        class_id="rogue", name="盗贼", description="物理输出，开锁拆除陷阱，高暴击。",
        hp_per_level=8, mp_per_level=4, primary_attr="dex",
        skill_table={
            1: [
                SkillDef("backstab", "偷袭", "目标满血时造成200%伤害", mp_cost=5,
                         damage_multiplier=2.0, extra_effects={"full_hp_only": True}),
                SkillDef("lockpick", "开锁", "探索中可以打开上锁宝箱/门", target_type="self"),
            ],
            3: [SkillDef("shadow_step", "暗影步", "绕后攻击，本回合暴击率+30%", mp_cost=8,
                         damage_multiplier=1.0, extra_effects={"crit_bonus": 30})],
            5: [SkillDef("poison_blade", "毒刃", "攻击附加中毒(每回合掉血)，持续3回合", mp_cost=8,
                         extra_effects={"dot": 5, "dot_turns": 3})],
            7: [SkillDef("smoke_bomb", "烟雾弹", "全队闪避率+20%，持续3回合", mp_cost=12,
                         target_type="all_ally", extra_effects={"dodge_buff": 20, "duration": 3})],
            10: [SkillDef("fatal_blow", "致命一击", "目标HP<30%时造成300%伤害", mp_cost=15,
                          damage_multiplier=3.0, extra_effects={"low_hp_only": True})],
            13: [SkillDef("double_shadow", "双重暗影", "暗影步可攻击2次", mp_cost=14,
                          damage_multiplier=1.0, extra_effects={"hits": 2, "crit_bonus": 30})],
            16: [SkillDef("assassin_instinct", "刺客本能", "击杀后立即获得额外一次攻击",
                          target_type="self")],
            20: [SkillDef("death_blossom", "死亡莲华", "攻击全部敌人，每击杀一个追加一次攻击",
                          mp_cost=35, target_type="all_enemy", damage_multiplier=1.2,
                          extra_effects={"chain_kill": True})],
        },
    ),
    "cleric": ClassData(
        class_id="cleric", name="牧师", description="治疗、Buff、驱散，亡灵克星。",
        hp_per_level=8, mp_per_level=8, primary_attr="wis",
        skill_table={
            1: [
                SkillDef("heal", "治愈术", "单体治疗，恢复(感知×2)HP", mp_cost=6,
                         target_type="single", extra_effects={"heal_mult": 2.0}),
                SkillDef("holy_light", "圣光", "驱散单体debuff", mp_cost=4,
                         target_type="single", extra_effects={"cleanse": True}),
            ],
            3: [SkillDef("shield", "护盾术", "目标获得(感知×3)临时护盾", mp_cost=10,
                         target_type="single", extra_effects={"shield_mult": 3.0})],
            5: [SkillDef("group_heal", "群体治疗", "全队恢复(感知×1.5)HP", mp_cost=18,
                         target_type="all_ally", extra_effects={"heal_mult": 1.5})],
            7: [SkillDef("holy_nova", "神圣新星", "全队治疗+驱散全体debuff", mp_cost=22,
                         target_type="all_ally", extra_effects={"heal_mult": 1.0, "cleanse": True})],
            10: [SkillDef("revive", "复活术", "战斗中复活一名阵亡队友(HP50%)，每场限1次",
                          mp_cost=35, target_type="single",
                          extra_effects={"revive": True, "revive_hp_pct": 50})],
            13: [SkillDef("faith_wall", "信仰之壁", "全队减伤30%，持续2回合", mp_cost=25,
                          target_type="all_ally", extra_effects={"dmg_reduce": 30, "duration": 2})],
            16: [SkillDef("holy_judgement", "神圣审判", "对亡灵/恶魔造成(感知×5)神圣伤害",
                          mp_cost=20, damage_multiplier=1.0,
                          extra_effects={"holy_mult": 5.0}),
                 ],
            20: [SkillDef("divine_blessing", "神之恩赐", "全队HP/MP回满+清除所有debuff，每场限1次",
                          mp_cost=50, target_type="all_ally",
                          extra_effects={"full_restore": True})],
        },
    ),
    "ranger": ClassData(
        class_id="ranger", name="游侠", description="远程输出、陷阱、动物伙伴。",
        hp_per_level=9, mp_per_level=5, primary_attr="dex",
        skill_table={
            1: [
                SkillDef("aimed_shot", "精准射击", "远程伤害无距离衰减", target_type="self"),
                SkillDef("tracking", "追踪", "探索中显示附近怪物位置与类型", target_type="self"),
            ],
            3: [SkillDef("scatter_shot", "散射", "同时攻击2个目标(各70%伤害)", mp_cost=10,
                         damage_multiplier=0.7, extra_effects={"hits": 2})],
            5: [SkillDef("trap", "陷阱", "设置陷阱，敌人踩中受伤害+定身1回合", mp_cost=12,
                         target_type="single", extra_effects={"trap_damage": 20, "root": 1})],
            7: [SkillDef("animal_companion", "动物伙伴", "召唤一头狼协助战斗（独立行动）", mp_cost=20,
                         target_type="self", extra_effects={"summon": "wolf_companion"})],
            10: [SkillDef("arrow_rain", "箭雨", "敌方全体远程伤害", mp_cost=20,
                          target_type="all_enemy", damage_multiplier=0.9)],
            13: [SkillDef("mark", "标记射击", "标记目标，全队对其伤害+20%", mp_cost=8,
                          target_type="single", extra_effects={"mark_dmg_bonus": 20})],
            16: [SkillDef("nature_fury", "自然之怒", "动物伙伴伤害翻倍，持续3回合", mp_cost=18,
                          target_type="self", extra_effects={"pet_dmg_buff": 100, "duration": 3})],
            20: [SkillDef("arrow_storm", "万箭齐发", "敌方全体巨额伤害+减速+标记，每场限1次",
                          mp_cost=40, target_type="all_enemy", damage_multiplier=1.5,
                          extra_effects={"slow": 1, "mark_dmg_bonus": 20})],
        },
    ),
}
