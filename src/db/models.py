"""数据库映射模型 — 纯 dataclass，用于序列化/反序列化"""

from dataclasses import dataclass, field
import json


@dataclass
class SaveSlot:
    id: int = 0
    slot_name: str = "新的冒险"
    party_name: str = "冒险小队"
    avg_level: int = 1
    play_secs: int = 0
    scene_id: str = "river_town"
    gold: int = 0
    created_at: str = ""
    updated_at: str = ""


@dataclass
class PartyMemberRow:
    id: int = 0
    save_id: int = 0
    name: str = ""
    race: str = ""
    class_: str = ""                    # 数据库列名叫 "class"
    is_main: bool = False
    level: int = 1
    xp: int = 0
    hp_cur: int = 0
    hp_max: int = 0
    mp_cur: int = 0
    mp_max: int = 0
    str: int = 8; dex: int = 8; con: int = 8
    intel: int = 8; wis: int = 8; cha: int = 8
    gold: int = 0
    slot_index: int = 0


@dataclass
class AutoRuleRow:
    id: int = 0
    member_id: int = 0
    rule_id: str = ""
    enabled: bool = True
    threshold: int = 30


@dataclass
class InventoryRow:
    id: int = 0
    save_id: int = 0
    item_id: str = ""
    quantity: int = 1
    equipped_by: int = 0              # 0=背包, 1-4=队员slot+1 或直接存slot_index


@dataclass
class QuestStateRow:
    id: int = 0
    save_id: int = 0
    quest_id: str = ""
    status: str = "active"
    progress: str = "{}"              # JSON


@dataclass
class GameProgressRow:
    save_id: int = 0
    scene_id: str = "river_town"
    flags: str = "{}"                  # JSON: {flag_name: bool}
    defeated: str = "[]"               # JSON: [boss_id, ...]
