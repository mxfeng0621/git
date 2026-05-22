# 数据库设计文档

## 1. 基础信息

| 项目 | 说明 |
|------|------|
| 数据库类型 | SQLite 3 |
| 文件位置 | `saves/game.db`（每个游戏安装目录一个文件，所有存档位共用） |
| 字符编码 | UTF-8 |
| 外键约束 | 已开启（`PRAGMA foreign_keys = ON`） |

### 1.1 术语中英对照

| 英文术语 | 中文含义 | 说明 |
|----------|----------|------|
| PK (Primary Key) | 主键 | 唯一标识一行数据，不可重复 |
| FK (Foreign Key) | 外键 | 引用另一张表的主键，建立表之间的关联 |
| AUTOINCREMENT | 自增 | 每次插入新行自动 +1，无需手动指定 |
| NOT NULL | 不能为空 | 该字段必须有值 |
| DEFAULT | 默认值 | 如果不填，自动使用预设值 |
| ON DELETE CASCADE | 级联删除 | 父表记录被删除时，子表关联记录自动删除 |
| 1:1 | 一对一 | 一条记录对应另一张表的一条记录 |
| 1:N | 一对多 | 一条记录对应另一张表的多条记录 |

---

## 2. 表关系图

```
                    ┌─────────────────────────┐
                    │      save_slots         │
                    │       (存档元信息)        │
                    │  一个存档槽 = 一份游戏进度 │
                    └──────┬────────┬─────────┘
                           │ 1      │ 1
               ┌───────────┤        ├───────────┐
               │ 1:N       │        │ 1:N       │ 1:1
               ▼           ▼        ▼           ▼
┌──────────────────┐  ┌──────────┐  ┌──────────────┐  ┌──────────────┐
│   party_member   │  │inventory │  │ quest_state  │  │game_progress │
│    (队伍成员)     │  │(物品背包)│  │  (任务状态)   │  │ (世界进度)    │
│  一个存档有4个队员│  │队伍共用  │  │ 一个存档多个   │  │ 与存档一一对应 │
└────────┬─────────┘  └──────────┘  │ 任务记录      │  └──────────────┘
         │ 1                        └──────────────┘
         │ 1:N
         ▼
┌────────────────────┐
│ member_auto_rules  │
│  (成员条件战斗规则)  │
│  每个队员有6条规则   │
└────────────────────┘
```

### 表关系说明

| 父表（1 方） | 子表（N 方） | 删除规则 | 关系说明 |
|-------------|-------------|---------|---------|
| `save_slots` | `party_member` | 级联删除 | 一个存档最多4个队员，删存档时队员一起删 |
| `save_slots` | `inventory` | 级联删除 | 一个存档共享一个背包，删存档时背包清空 |
| `save_slots` | `quest_state` | 级联删除 | 一个存档有多条任务记录，删存档时任务记录清空 |
| `save_slots` | `game_progress` | 一对一 | 一个存档只有一条世界进度记录 |
| `party_member` | `member_auto_rules` | 级联删除 | 每个队员拥有独立的自动战斗规则配置 |

---

## 3. 各表详细定义

### 3.1 save_slots — 存档元信息表

**用途**：记录每个存档位的概要信息，读档界面的列表就是读这张表。

| 序号 | 列名 | 类型 | 约束 | 中文说明 |
|------|------|------|------|----------|
| 1 | `id` | INTEGER | **主键**，自增 | 存档唯一编号（1, 2, 3...），其他表通过它关联存档 |
| 2 | `slot_name` | TEXT | 不能为空，默认"新的冒险" | 存档位的显示名称，玩家可以自定义 |
| 3 | `party_name` | TEXT | 不能为空，默认"冒险小队" | 玩家给队伍取的名字 |
| 4 | `avg_level` | INTEGER | 默认 1 | 全队平均等级，存档时自动计算，用于读档界面展示 |
| 5 | `play_secs` | INTEGER | 默认 0 | 累计游戏时长（秒），每次存档时更新 |
| 6 | `scene_id` | TEXT | 不能为空，默认"river_town" | 当前所在场景的 ID，如 "dark_forest" |
| 7 | `created_at` | TEXT | 默认当前时间 | 存档首次创建的时间戳 |
| 8 | `updated_at` | TEXT | 默认当前时间 | 存档最近一次覆盖的时间戳 |

```sql
CREATE TABLE save_slots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,  -- 存档编号（主键，自增）
    slot_name   TEXT NOT NULL DEFAULT '新的冒险',     -- 存档位名称
    party_name  TEXT NOT NULL DEFAULT '冒险小队',     -- 队伍名称
    avg_level   INTEGER DEFAULT 1,                   -- 队伍平均等级
    play_secs   INTEGER DEFAULT 0,                   -- 游戏时长（秒）
    scene_id    TEXT NOT NULL DEFAULT 'river_town',  -- 当前场景ID
    created_at  TEXT DEFAULT (datetime('now','localtime')),  -- 创建时间
    updated_at  TEXT DEFAULT (datetime('now','localtime'))   -- 更新时间
);
```

---

### 3.2 party_member — 队伍成员表

**用途**：存储每个队员的完整状态——属性、血蓝、等级经验、在队伍中的位置。

**设计要点**：
- `slot_index`（0-3）决定队员在 UI 队伍面板中的排列位置（0 = 最上面，3 = 最下面）
- `is_main=1` 表示主角，不可离队；`is_main=0` 表示同伴，可以在酒馆替换
- `gold` 是每人携带的金币，队伍总金币 = 所有队员 `gold` 之和

| 序号 | 列名 | 类型 | 约束 | 中文说明 |
|------|------|------|------|----------|
| 1 | `id` | INTEGER | **主键**，自增 | 队员在数据库中的唯一编号，背包表和规则表通过它关联队员 |
| 2 | `save_id` | INTEGER | **外键**→save_slots.id，不能为空，级联删除 | 属于哪个存档 |
| 3 | `name` | TEXT | 不能为空 | 角色姓名，玩家自定义 |
| 4 | `race` | TEXT | 不能为空 | 种族 ID：`human`(人类) `elf`(精灵) `dwarf`(矮人) `halfling`(半身人) |
| 5 | `class` | TEXT | 不能为空 | 职业 ID：`warrior`(战士) `mage`(法师) `rogue`(盗贼) `cleric`(牧师) `ranger`(游侠) |
| 6 | `is_main` | INTEGER | 默认 0 | 是否为主角：1=主角(不可离队) 0=同伴(可替换) |
| 7 | `level` | INTEGER | 默认 1 | 当前等级，范围 1-20 |
| 8 | `xp` | INTEGER | 默认 0 | 当前等级已获得的经验值 |
| 9 | `hp_cur` | INTEGER | 不能为空 | 当前生命值 |
| 10 | `hp_max` | INTEGER | 不能为空 | 最大生命值上限 |
| 11 | `mp_cur` | INTEGER | 不能为空 | 当前法力值 |
| 12 | `mp_max` | INTEGER | 不能为空 | 最大法力值上限 |
| 13 | `str` | INTEGER | 不能为空 | **力量** — 影响近战物理伤害 |
| 14 | `dex` | INTEGER | 不能为空 | **敏捷** — 影响远程伤害、闪避率、行动顺序 |
| 15 | `con` | INTEGER | 不能为空 | **体质** — 影响 HP 上限和防御力 |
| 16 | `intel` | INTEGER | 不能为空 | **智力** — 影响法术伤害和法术暴击率 |
| 17 | `wis` | INTEGER | 不能为空 | **感知** — 影响 MP 上限和治疗强度 |
| 18 | `cha` | INTEGER | 不能为空 | **魅力** — 影响商店价格和说服成功率 |
| 19 | `gold` | INTEGER | 默认 0 | 该角色携带的金币数 |
| 20 | `slot_index` | INTEGER | 默认 0 | 在队伍面板中的位置：0=左上一号位 1=左中 2=左下 3=右下 |

```sql
CREATE TABLE party_member (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,   -- 队员编号（主键，自增）
    save_id       INTEGER NOT NULL                     -- 所属存档（外键）
                  REFERENCES save_slots(id) ON DELETE CASCADE,
    name          TEXT NOT NULL,                       -- 角色姓名
    race          TEXT NOT NULL,                       -- 种族ID
    class         TEXT NOT NULL,                       -- 职业ID
    is_main       INTEGER DEFAULT 0,                   -- 是否主角：1=是 0=否
    level         INTEGER DEFAULT 1,                   -- 等级 1-20
    xp            INTEGER DEFAULT 0,                   -- 当前经验值
    hp_cur        INTEGER NOT NULL,                    -- 当前HP
    hp_max        INTEGER NOT NULL,                    -- 最大HP
    mp_cur        INTEGER NOT NULL,                    -- 当前MP
    mp_max        INTEGER NOT NULL,                    -- 最大MP
    str           INTEGER NOT NULL,                    -- 力量（近战伤害）
    dex           INTEGER NOT NULL,                    -- 敏捷（远程/闪避/先手）
    con           INTEGER NOT NULL,                    -- 体质（HP上限/防御）
    intel         INTEGER NOT NULL,                    -- 智力（法术伤害/暴击）
    wis           INTEGER NOT NULL,                    -- 感知（MP上限/治疗）
    cha           INTEGER NOT NULL,                    -- 魅力（交易/说服）
    gold          INTEGER DEFAULT 0,                   -- 携带金币
    slot_index    INTEGER DEFAULT 0                    -- 队伍位置 0-3
);
```

---

### 3.3 member_auto_rules — 成员自动战斗规则表

**用途**：存储每个队员的战斗自动规则配置。每条规则有独立的触发阈值和开关状态。
战斗中每回合先检查规则，规则触发的优先级高于战斗策略。

| 序号 | 列名 | 类型 | 约束 | 中文说明 |
|------|------|------|------|----------|
| 1 | `id` | INTEGER | **主键**，自增 | 规则行编号 |
| 2 | `member_id` | INTEGER | **外键**→party_member.id，不能为空，级联删除 | 属于哪个队员 |
| 3 | `rule_id` | TEXT | 不能为空 | 规则标识符（见下方规则表） |
| 4 | `enabled` | INTEGER | 默认 1 | 是否启用：1=开启 0=关闭 |
| 5 | `threshold` | INTEGER | 默认 30 | 触发阈值（百分比，1-99），例：30 表示 HP 低于 30% 时触发 |

**6条内置规则：**

| 规则ID | 规则名称 | 默认阈值 | 触发条件 | 触发后动作 |
|--------|----------|----------|----------|-----------|
| `self_heal` | 自保喝药 | 30% | 自己的 HP 低于阈值 | 自动使用背包中最便宜的治疗药水 |
| `emergency_heal` | 急救队友 | 20% | 任意队友 HP 低于阈值（仅牧师） | 对 HP 最低的队友施放单体治疗 |
| `mana_saver` | 法力红线 | 10% | 自己的 MP 低于阈值 | 将自己的策略切换为"保留法力" |
| `finish_off` | 优先击杀 | 15% | 有敌人 HP 低于阈值 | 全员优先攻击残血敌人 |
| `boss_burst` | Boss爆发 | — | 场上存在 Boss 级敌人（仅法师） | 法师使用当前最强法术 |
| `group_heal` | 群体治疗 | 50% | 3名以上队友 HP 低于阈值（仅牧师） | 牧师施放群体治疗 |

```sql
CREATE TABLE member_auto_rules (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,   -- 规则编号（主键，自增）
    member_id     INTEGER NOT NULL                     -- 所属队员（外键）
                  REFERENCES party_member(id) ON DELETE CASCADE,
    rule_id       TEXT NOT NULL,                       -- 规则ID
    enabled       INTEGER DEFAULT 1,                   -- 是否启用：1=是 0=否
    threshold     INTEGER DEFAULT 30                   -- 触发阈值（百分比）
);
```

---

### 3.4 inventory — 物品背包表

**用途**：记录队伍拥有的所有物品。`equipped_by=0` 表示在公共背包里，`equipped_by=队员id` 表示装备在某队员身上。

| 序号 | 列名 | 类型 | 约束 | 中文说明 |
|------|------|------|------|----------|
| 1 | `id` | INTEGER | **主键**，自增 | 物品行编号 |
| 2 | `save_id` | INTEGER | **外键**→save_slots.id，不能为空，级联删除 | 属于哪个存档 |
| 3 | `item_id` | TEXT | 不能为空 | 物品模板 ID，如 `iron_sword` `health_potion_s` |
| 4 | `quantity` | INTEGER | 默认 1 | 数量：消耗品可堆叠（如药水×5），装备固定为1 |
| 5 | `equipped_by` | INTEGER | 默认 0 | 装备状态：0=在背包中 非0=装备在对应队员id身上 |

```sql
CREATE TABLE inventory (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,    -- 物品行编号（主键，自增）
    save_id     INTEGER NOT NULL                      -- 所属存档（外键）
                REFERENCES save_slots(id) ON DELETE CASCADE,
    item_id     TEXT NOT NULL,                        -- 物品模板ID
    quantity    INTEGER DEFAULT 1,                    -- 数量
    equipped_by INTEGER DEFAULT 0                     -- 装备者：0=背包 非0=队员id
);
```

---

### 3.5 quest_state — 任务状态表

**用途**：记录每个存档中所有任务的状态。一个任务一条记录，`progress` 字段以 JSON 格式存储子目标完成进度。

| 序号 | 列名 | 类型 | 约束 | 中文说明 |
|------|------|------|------|----------|
| 1 | `id` | INTEGER | **主键**，自增 | 任务记录编号 |
| 2 | `save_id` | INTEGER | **外键**→save_slots.id，不能为空，级联删除 | 属于哪个存档 |
| 3 | `quest_id` | TEXT | 不能为空 | 任务 ID，如 `q_main_01` |
| 4 | `status` | TEXT | 默认"active" | 任务状态：`active`(进行中) `completed`(已完成) `failed`(已失败) |
| 5 | `progress` | TEXT | 默认"{}" | 任务进度（JSON格式），记录各子目标的完成数量 |

**progress 字段（JSON）示例**：

```json
{
  "objectives": [
    {
      "objective_id": "kill_goblins",    // 子目标ID
      "current_count": 3                 // 当前完成数量（目标可能是5只）
    }
  ]
}
```

```sql
CREATE TABLE quest_state (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,    -- 任务记录编号（主键，自增）
    save_id     INTEGER NOT NULL                      -- 所属存档（外键）
                REFERENCES save_slots(id) ON DELETE CASCADE,
    quest_id    TEXT NOT NULL,                        -- 任务ID
    status      TEXT DEFAULT 'active',                -- 状态：active/completed/failed
    progress    TEXT DEFAULT '{}'                     -- 子目标进度（JSON）
);
```

---

### 3.6 game_progress — 世界进度表

**用途**：与 `save_slots` 一一对应，记录不属于角色个人、而是属于游戏世界层面的推进状态——当前场景、剧情标记、已被击败的Boss。

| 序号 | 列名 | 类型 | 约束 | 中文说明 |
|------|------|------|------|----------|
| 1 | `save_id` | INTEGER | **主键**+**外键**→save_slots.id，级联删除 | 与存档槽一一对应 |
| 2 | `scene_id` | TEXT | 默认"river_town" | 队伍当前所在的场景 ID |
| 3 | `flags` | TEXT | 默认"{}" | 剧情标记（JSON对象），记录玩家做出的关键选择 |
| 4 | `defeated` | TEXT | 默认"[]" | 已击败Boss列表（JSON数组），Boss不会重复出现 |

**flags 字段示例**（记录剧情关键节点）：

```json
{
  "met_elf_king": true,           // 见过精灵王 → 是
  "goblin_camp_cleared": true,    // 清剿地精营地 → 是
  "dwarf_alliance": false         // 与矮人结盟 → 否
}
```

**defeated 字段示例**（记录已杀Boss）：

```json
["goblin_chief", "shadow_dragon_whelp"]
// 已击败：地精头领、暗影幼龙
```

```sql
CREATE TABLE game_progress (
    save_id     INTEGER PRIMARY KEY                   -- 存档编号（主键，也是外键）
                REFERENCES save_slots(id) ON DELETE CASCADE,
    scene_id    TEXT DEFAULT 'river_town',            -- 当前场景ID
    flags       TEXT DEFAULT '{}',                    -- 剧情标记（JSON对象）
    defeated    TEXT DEFAULT '[]'                     -- 已击败Boss列表（JSON数组）
);
```

---

## 4. 存档与读档流程

### 4.1 存档流程（游戏内存 → 数据库）

```
第1步：调用 save_game(engine, slot)
第2步：写入或更新 save_slots 行（创建或覆盖存档元信息）
第3步：删除旧数据 → 重新插入所有 party_member 行（当前4个队员完整数据）
第4步：为每个队员保存其 member_auto_rules 配置
第5步：删除旧数据 → 重新插入所有 inventory 行（背包所有物品+装备状态）
第6步：删除旧数据 → 重新插入所有 quest_state 行（所有任务进度）
第7步：写入或更新 game_progress 行（场景、剧情标记、已击败Boss）
```

### 4.2 读档流程（数据库 → 游戏内存）

```
第1步：调用 load_game(engine, slot)
第2步：读取 save_slots 行 → 验证存档是否存在
第3步：读取 game_progress 行 → 恢复 场景ID、剧情标记、已击败Boss列表
第4步：读取 party_member 行 → 重建4个 Character 对象 → 填入 Party.members[0..3]
第5步：读取 member_auto_rules 行 → 为每个队员重建自动规则引擎
第6步：读取 inventory 行 → 重建背包物品列表和装备状态
第7步：读取 quest_state 行 → 重建任务管理器状态
```

---

## 5. 数据举例

以下用一个完整存档展示各表之间的关系：

### 场景
玩家创建了"阿尔萨斯"（人类战士）作为主角，在酒馆招募了"梅林"（精灵法师），在河畔镇接了一个任务"清剿地精"，打了Boss"地精头领"之后存档到槽位1。

### save_slots 表（1行）
| id | slot_name | party_name | avg_level | scene_id |
|----|-----------|------------|-----------|----------|
| 1 | 我的存档 | 龙焰小队 | 5 | river_town |

### party_member 表（2行，因为只有2个队员）
| id | save_id | name | race | class | is_main | level | hp_cur | hp_max | slot_index |
|----|---------|------|------|-------|---------|-------|--------|--------|------------|
| 1 | 1 | 阿尔萨斯 | human | warrior | 1 | 5 | 78 | 78 | 0 |
| 2 | 1 | 梅林 | elf | mage | 0 | 5 | 42 | 42 | 1 |

### member_auto_rules 表（每个队员6条）
| id | member_id | rule_id | enabled | threshold |
|----|-----------|---------|---------|-----------|
| 1 | 1 | self_heal | 1 | 30 |
| 2 | 1 | emergency_heal | 0 | 20 |

（阿尔萨斯是战士不会治疗，所以关了急救队友规则）

### inventory 表（3件物品）
| id | save_id | item_id | quantity | equipped_by |
|----|---------|---------|----------|-------------|
| 1 | 1 | iron_sword | 1 | 1 |
| 2 | 1 | wizard_staff | 1 | 2 |
| 3 | 1 | health_potion_s | 5 | 0 |

- 铁剑装备在队员1（阿尔萨斯）
- 法杖装备在队员2（梅林）
- 5瓶治疗药水在公共背包

### quest_state 表（1个任务）
| id | save_id | quest_id | status | progress |
|----|---------|----------|--------|----------|
| 1 | 1 | q_clear_goblins | active | {"objectives":[{"objective_id":"kill_chief","current_count":0}]} |

### game_progress 表（1行）
| save_id | scene_id | flags | defeated |
|---------|----------|-------|----------|
| 1 | river_town | {"tutorial_done":true} | ["goblin_chief"] |

---

## 6. 性能索引建议

当前设计依赖主键自带的索引。如果数据量增大（多存档位反复存取），建议添加以下显式索引：

```sql
-- 加速按存档查询队员（最常用）
CREATE INDEX IF NOT EXISTS idx_member_save ON party_member(save_id);

-- 加速按存档查询背包
CREATE INDEX IF NOT EXISTS idx_inventory_save ON inventory(save_id);

-- 加速按存档查询任务
CREATE INDEX IF NOT EXISTS idx_quest_save ON quest_state(save_id);

-- 加速按队员查询规则
CREATE INDEX IF NOT EXISTS idx_rules_member ON member_auto_rules(member_id);
```

> **注意**：SQLite 会自动为主键（PRIMARY KEY）建立索引，所以 `id` 列不需要额外建索引。
> 外键列加索引可以加速级联删除操作。
