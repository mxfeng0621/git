"""装备与道具模板"""

from dataclasses import dataclass, field
from enum import Enum


class ItemType(Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    HELMET = "helmet"
    GLOVES = "gloves"
    BOOTS = "boots"
    ACCESSORY = "accessory"
    CONSUMABLE = "consumable"
    QUEST = "quest"


class Rarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


RARITY_NAMES = {
    Rarity.COMMON: "普通",
    Rarity.UNCOMMON: "精良",
    Rarity.RARE: "稀有",
    Rarity.EPIC: "史诗",
    Rarity.LEGENDARY: "传说",
}

RARITY_COLORS = {
    Rarity.COMMON: "#9d9d9d",
    Rarity.UNCOMMON: "#1eff00",
    Rarity.RARE: "#0070dd",
    Rarity.EPIC: "#a335ee",
    Rarity.LEGENDARY: "#ff8000",
}


@dataclass
class ItemTemplate:
    item_id: str
    name: str
    description: str
    item_type: ItemType
    rarity: Rarity = Rarity.COMMON
    price: int = 0
    # 装备属性
    slot: str = ""                       # weapon / offhand / head / body / hands / feet / accessory
    damage_dice: str = ""                # "1d6" / "2d4" 等
    armor_value: int = 0                 # 护甲值
    attr_bonus: dict[str, int] = field(default_factory=dict)
    hp_bonus: int = 0
    mp_bonus: int = 0
    usable_classes: list[str] = field(default_factory=list)  # 空=全职业可用
    # 消耗品属性
    heal_hp: int = 0
    heal_mp: int = 0
    temp_attr_bonus: dict[str, int] = field(default_factory=dict)
    duration_turns: int = 0              # 临时效果持续回合数


# ===== 武器 =====
ITEMS: dict[str, ItemTemplate] = {
    "rusty_sword": ItemTemplate(
        item_id="rusty_sword", name="生锈长剑", description="一把老旧的长剑，但仍能使用。",
        item_type=ItemType.WEAPON, rarity=Rarity.COMMON, price=10,
        slot="weapon", damage_dice="1d8",
    ),
    "iron_sword": ItemTemplate(
        item_id="iron_sword", name="铁剑", description="标准制式铁剑。",
        item_type=ItemType.WEAPON, rarity=Rarity.COMMON, price=30,
        slot="weapon", damage_dice="1d10",
    ),
    "steel_blade": ItemTemplate(
        item_id="steel_blade", name="精钢长剑", description="锻造精良的钢剑，锋利无比。",
        item_type=ItemType.WEAPON, rarity=Rarity.UNCOMMON, price=80,
        slot="weapon", damage_dice="1d12", attr_bonus={"str": 1},
    ),
    "flame_sword": ItemTemplate(
        item_id="flame_sword", name="烈焰之刃", description="剑身泛着赤红火光的上古武器。",
        item_type=ItemType.WEAPON, rarity=Rarity.EPIC, price=500,
        slot="weapon", damage_dice="2d8", attr_bonus={"str": 3},
    ),
    "short_bow": ItemTemplate(
        item_id="short_bow", name="短弓", description="猎人常用的短弓。",
        item_type=ItemType.WEAPON, rarity=Rarity.COMMON, price=15,
        slot="weapon", damage_dice="1d6", usable_classes=["游侠", "盗贼"],
    ),
    "elven_bow": ItemTemplate(
        item_id="elven_bow", name="精灵长弓", description="精灵工艺打造的精美长弓。",
        item_type=ItemType.WEAPON, rarity=Rarity.UNCOMMON, price=100,
        slot="weapon", damage_dice="1d10", attr_bonus={"dex": 2}, usable_classes=["游侠"],
    ),
    "wizard_staff": ItemTemplate(
        item_id="wizard_staff", name="法师之杖", description="镶嵌蓝宝石的橡木法杖，蕴含魔力。",
        item_type=ItemType.WEAPON, rarity=Rarity.UNCOMMON, price=90,
        slot="weapon", damage_dice="1d6", attr_bonus={"int": 2}, usable_classes=["法师"],
    ),
    "holy_mace": ItemTemplate(
        item_id="holy_mace", name="圣光钉锤", description="受到祝福的武器，对亡灵有奇效。",
        item_type=ItemType.WEAPON, rarity=Rarity.RARE, price=200,
        slot="weapon", damage_dice="1d10", attr_bonus={"wis": 2}, usable_classes=["牧师"],
    ),
    "dagger": ItemTemplate(
        item_id="dagger", name="匕首", description="轻巧灵便的短刃。",
        item_type=ItemType.WEAPON, rarity=Rarity.COMMON, price=8,
        slot="weapon", damage_dice="1d4", usable_classes=["盗贼", "法师"],
    ),

    # ===== 防具 =====
    "leather_armor": ItemTemplate(
        item_id="leather_armor", name="皮甲", description="轻便的皮革护甲。",
        item_type=ItemType.ARMOR, rarity=Rarity.COMMON, price=20,
        slot="body", armor_value=2,
    ),
    "chainmail": ItemTemplate(
        item_id="chainmail", name="锁子甲", description="铁环编织的中型护甲。",
        item_type=ItemType.ARMOR, rarity=Rarity.UNCOMMON, price=60,
        slot="body", armor_value=5,
    ),
    "plate_armor": ItemTemplate(
        item_id="plate_armor", name="板甲", description="厚重的全身钢板甲。",
        item_type=ItemType.ARMOR, rarity=Rarity.RARE, price=200,
        slot="body", armor_value=8, usable_classes=["战士"],
    ),
    "cloth_robe": ItemTemplate(
        item_id="cloth_robe", name="法师长袍", description="轻便的附魔布袍。",
        item_type=ItemType.ARMOR, rarity=Rarity.COMMON, price=15,
        slot="body", armor_value=1, mp_bonus=20, usable_classes=["法师", "牧师"],
    ),
    "iron_helmet": ItemTemplate(
        item_id="iron_helmet", name="铁头盔", description="保护头部的铁盔。",
        item_type=ItemType.HELMET, rarity=Rarity.COMMON, price=15,
        slot="head", armor_value=1,
    ),

    # ===== 消耗品 =====
    "health_potion_s": ItemTemplate(
        item_id="health_potion_s", name="小型治疗药水", description="恢复少量生命值。",
        item_type=ItemType.CONSUMABLE, rarity=Rarity.COMMON, price=25, heal_hp=30,
    ),
    "health_potion_m": ItemTemplate(
        item_id="health_potion_m", name="中型治疗药水", description="恢复中量生命值。",
        item_type=ItemType.CONSUMABLE, rarity=Rarity.UNCOMMON, price=60, heal_hp=80,
    ),
    "health_potion_l": ItemTemplate(
        item_id="health_potion_l", name="大型治疗药水", description="恢复大量生命值。",
        item_type=ItemType.CONSUMABLE, rarity=Rarity.RARE, price=150, heal_hp=200,
    ),
    "mana_potion_s": ItemTemplate(
        item_id="mana_potion_s", name="小型法力药水", description="恢复少量法力值。",
        item_type=ItemType.CONSUMABLE, rarity=Rarity.COMMON, price=20, heal_mp=25,
    ),
    "mana_potion_m": ItemTemplate(
        item_id="mana_potion_m", name="中型法力药水", description="恢复中量法力值。",
        item_type=ItemType.CONSUMABLE, rarity=Rarity.UNCOMMON, price=50, heal_mp=60,
    ),
    "strength_potion": ItemTemplate(
        item_id="strength_potion", name="力量药水", description="暂时提升力量。",
        item_type=ItemType.CONSUMABLE, rarity=Rarity.UNCOMMON, price=45,
        temp_attr_bonus={"str": 4}, duration_turns=3,
    ),
    "throwing_knife": ItemTemplate(
        item_id="throwing_knife", name="飞刀", description="可投掷的锋利小刀。",
        item_type=ItemType.CONSUMABLE, rarity=Rarity.COMMON, price=5,
        damage_dice="1d4",
    ),

    # ===== 饰品 =====
    "ring_of_protection": ItemTemplate(
        item_id="ring_of_protection", name="防护戒指", description="散发微弱魔法光芒的戒指。",
        item_type=ItemType.ACCESSORY, rarity=Rarity.UNCOMMON, price=120,
        slot="accessory", armor_value=2,
    ),
    "amulet_of_vitality": ItemTemplate(
        item_id="amulet_of_vitality", name="活力护符", description="蕴含生命能量的护身符。",
        item_type=ItemType.ACCESSORY, rarity=Rarity.RARE, price=180,
        slot="accessory", hp_bonus=50,
    ),
}
