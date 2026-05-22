"""怪物模板"""

from dataclasses import dataclass, field
from enum import Enum


class MonsterTier(Enum):
    NORMAL = "normal"
    ELITE = "elite"
    BOSS = "boss"


class MonsterBehavior(Enum):
    FIERCE = "fierce"         # 攻击HP最低者
    TACTICAL = "tactical"     # 围攻前排，HP<30%逃跑
    RELENTLESS = "relentless"  # 攻击最近的，无视恐惧
    BOSS_AI = "boss_ai"       # 半血切换阶段


@dataclass
class MonsterTemplate:
    monster_id: str
    name: str
    description: str
    tier: MonsterTier
    behavior: MonsterBehavior
    hp: int
    mp: int = 0
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    armor: int = 2
    damage_dice: str = "1d6"
    skills: list[dict] = field(default_factory=list)
    xp_reward: int = 0
    gold_min: int = 0
    gold_max: int = 0
    loot_table: list[dict] = field(default_factory=list)  # [{item_id, chance%}]


MONSTERS: dict[str, MonsterTemplate] = {
    # ===== 普通怪物 =====
    "goblin": MonsterTemplate(
        monster_id="goblin", name="地精", description="矮小丑陋的绿皮生物，手持生锈短刀。",
        tier=MonsterTier.NORMAL, behavior=MonsterBehavior.TACTICAL,
        hp=18, dexterity=12,
        damage_dice="1d6", armor=2,
        xp_reward=25, gold_min=2, gold_max=8,
        loot_table=[{"item_id": "health_potion_s", "chance": 15}],
    ),
    "goblin_archer": MonsterTemplate(
        monster_id="goblin_archer", name="地精弓箭手", description="躲在远处放冷箭的地精。",
        tier=MonsterTier.NORMAL, behavior=MonsterBehavior.TACTICAL,
        hp=14, dexterity=14,
        damage_dice="1d6", armor=1,
        xp_reward=30, gold_min=3, gold_max=10,
    ),
    "wolf": MonsterTemplate(
        monster_id="wolf", name="森林狼", description="饥饿的灰狼，眼中闪烁绿光。",
        tier=MonsterTier.NORMAL, behavior=MonsterBehavior.FIERCE,
        hp=22, strength=12, dexterity=13,
        damage_dice="1d8", armor=1,
        xp_reward=30, gold_min=0, gold_max=5,
        loot_table=[{"item_id": "throwing_knife", "chance": 20}],
    ),
    "skeleton": MonsterTemplate(
        monster_id="skeleton", name="骷髅兵", description="被亡灵法术驱动的枯骨战士。",
        tier=MonsterTier.NORMAL, behavior=MonsterBehavior.RELENTLESS,
        hp=20, strength=11, constitution=12,
        damage_dice="1d8", armor=3,
        xp_reward=35, gold_min=2, gold_max=10,
    ),
    "giant_spider": MonsterTemplate(
        monster_id="giant_spider", name="巨蜘蛛", description="磨盘大的毒蜘蛛，在洞穴中结网捕猎。",
        tier=MonsterTier.NORMAL, behavior=MonsterBehavior.FIERCE,
        hp=25, strength=13, dexterity=14,
        damage_dice="1d8", armor=2,
        skills=[{"name": "毒液喷射", "desc": "单体中毒3回合", "dot_damage": 5, "dot_turns": 3}],
        xp_reward=40, gold_min=0, gold_max=8,
    ),

    # ===== 精英怪物 =====
    "goblin_chief": MonsterTemplate(
        monster_id="goblin_chief", name="地精头领", description="体型更大的地精，手持精良战斧。",
        tier=MonsterTier.ELITE, behavior=MonsterBehavior.TACTICAL,
        hp=60, strength=15, constitution=14,
        damage_dice="1d12", armor=4,
        skills=[{"name": "战吼", "desc": "全队敌人攻击+10%", "atk_buff": 10, "duration": 2}],
        xp_reward=80, gold_min=15, gold_max=40,
        loot_table=[{"item_id": "iron_sword", "chance": 30}],
    ),
    "wraith": MonsterTemplate(
        monster_id="wraith", name="幽魂", description="半透明的不死生物，散发刺骨寒气。",
        tier=MonsterTier.ELITE, behavior=MonsterBehavior.RELENTLESS,
        hp=50, intelligence=14, wisdom=14,
        damage_dice="2d6", armor=1,
        skills=[{"name": "吸取生命", "desc": "造成伤害并恢复自身HP", "life_steal": 50}],
        xp_reward=100, gold_min=0, gold_max=30,
        loot_table=[{"item_id": "mana_potion_m", "chance": 25}],
    ),
    "ogre": MonsterTemplate(
        monster_id="ogre", name="食人魔", description="三米高的巨大人形怪物，挥舞粗木棍。",
        tier=MonsterTier.ELITE, behavior=MonsterBehavior.FIERCE,
        hp=90, strength=18, constitution=16,
        damage_dice="2d8", armor=5,
        xp_reward=120, gold_min=30, gold_max=80,
        loot_table=[{"item_id": "health_potion_m", "chance": 40}],
    ),

    # ===== Boss =====
    "shadow_dragon_whelp": MonsterTemplate(
        monster_id="shadow_dragon_whelp", name="暗影幼龙",
        description="黑龙的幼崽，虽未成年但已足以毁灭一支小队。",
        tier=MonsterTier.BOSS, behavior=MonsterBehavior.BOSS_AI,
        hp=200, mp=80,
        strength=18, dexterity=12, constitution=18,
        intelligence=14, wisdom=12, charisma=16,
        damage_dice="2d10", armor=8,
        skills=[
            {"name": "暗影吐息", "desc": "全体暗影伤害", "aoe_multiplier": 1.5},
            {"name": "龙威", "desc": "全队攻击力-15%", "atk_debuff": 15, "duration": 2},
            {"name": "狂怒", "desc": "HP<50%时攻击力+30%", "phase2_buff": 30},
        ],
        xp_reward=500, gold_min=100, gold_max=300,
        loot_table=[
            {"item_id": "flame_sword", "chance": 40},
            {"item_id": "amulet_of_vitality", "chance": 30},
        ],
    ),
}
