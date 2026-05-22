"""骰子系统"""

import random
from typing import Callable


def roll(die: str) -> int:
    """
    掷骰: roll("d20") / roll("2d6") / roll("3d8+2")
    """
    parts = die.split("d")
    count = int(parts[0]) if parts[0] else 1
    rest = parts[1]
    bonus = 0
    if "+" in rest:
        rest, bonus_str = rest.split("+")
        bonus = int(bonus_str)
    elif "-" in rest:
        rest, bonus_str = rest.split("-")
        bonus = -int(bonus_str)
    sides = int(rest)
    total = sum(random.randint(1, sides) for _ in range(count))
    return total + bonus


def d20() -> int:
    return roll("1d20")


def d(sides: int) -> int:
    return roll(f"1d{sides}")


def ability_modifier(value: int) -> int:
    """属性修正值: (属性-10)//2"""
    return (value - 10) // 2


def try_chance(percent: float) -> bool:
    """percent% 概率返回 True"""
    return random.random() * 100 < percent
