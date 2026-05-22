# 开发文档

## 1. 技术栈

| 层 | 选型 | 说明 |
|----|------|------|
| GUI | PySide6 6.5+ | Qt 官方 Python 绑定，LGPL 许可 |
| 数据库 | sqlite3 | Python 内置，零配置，单文件存储 |
| 数据模型 | dataclasses | 标准库，类型安全，轻量 |
| 样式 | QSS (Qt Style Sheet) | 类 CSS 语法，全局/组件级样式 |
| 打包 | PyInstaller | 生成独立 exe |
| 测试 | pytest | 核心逻辑单元测试 |

## 2. 项目结构

```
src/
├── main.py                 # 应用入口
├── app/                    # 应用层（组装、启动）
│   ├── main_window.py      # QMainWindow 主窗口
│   └── styles.py           # QSS 样式常量
├── core/                   # 核心逻辑，零 UI 依赖
│   ├── engine.py           # GameEngine 总调度
│   ├── character.py        # 角色数据类与升级逻辑
│   ├── party.py            # 队伍管理（招募/离队/阵容） 
│   ├── combat.py           # 战斗引擎（自动回合 + 策略驱动）
│   ├── auto_rules.py       # 条件规则引擎
│   ├── dice.py             # 骰子工具
│   ├── inventory.py        # 背包与装备管理
│   ├── quest.py            # 任务状态机
│   └── dialogue.py         # 对话树结构
├── data/                   # 静态游戏数据（常量/模板）
│   ├── classes.py          # 职业模板（战士/法师/盗贼/牧师/游侠）
│   ├── races.py            # 种族模板
│   ├── monsters.py         # 怪物模板
│   ├── items.py            # 装备和道具模板
│   ├── spells.py           # 法术模板
│   └── quests.py           # 任务定义
├── world/                  # 世界内容
│   ├── world_map.py        # 场景拓扑图
│   ├── scenes.py           # 场景数据（描述/链接/事件）
│   └── story.py            # 剧情脚本（触发条件/对话/过场）
├── db/                     # 持久化层
│   ├── database.py         # 连接管理与建表
│   ├── models.py           # 表对应的 dataclass
│   └── repository.py       # CRUD 操作
├── ui/                     # UI 组件
│   ├── character_panel.py  # 角色状态面板
│   ├── scene_view.py       # 场景主视图（插图+文本）
│   ├── log_panel.py        # 消息日志
│   ├── command_input.py    # 命令输入框
│   ├── inventory_dialog.py # 背包/装备弹窗
│   ├── quest_dialog.py     # 任务日志弹窗
│   ├── combat_widget.py    # 战斗界面
│   └── menu_bar.py         # 菜单栏
├── services/               # 服务层
│   ├── save_service.py     # 存档/读档
│   ├── image_provider.py   # 插图提供者接口
│   └── command_parser.py   # 文本命令解析
└── utils/
    └── constants.py        # 枚举、常量
```

## 3. 数据库设计

游戏数据存储于 `saves/game.db`，每个存档位一组关联行。

### 3.1 表结构

```sql
CREATE TABLE save_slots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_name   TEXT NOT NULL,
    party_name  TEXT NOT NULL DEFAULT '冒险小队',
    avg_level   INTEGER DEFAULT 1,
    play_secs   INTEGER DEFAULT 0,
    scene_id    TEXT,
    created_at  TEXT DEFAULT (datetime('now','localtime')),
    updated_at  TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE party_member (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    save_id       INTEGER REFERENCES save_slots(id) ON DELETE CASCADE,
    name          TEXT NOT NULL,
    race          TEXT,
    class         TEXT,
    is_main       INTEGER DEFAULT 0,    -- 1=主角(不可离队)
    level         INTEGER DEFAULT 1,
    xp            INTEGER DEFAULT 0,
    hp_cur        INTEGER, hp_max      INTEGER,
    mp_cur        INTEGER, mp_max      INTEGER,
    str           INTEGER, dex         INTEGER, con INTEGER,
    intel         INTEGER, wis         INTEGER, cha INTEGER,
    gold          INTEGER DEFAULT 0,
    slot_index    INTEGER DEFAULT 0     -- 在队伍中的位置 0-3
);

CREATE TABLE member_auto_rules (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id     INTEGER REFERENCES party_member(id) ON DELETE CASCADE,
    rule_id       TEXT NOT NULL,         -- 如 'self_heal' / 'mana_saver' / 'boss_burst'
    enabled       INTEGER DEFAULT 1,
    threshold     INTEGER DEFAULT 30     -- 触发阈值（百分比等）
);

CREATE TABLE inventory (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    save_id   INTEGER REFERENCES save_slots(id) ON DELETE CASCADE,
    item_id   TEXT NOT NULL,
    quantity  INTEGER DEFAULT 1,
    equipped_by INTEGER DEFAULT 0  -- 0=队伍背包, 非0=装备在member_id身上
);

CREATE TABLE quest_state (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    save_id   INTEGER REFERENCES save_slots(id) ON DELETE CASCADE,
    quest_id  TEXT NOT NULL,
    status    TEXT DEFAULT 'active',  -- active / completed / failed
    progress  TEXT DEFAULT '{}'
);

CREATE TABLE game_progress (
    save_id     INTEGER PRIMARY KEY REFERENCES save_slots(id) ON DELETE CASCADE,
    scene_id    TEXT,
    flags       TEXT DEFAULT '{}',
    defeated    TEXT DEFAULT '[]'
);
```

### 3.2 外键与级联

- 所有数据表通过 `save_id` 关联 `save_slots`
- `ON DELETE CASCADE` 确保删除存档时清理所有关联数据
- `PRAGMA foreign_keys = ON` 在连接时启用

## 4. 核心模块接口

### 4.1 GameEngine（引擎调度）

```python
class GameEngine:
    """中央调度器"""
    party: Party                          # 4人队伍
    inventory: Inventory                  # 队伍背包
    quest_manager: QuestManager
    combat: Combat | None                 # 非None时战斗进行中
    auto_rules: AutoRuleEngine            # 条件规则引擎
    world: WorldMap
    current_scene: Scene

    def execute(self, command: Command) -> ActionResult: ...
    def start_combat(self, enemies: list[Monster]) -> None:
        """弹出策略面板 → 确认后开始自动战斗"""
    def adjust_strategy(self, member_index: int, strategy: Strategy) -> None: ...
    def use_item_manual(self, item_id: str, target: str) -> ActionResult: ...
```

### 4.2 Party & Character（队伍与角色）

```python
@dataclass
class Party:
    members: list[Character]             # 固定4人，按slot_index排序
    bench: list[Character]               # 酒馆待命角色
    gold: int

    def get_front_row(self) -> list[Character]: ...  # 前排(战士/盗贼)
    def get_back_row(self) -> list[Character]: ...   # 后排(法师/牧师/游侠)
    def recruit(self, char: Character) -> None: ...
    def swap(self, member_index: int, bench_index: int) -> None: ...
    def living(self) -> list[Character]: ...          # HP>0的存活队员
    def distribute_xp(self, amount: int, participants: list[int]) -> None: ...

@dataclass
class Character:
    name: str
    race: Race
    class_: CharacterClass
    level: int = 1
    xp: int = 0
    attributes: dict[str, int]           # str/dex/con/int/wis/cha
    hp_current: int; hp_max: int
    mp_current: int; mp_max: int
    unlocked_skills: list[Skill]         # 已解锁技能（按等级表）
    racial_active: RacialSkill           # 种族主动技能
    racial_passives: list[Passive]       # 种族被动特质
    strategy: StrategyType = StrategyType.BALANCED
    is_main: bool = False

    def add_xp(self, amount: int) -> bool:               # True=升级
    def xp_to_next(self) -> int:                          # 距下一级还差多少
    def get_skill(self, skill_id: str) -> Skill | None: ...
    def attributes_with_racial(self) -> dict[str, int]:   # 含种族加成的最终属性

@dataclass
class Skill:
    skill_id: str                        # 'heavy_strike' / 'fireball' / 'backstab'
    name: str                            # 猛击 / 火球术 / 偷袭
    level_required: int
    mp_cost: int = 0
    cooldown: int = 0                    # 冷却回合数，0=无冷却
    damage_multiplier: float = 1.0
    target_type: str                     # 'single' / 'all_enemy' / 'all_ally' / 'self'
    extra_effects: dict = {}             # {'slow':1, 'dot':[5,3]} 等附加效果

@dataclass
class RacialSkill:
    skill_id: str
    name: str
    use_limit: str                       # 'once_per_combat' / 'once_per_explore'
    effect: dict
```

### 4.3 固定升级表数据

职业升级表以数据驱动方式定义，存放在 `data/classes.py`：

```python
CLASS_TABLES: dict[str, dict[int, list[Skill]]] = {
    "战士": {
        1:  [Skill("heavy_armor", "重甲精通", ...), Skill("taunt", "挑衅", ...)],
        3:  [Skill("heavy_strike", "猛击", ...)],
        5:  [Skill("extra_attack", "额外攻击", ...)],
        7:  [Skill("armor_break", "破甲斩", ...)],
        10: [Skill("war_cry", "战吼", ...)],
        # ...
    },
    "法师": { ... },
    # ...
}
```

购点数据定义在 `data/races.py`：

```python
POINT_BUY_COST = {
    8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9
}
TOTAL_POINTS = 27

RACIAL_DATA = {
    "人类": RacialData(
        attr_bonus={"str":1,"dex":1,"con":1,"int":1,"wis":1,"cha":1},
        active=RacialSkill("adversity", "逆境求生", use_limit="once_per_combat",
                           effect={"dodge_bonus": 20, "duration": 1}),
        passives=[Passive("versatile", "多才多艺", {"xp_bonus": 0.05}),
                  Passive("diplomat", "外交手腕", {"price_bonus": 0.05})]
    ),
    # ...
}
```

### 4.4 Combat（策略驱动自动战斗）

```python
class Combat:
    party: Party
    enemies: list[Monster]
    round_number: int
    log: list[CombatEvent]

    def set_strategies(self, mapping: dict[int, StrategyType]) -> None:
        """为每位队员设置战斗策略"""

    def auto_round(self) -> list[CombatEvent]:
        """执行一整个自动回合，返回事件列表"""
        for member in sort_by_speed(self.party.members):
            # 1. 先检查条件规则（优先级高于策略）
            rule_action = auto_rule_engine.check(member, self)
            # 2. 无规则触发则按策略行动
            action = rule_action or resolve_strategy(member)
            event = self.execute_action(member, action)
            self.log.append(event)
        # 怪物行动
        for enemy in self.enemies:
            event = self.execute_monster(enemy)
            self.log.append(event)

    def execute_action(self, actor, action) -> CombatEvent: ...
    def check_end(self) -> CombatResult | None: ...

class StrategyType(Enum):
    FULL_ASSAULT = "全力猛攻"
    BALANCED = "平衡输出"
    CONSERVE_MANA = "保留法力"
    PRIORITY_HEAL = "优先治疗"
    DEFEND = "防御牵制"

class CombatEvent:
    actor: str; action: str; target: str
    damage: int; healing: int
    is_critical: bool; is_kill: bool
    text: str                            # 战斗日志文本
```

### 4.5 AutoRuleEngine（条件规则）

```python
class AutoRuleEngine:
    rules: dict[int, list[AutoRule]]     # member_id → 规则列表

    def check(self, member: Character, combat: Combat) -> Action | None:
        """按优先级遍历规则，返回第一个触发的动作，无触发返回None"""
        for rule in self.rules[member.id]:
            if rule.enabled and rule.evaluate(member, combat):
                return rule.action
        return None

@dataclass
class AutoRule:
    rule_id: str                         # 'self_heal' / 'mana_saver' / 'boss_burst' ...
    enabled: bool
    threshold: int                       # 触发阈值
    action: Action

    def evaluate(self, member, combat) -> bool: ...
```

内置规则模板：
| rule_id | 默认条件 | 动作 |
|---------|----------|------|
| `self_heal` | 自身HP < 30% | 使用最低级治疗药水 |
| `emergency_heal` | 队友HP < 20% | 牧师施放单体治疗 |
| `mana_saver` | 自身MP < 10% | 切换为保留法力 |
| `finish_off` | 敌人HP < 15% | 全员优先攻击该目标 |
| `boss_burst` | 存在Boss级敌人 | 法师使用最强技能 |
| `group_heal` | 3人以上HP < 50% | 牧师施放群体治疗 |

### 4.6 CommandParser（命令解析）

```python
class CommandParser:
    def parse(self, text: str) -> Command | Error:
        """将原始文本解析为Command结构"""

@dataclass
class Command:
    action: ActionType       # 枚举：ATTACK / CAST / MOVE / TALK / ...
    target: str | None
    params: dict[str, str]
```

### 4.7 ImageProvider（插图接口）

```python
class ImageProvider(ABC):
    @abstractmethod
    def get_scene_image(self, scene_id: str) -> QPixmap | None: ...

class LocalImageProvider(ImageProvider):
    """从 assets/images/scenes/{scene_id}.png 加载"""
    def __init__(self, base_path: str): ...

# 未来实现
# class AIImageProvider(ImageProvider):
#     def __init__(self, api_key: str, endpoint: str): ...
```

## 5. 事件通信

使用 PySide6 信号/槽机制解耦 UI 与逻辑：

```python
class GameSignals(QObject):
    # 队伍级事件
    hp_changed = Signal(int, int, int)       # member_index, cur, max
    mp_changed = Signal(int, int, int)       # member_index, cur, max
    strategy_changed = Signal(int, str)      # member_index, strategy_name
    member_level_up = Signal(int, int)       # member_index, new_level

    # 战斗事件
    combat_started = Signal(list)            # enemies info
    combat_round = Signal(list)              # CombatEvent列表
    combat_ended = Signal(object)            # CombatResult

    # 世界事件
    scene_changed = Signal(str, str)         # scene_id, description
    message = Signal(str, str)               # text, category
    item_acquired = Signal(str, int)         # item_id, quantity
    quest_updated = Signal(str, str)         # quest_id, status
    gold_changed = Signal(int)               # new_gold_total
```

Engine 持有 `GameSignals` 实例，各 UI 组件订阅所需信号。

## 6. 数据流

```
探索模式：
  用户输入 → CommandParser → Command
      → GameEngine.execute(Command)
          → 修改 Core 对象（Party/Inventory/Quest/...）
          → 发出 GameSignals → UI 组件更新
          → 返回 ActionResult → 追加到 LogPanel

战斗模式：
  触发遇敌 → GameEngine.start_combat(enemies)
      → [策略面板] 玩家确认各人策略
      → Combat.auto_round() 循环:
          每回合 →
              AutoRuleEngine.check() 遍历条件规则
              → 按策略/规则自动选择动作
              → execute_action() 产生 CombatEvent
              → 发出 combat_round 信号 → LogPanel 滚动日志
              → check_end() → 继续/结束
      → combat_ended → 结算经验/掉落 → 回到探索模式
```

## 7. 构建与打包

### requirements.txt

```
PySide6>=6.5.0
```

### PyInstaller 打包

```bash
pyinstaller --name "龙焰传说" \
    --windowed \
    --icon assets/icon.ico \
    --add-data "assets;assets" \
    --add-data "data;data" \
    src/main.py
```

输出至 `dist/龙焰传说.exe`。

## 8. 版本管理

使用 `tools/` 目录管理阶段快照：

```
tools/
├── v0.1_project_init/     # 初始工程化
├── v0.2_core_systems/     # 核心逻辑完成
├── v0.3_db_save_load/     # 数据库与存档
├── v0.4_ui_complete/      # UI完成
├── v0.5_game_content/     # 游戏内容填充
└── v1.0_release/          # 正式发布
```
