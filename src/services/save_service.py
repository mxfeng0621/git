"""存档/读档服务 — GameEngine ↔ SQLite 双向转换"""

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from db.repository import (
    SaveRepo, PartyMemberRepo, AutoRuleRepo,
    InventoryRepo, QuestRepo, ProgressRepo,
)
from db.models import (
    SaveSlot, PartyMemberRow, InventoryRow, GameProgressRow,
)
from db.database import get_connection
from data.classes import CLASSES
from data.races import RACES

if TYPE_CHECKING:
    from core.engine import GameEngine
    from core.character import Character


def save_game(engine: "GameEngine", slot: int = 1,
              slot_name: str = "") -> int:
    """
    将引擎当前状态保存到指定存档位。
    返回 save_id。
    """
    party = engine.party
    inventory = engine.inventory
    quest_mgr = engine.quest_manager
    auto_rules = engine.auto_rules

    # 1) 创建/覆盖存档槽
    existing = SaveRepo.get(slot)
    if existing:
        save_id = existing.id
        SaveRepo.update(save_id, slot_name=slot_name or existing.slot_name)
    else:
        save_id = slot  # 强制使用slot作为id（自增表需要特殊处理）
        # 实际：检查 save_slots 中是否有 id=slot 的记录
        conn = get_connection()
        row = conn.execute("SELECT id FROM save_slots WHERE id = ?", (slot,)).fetchone()
        if row:
            save_id = row[0]
        else:
            save_id = SaveRepo.create(slot_name=slot_name or "冒险存档")

    # 更新元数据
    avg_lv = int(sum(m.level for m in party.members if m) /
                 max(party.active_count(), 1))
    SaveRepo.update(save_id,
                    slot_name=slot_name or f"存档 {slot}",
                    party_name="冒险小队",
                    avg_level=avg_lv,
                    gold=inventory.gold,
                    scene_id=engine.current_scene_id)

    # 2) 队伍成员
    member_data = []
    member_id_map = {}          # slot_index → DB member id
    for i, char in enumerate(party.members):
        if char is None:
            continue
        member_data.append({
            "name": char.name, "race": char.race_id, "class": char.class_id,
            "is_main": char.is_main, "level": char.level, "xp": char.xp,
            "hp_cur": char.hp_current, "hp_max": char.hp_max,
            "mp_cur": char.mp_current, "mp_max": char.mp_max,
            "str": char.attributes["str"], "dex": char.attributes["dex"],
            "con": char.attributes["con"], "intel": char.attributes["int"],
            "wis": char.attributes["wis"], "cha": char.attributes["cha"],
            "gold": 0, "slot_index": i,
        })
    PartyMemberRepo.save_all(save_id, member_data)

    # 重新加载以获取DB分配的 member.id
    db_members = PartyMemberRepo.load_all(save_id)
    for dbm in db_members:
        member_id_map[dbm.slot_index] = dbm.id

    # 3) 自动规则
    for i, char in enumerate(party.members):
        if char is None or i not in member_id_map:
            continue
        rules = auto_rules.get_rules(i)
        rule_data = [{"rule_id": r.rule_id, "enabled": r.enabled,
                       "threshold": r.threshold} for r in rules]
        AutoRuleRepo.save_all(save_id, member_id_map[i], rule_data)

    # 4) 物品
    item_data = []
    for item in inventory.items:
        item_data.append({
            "item_id": item.item_id,
            "quantity": item.quantity,
            "equipped_by": item.equipped_by,
        })
    InventoryRepo.save_all(save_id, item_data)

    # 5) 任务
    quest_data = []
    for qs in quest_mgr.quests.values():
        quest_data.append({
            "quest_id": qs.quest_id,
            "status": qs.status.value,
            "progress": {
                "objectives": [
                    {"objective_id": o.objective_id, "current_count": o.current_count}
                    for o in qs.objectives
                ],
            },
        })
    QuestRepo.save_all(save_id, quest_data)

    # 6) 进度（含好感度）
    all_affinity = {}
    for i, m in enumerate(party.members):
        if m and m.affinity:
            all_affinity[str(i)] = m.affinity
    engine.story_flags["_affinity"] = all_affinity
    ProgressRepo.save(
        save_id, engine.current_scene_id,
        engine.story_flags,
        list(engine.defeated_bosses),
    )

    return save_id


def load_game(engine: "GameEngine", save_id: int) -> bool:
    """
    从数据库读取存档，恢复引擎状态。
    返回是否成功。
    """
    from core.character import Character
    from core.inventory import InventoryItem
    from core.auto_rules import AutoRule, AutoRuleEngine
    from core.quest import QuestState as QState, QuestObjective
    from utils.constants import QuestStatus as QStatus

    slot = SaveRepo.get(save_id)
    if not slot:
        return False

    # 1) 进度
    progress = ProgressRepo.load(save_id) or GameProgressRow(save_id=save_id)
    engine.current_scene_id = progress.scene_id
    engine.story_flags = json.loads(progress.flags) if progress.flags else {}
    engine.defeated_bosses = set(json.loads(progress.defeated) if progress.defeated else [])
    all_affinity = engine.story_flags.pop("_affinity", {})

    # 2) 队员
    db_members = PartyMemberRepo.load_all(save_id)
    engine.party.members = [None, None, None, None]
    engine.party.bench = []
    member_id_to_slot = {}

    for dbm in db_members:
        char = Character(
            name=dbm.name, race_id=dbm.race, class_id=dbm.class_,
            level=dbm.level, xp=dbm.xp,
            attributes={
                "str": dbm.str, "dex": dbm.dex, "con": dbm.con,
                "int": dbm.intel, "wis": dbm.wis, "cha": dbm.cha,
            },
            hp_current=dbm.hp_cur, hp_max=dbm.hp_max,
            mp_current=dbm.mp_cur, mp_max=dbm.mp_max,
            is_main=dbm.is_main,
        )
        char.slot_index = dbm.slot_index
        char.affinity = all_affinity.get(str(dbm.slot_index), {})
        engine.party.members[dbm.slot_index] = char
        member_id_to_slot[dbm.id] = dbm.slot_index

    # 3) 自动规则
    engine.auto_rules = AutoRuleEngine()
    for dbm in db_members:
        rule_rows = AutoRuleRepo.load_for_member(dbm.id)
        engine.auto_rules.member_rules[dbm.slot_index] = [
            AutoRule(rule_id=r.rule_id, enabled=r.enabled, threshold=r.threshold)
            for r in rule_rows
        ]

    # 4) 物品
    item_rows = InventoryRepo.load_all(save_id)
    engine.inventory.items = [
        InventoryItem(item_id=r.item_id, quantity=r.quantity, equipped_by=r.equipped_by)
        for r in item_rows
    ]
    engine.inventory.gold = slot.gold

    # 5) 任务
    quest_rows = QuestRepo.load_all(save_id)
    engine.quest_manager.quests = {}
    engine.quest_manager.completed_ids = set()
    for r in quest_rows:
        prog = json.loads(r.progress) if isinstance(r.progress, str) else r.progress
        objectives = []
        for od in prog.get("objectives", []):
            objectives.append(QuestObjective(
                objective_id=od["objective_id"],
                description="", target_type="", current_count=od["current_count"],
            ))
        status = QStatus(r.status)
        qs = QState(quest_id=r.quest_id, status=status, objectives=objectives)
        engine.quest_manager.quests[r.quest_id] = qs
        if status == QStatus.COMPLETED:
            engine.quest_manager.completed_ids.add(r.quest_id)

    return True


def list_saves() -> list[SaveSlot]:
    return SaveRepo.list_all()


def delete_save(save_id: int) -> None:
    SaveRepo.delete(save_id)
