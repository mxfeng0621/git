"""种族数据"""

from dataclasses import dataclass, field


@dataclass
class RacialData:
    race_id: str
    name: str
    description: str
    attr_bonus: dict[str, int]            # str/dex/con/int/wis/cha 加成
    active_name: str
    active_desc: str
    active_limit: str                     # "once_per_combat" | "once_per_explore"
    active_effect: dict                   # 效果参数
    passives: list[dict]                  # [{name, desc, effect}, ...]


RACES: dict[str, RacialData] = {
    "human": RacialData(
        race_id="human",
        name="人类",
        description="适应力最强、分布最广的种族，以多才多艺和外交手腕著称。",
        attr_bonus={"str": 1, "dex": 1, "con": 1, "int": 1, "wis": 1, "cha": 1},
        active_name="逆境求生",
        active_desc="本回合闪避率+20%",
        active_limit="once_per_combat",
        active_effect={"dodge_bonus": 20, "duration": 1},
        passives=[
            {"name": "多才多艺", "desc": "经验获取+5%", "effect": {"xp_bonus": 0.05}},
            {"name": "外交手腕", "desc": "商店买卖价格优惠5%", "effect": {"price_bonus": 0.05}},
        ],
    ),
    "elf": RacialData(
        race_id="elf",
        name="精灵",
        description="古老的森林种族，优雅而敏锐，与自然有着深厚的联系。",
        attr_bonus={"dex": 2, "int": 1, "str": 0, "con": 0, "wis": 0, "cha": 0},
        active_name="精灵之眼",
        active_desc="揭示当前场景所有隐藏物品和陷阱",
        active_limit="once_per_explore",
        active_effect={"reveal_hidden": True},
        passives=[
            {"name": "敏锐感知", "desc": "先手值+2", "effect": {"initiative_bonus": 2}},
            {"name": "森林之友", "desc": "森林场景战斗时全队命中率+5%",
             "effect": {"forest_hit_bonus": 5}},
        ],
    ),
    "dwarf": RacialData(
        race_id="dwarf",
        name="矮人",
        description="山中之民，坚韧不拔，天生的锻造大师和矿工。",
        attr_bonus={"con": 2, "str": 1, "dex": 0, "int": 0, "wis": 0, "cha": 0},
        active_name="石之坚韧",
        active_desc="获得最大HP 20%的护盾，持续2回合",
        active_limit="once_per_combat",
        active_effect={"shield_pct": 20, "duration": 2},
        passives=[
            {"name": "毒素抗性", "desc": "毒伤害减免30%", "effect": {"poison_resist": 30}},
            {"name": "矿洞直觉", "desc": "矿洞/地下场景额外发现稀有矿石",
             "effect": {"mine_bonus": True}},
        ],
    ),
    "halfling": RacialData(
        race_id="halfling",
        name="半身人",
        description="小巧灵活、运气极佳的种族，投掷物品的好手。",
        attr_bonus={"dex": 2, "cha": 1, "str": 0, "con": 0, "int": 0, "wis": 0},
        active_name="幸运硬币",
        active_desc="下次受击时50%概率完全闪避",
        active_limit="once_per_combat",
        active_effect={"evade_chance": 50},
        passives=[
            {"name": "小幸运", "desc": "闪避率+5%", "effect": {"dodge_bonus": 5}},
            {"name": "投掷专精", "desc": "使用投掷类道具时伤害+30%",
             "effect": {"throw_damage_bonus": 30}},
        ],
    ),
}
