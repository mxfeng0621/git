"""游戏常量与枚举定义"""

from enum import Enum


class Attr(Enum):
    """六维属性"""
    STR = "力量"
    DEX = "敏捷"
    CON = "体质"
    INT = "智力"
    WIS = "感知"
    CHA = "魅力"


class CharClass(Enum):
    """职业"""
    WARRIOR = "战士"
    MAGE = "法师"
    ROGUE = "盗贼"
    CLERIC = "牧师"
    RANGER = "游侠"


class Race(Enum):
    """种族"""
    HUMAN = "人类"
    ELF = "精灵"
    DWARF = "矮人"
    HALFLING = "半身人"


class StrategyType(Enum):
    """战斗策略"""
    FULL_ASSAULT = "全力猛攻"
    BALANCED = "平衡输出"
    CONSERVE_MANA = "保留法力"
    PRIORITY_HEAL = "优先治疗"
    DEFEND = "防御牵制"


class QuestStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class CombatResult(Enum):
    VICTORY = "victory"
    DEFEAT = "defeat"
    RETREATED = "retreated"


class MessageCategory(Enum):
    INFO = "info"
    WARNING = "warning"
    DANGER = "danger"
    LOOT = "loot"
    COMBAT = "combat"
    SYSTEM = "system"


# 购点制
POINT_BUY_COST = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
TOTAL_POINTS = 27
ATTR_MIN = 8
ATTR_MAX = 15
LEVEL_CAP = 20
PARTY_SIZE = 4
SAVE_SLOTS = 5
GOLD_START = 50
