"""文本命令解析器"""

from dataclasses import dataclass, field
from enum import Enum
import re


class ActionCategory(Enum):
    MOVE = "move"
    COMBAT = "combat"
    INTERACT = "interact"
    ITEM = "item"
    INFO = "info"
    SYSTEM = "system"


@dataclass
class Command:
    category: ActionCategory
    action: str                          # 归一化动作名
    raw: str                             # 原始输入
    target: str = ""                     # 目标名称
    params: dict[str, str] = field(default_factory=dict)


# 命令映射：{关键词: (类别, 动作名)}
COMMAND_MAP: dict[str, tuple[ActionCategory, str]] = {
    # 移动类
    "前往": (ActionCategory.MOVE, "go"),
    "去": (ActionCategory.MOVE, "go"),
    "移动": (ActionCategory.MOVE, "go"),
    "返回": (ActionCategory.MOVE, "back"),
    "back": (ActionCategory.MOVE, "back"),
    "地图": (ActionCategory.INFO, "map"),
    "map": (ActionCategory.INFO, "map"),

    # 战斗类
    "策略": (ActionCategory.COMBAT, "strategy"),
    "集火": (ActionCategory.COMBAT, "focus"),
    "focus": (ActionCategory.COMBAT, "focus"),
    "逃跑": (ActionCategory.COMBAT, "flee"),
    "flee": (ActionCategory.COMBAT, "flee"),
    "撤退": (ActionCategory.COMBAT, "flee"),

    # 交互类
    "探索": (ActionCategory.INTERACT, "explore"),
    "explore": (ActionCategory.INTERACT, "explore"),
    "搜索": (ActionCategory.INTERACT, "explore"),
    "对话": (ActionCategory.INTERACT, "talk"),
    "talk": (ActionCategory.INTERACT, "talk"),
    "检查": (ActionCategory.INTERACT, "examine"),
    "examine": (ActionCategory.INTERACT, "examine"),
    "拾取": (ActionCategory.INTERACT, "pickup"),
    "pick": (ActionCategory.INTERACT, "pickup"),
    "休息": (ActionCategory.INTERACT, "rest"),
    "rest": (ActionCategory.INTERACT, "rest"),

    # 物品类
    "背包": (ActionCategory.INFO, "inventory"),
    "inventory": (ActionCategory.INFO, "inventory"),
    "装备": (ActionCategory.ITEM, "equip"),
    "equip": (ActionCategory.ITEM, "equip"),
    "卸下": (ActionCategory.ITEM, "unequip"),
    "使用": (ActionCategory.ITEM, "use"),
    "use": (ActionCategory.ITEM, "use"),
    "丢弃": (ActionCategory.ITEM, "discard"),
    "discard": (ActionCategory.ITEM, "discard"),

    # 信息类
    "状态": (ActionCategory.INFO, "status"),
    "status": (ActionCategory.INFO, "status"),
    "任务": (ActionCategory.INFO, "quests"),
    "quests": (ActionCategory.INFO, "quests"),
    "帮助": (ActionCategory.INFO, "help"),
    "help": (ActionCategory.INFO, "help"),
    "?" : (ActionCategory.INFO, "help"),

    # 系统类
    "存档": (ActionCategory.SYSTEM, "save"),
    "save": (ActionCategory.SYSTEM, "save"),
    "读档": (ActionCategory.SYSTEM, "load"),
    "load": (ActionCategory.SYSTEM, "load"),
    "设置": (ActionCategory.SYSTEM, "settings"),
    "settings": (ActionCategory.SYSTEM, "settings"),
}

# 物品名 → item_id 模糊匹配
ITEM_ALIASES: dict[str, str] = {
    "长剑": "iron_sword",
    "铁剑": "iron_sword",
    "铁盾": "iron_helmet",
    "皮甲": "leather_armor",
    "药水": "health_potion_s",
    "治疗药水": "health_potion_s",
    "法力药水": "mana_potion_s",
    "火球": "fireball",
}


class CommandParser:
    def parse(self, text: str) -> Command:
        raw = text.strip()
        if not raw:
            return Command(ActionCategory.INFO, "help", raw)

        # 尝试匹配关键词
        for keyword, (cat, action) in sorted(COMMAND_MAP.items(),
                                              key=lambda x: -len(x[0])):
            if raw.startswith(keyword):
                rest = raw[len(keyword):].strip()
                target = rest if rest else ""
                return Command(cat, action, raw, target)

        # 未匹配 → 尝试作为自定义对话/探索指令
        return Command(ActionCategory.INTERACT, "custom", raw, target=raw)
