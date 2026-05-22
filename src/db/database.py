"""数据库连接管理与建表"""

import sqlite3
import os


DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "saves")
DB_PATH = os.path.join(DB_DIR, "game.db")

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS save_slots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_name   TEXT NOT NULL DEFAULT '新的冒险',
    party_name  TEXT NOT NULL DEFAULT '冒险小队',
    avg_level   INTEGER DEFAULT 1,
    play_secs   INTEGER DEFAULT 0,
    scene_id    TEXT NOT NULL DEFAULT 'river_town',
    created_at  TEXT DEFAULT (datetime('now','localtime')),
    updated_at  TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS party_member (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    save_id       INTEGER NOT NULL REFERENCES save_slots(id) ON DELETE CASCADE,
    name          TEXT NOT NULL,
    race          TEXT NOT NULL,
    class         TEXT NOT NULL,
    is_main       INTEGER DEFAULT 0,
    level         INTEGER DEFAULT 1,
    xp            INTEGER DEFAULT 0,
    hp_cur        INTEGER NOT NULL,
    hp_max        INTEGER NOT NULL,
    mp_cur        INTEGER NOT NULL,
    mp_max        INTEGER NOT NULL,
    str           INTEGER NOT NULL,  dex INTEGER NOT NULL,  con INTEGER NOT NULL,
    intel         INTEGER NOT NULL,  wis INTEGER NOT NULL,  cha INTEGER NOT NULL,
    gold          INTEGER DEFAULT 0,
    slot_index    INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS member_auto_rules (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id     INTEGER NOT NULL REFERENCES party_member(id) ON DELETE CASCADE,
    rule_id       TEXT NOT NULL,
    enabled       INTEGER DEFAULT 1,
    threshold     INTEGER DEFAULT 30
);

CREATE TABLE IF NOT EXISTS inventory (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    save_id     INTEGER NOT NULL REFERENCES save_slots(id) ON DELETE CASCADE,
    item_id     TEXT NOT NULL,
    quantity    INTEGER DEFAULT 1,
    equipped_by INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS quest_state (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    save_id     INTEGER NOT NULL REFERENCES save_slots(id) ON DELETE CASCADE,
    quest_id    TEXT NOT NULL,
    status      TEXT DEFAULT 'active',
    progress    TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS game_progress (
    save_id     INTEGER PRIMARY KEY REFERENCES save_slots(id) ON DELETE CASCADE,
    scene_id    TEXT DEFAULT 'river_town',
    flags       TEXT DEFAULT '{}',
    defeated    TEXT DEFAULT '[]'
);
"""


def get_connection() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


MIGRATIONS = [
    # v0.4: 添加队伍金币列
    "ALTER TABLE save_slots ADD COLUMN gold INTEGER DEFAULT 0",
]


def init_db() -> None:
    """建表 + 迁移（首次启动调用）"""
    conn = get_connection()
    conn.executescript(SCHEMA)

    # 执行增量迁移
    existing = {r[1] for r in conn.execute("PRAGMA table_info(save_slots)")}
    for sql in MIGRATIONS:
        col = sql.split("ADD COLUMN ")[1].split(" ")[0] if "ADD COLUMN" in sql else ""
        if col and col not in existing:
            conn.execute(sql)

    conn.commit()
    conn.close()
