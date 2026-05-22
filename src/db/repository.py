"""数据访问层 — CRUD 操作"""

import sqlite3
import json
from typing import Any

from db.database import get_connection
from db.models import (
    SaveSlot, PartyMemberRow, AutoRuleRow,
    InventoryRow, QuestStateRow, GameProgressRow,
)


class SaveRepo:
    """存档元信息"""

    @staticmethod
    def list_all() -> list[SaveSlot]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, slot_name, party_name, avg_level, play_secs, "
            "scene_id, created_at, updated_at FROM save_slots ORDER BY updated_at DESC"
        ).fetchall()
        return [SaveSlot(**dict(r)) for r in rows]

    @staticmethod
    def get(save_id: int) -> SaveSlot | None:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM save_slots WHERE id = ?", (save_id,)
        ).fetchone()
        return SaveSlot(**dict(row)) if row else None

    @staticmethod
    def create(slot_name: str = "新的冒险", party_name: str = "冒险小队",
               scene_id: str = "river_town") -> int:
        conn = get_connection()
        cur = conn.execute(
            "INSERT INTO save_slots (slot_name, party_name, scene_id) VALUES (?, ?, ?)",
            (slot_name, party_name, scene_id),
        )
        conn.commit()
        return cur.lastrowid

    @staticmethod
    def update(save_id: int, **kwargs) -> None:
        if not kwargs:
            return
        sets = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [save_id]
        conn = get_connection()
        conn.execute(
            f"UPDATE save_slots SET {sets}, updated_at = datetime('now','localtime') "
            f"WHERE id = ?", values,
        )
        conn.commit()

    @staticmethod
    def delete(save_id: int) -> None:
        conn = get_connection()
        conn.execute("DELETE FROM save_slots WHERE id = ?", (save_id,))
        conn.commit()

    @staticmethod
    def count() -> int:
        conn = get_connection()
        return conn.execute("SELECT COUNT(*) FROM save_slots").fetchone()[0]


class PartyMemberRepo:
    """队伍成员"""

    @staticmethod
    def save_all(save_id: int, members_data: list[dict]) -> None:
        conn = get_connection()
        # 先删后插（全量替换）
        conn.execute("DELETE FROM party_member WHERE save_id = ?", (save_id,))
        for m in members_data:
            conn.execute(
                "INSERT INTO party_member "
                "(save_id, name, race, class, is_main, level, xp, "
                "hp_cur, hp_max, mp_cur, mp_max, "
                "str, dex, con, intel, wis, cha, gold, slot_index) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (save_id, m["name"], m["race"], m["class"],
                 int(m.get("is_main", False)), m["level"], m["xp"],
                 m["hp_cur"], m["hp_max"], m["mp_cur"], m["mp_max"],
                 m["str"], m["dex"], m["con"], m["intel"], m["wis"], m["cha"],
                 m.get("gold", 0), m["slot_index"]),
            )
        conn.commit()

    @staticmethod
    def load_all(save_id: int) -> list[PartyMemberRow]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM party_member WHERE save_id = ? ORDER BY slot_index",
            (save_id,),
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            if "class" in d:
                d["class_"] = d.pop("class")
            results.append(PartyMemberRow(**d))
        return results


class AutoRuleRepo:
    """自动规则"""

    @staticmethod
    def save_all(save_id: int, member_id: int, rules: list[dict]) -> None:
        conn = get_connection()
        conn.execute("DELETE FROM member_auto_rules WHERE member_id = ?", (member_id,))
        for r in rules:
            conn.execute(
                "INSERT INTO member_auto_rules (member_id, rule_id, enabled, threshold) "
                "VALUES (?, ?, ?, ?)",
                (member_id, r["rule_id"], int(r.get("enabled", True)),
                 r.get("threshold", 30)),
            )
        conn.commit()

    @staticmethod
    def load_for_member(member_id: int) -> list[AutoRuleRow]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM member_auto_rules WHERE member_id = ?", (member_id,),
        ).fetchall()
        return [AutoRuleRow(**dict(r)) for r in rows]


class InventoryRepo:
    """物品/背包"""

    @staticmethod
    def save_all(save_id: int, items: list[dict]) -> None:
        conn = get_connection()
        conn.execute("DELETE FROM inventory WHERE save_id = ?", (save_id,))
        for item in items:
            conn.execute(
                "INSERT INTO inventory (save_id, item_id, quantity, equipped_by) "
                "VALUES (?, ?, ?, ?)",
                (save_id, item["item_id"], item["quantity"], item.get("equipped_by", 0)),
            )
        conn.commit()

    @staticmethod
    def load_all(save_id: int) -> list[InventoryRow]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM inventory WHERE save_id = ?", (save_id,),
        ).fetchall()
        return [InventoryRow(**dict(r)) for r in rows]


class QuestRepo:
    """任务状态"""

    @staticmethod
    def save_all(save_id: int, quests: list[dict]) -> None:
        conn = get_connection()
        conn.execute("DELETE FROM quest_state WHERE save_id = ?", (save_id,))
        for q in quests:
            conn.execute(
                "INSERT INTO quest_state (save_id, quest_id, status, progress) "
                "VALUES (?, ?, ?, ?)",
                (save_id, q["quest_id"], q["status"],
                 json.dumps(q.get("progress", {}), ensure_ascii=False)),
            )
        conn.commit()

    @staticmethod
    def load_all(save_id: int) -> list[QuestStateRow]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM quest_state WHERE save_id = ?", (save_id,),
        ).fetchall()
        return [QuestStateRow(**dict(r)) for r in rows]


class ProgressRepo:
    """游戏进度"""

    @staticmethod
    def save(save_id: int, scene_id: str, flags: dict, defeated: list[str]) -> None:
        conn = get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO game_progress (save_id, scene_id, flags, defeated) "
            "VALUES (?, ?, ?, ?)",
            (save_id, scene_id,
             json.dumps(flags, ensure_ascii=False),
             json.dumps(defeated, ensure_ascii=False)),
        )
        conn.commit()

    @staticmethod
    def load(save_id: int) -> GameProgressRow | None:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM game_progress WHERE save_id = ?", (save_id,),
        ).fetchone()
        return GameProgressRow(**dict(row)) if row else None
