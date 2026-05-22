"""任务系统"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


class QuestType(Enum):
    MAIN = "main"
    SIDE = "side"
    BOUNTY = "bounty"
    CLASS_QUEST = "class_quest"


@dataclass
class QuestObjective:
    objective_id: str
    description: str
    target_type: str           # "kill" / "collect" / "talk" / "explore"
    target_id: str = ""        # 怪物id / 物品id / NPC id / 场景id
    target_count: int = 1
    current_count: int = 0

    @property
    def is_complete(self) -> bool:
        return self.current_count >= self.target_count

    @property
    def progress_pct(self) -> int:
        return int(self.current_count / max(self.target_count, 1) * 100)


@dataclass
class QuestReward:
    xp: int = 0
    gold: int = 0
    items: list[dict] = field(default_factory=list)   # [{item_id, quantity}]


@dataclass
class QuestDef:
    quest_id: str
    name: str
    description: str
    quest_type: QuestType
    objectives: list[QuestObjective]
    reward: QuestReward
    prerequisites: list[str] = field(default_factory=list)    # 前置任务id
    level_required: int = 1
    giver_npc: str = ""
    completion_text: str = ""


class QuestStatus(Enum):
    AVAILABLE = "available"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class QuestState:
    quest_id: str
    status: QuestStatus = QuestStatus.AVAILABLE
    objectives: list[QuestObjective] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return all(o.is_complete for o in self.objectives)


@dataclass
class QuestManager:
    quests: dict[str, QuestState] = field(default_factory=dict)
    completed_ids: set[str] = field(default_factory=set)

    def init_from_defs(self, defs: list[QuestDef]) -> None:
        for qd in defs:
            if qd.quest_id not in self.quests:
                self.quests[qd.quest_id] = QuestState(
                    quest_id=qd.quest_id,
                    objectives=[QuestObjective(**o.__dict__) for o in qd.objectives],
                )

    def start(self, quest_id: str) -> bool:
        qs = self.quests.get(quest_id)
        if qs and qs.status == QuestStatus.AVAILABLE:
            qs.status = QuestStatus.ACTIVE
            return True
        return False

    def complete(self, quest_id: str) -> bool:
        qs = self.quests.get(quest_id)
        if qs and qs.status == QuestStatus.ACTIVE and qs.is_complete:
            qs.status = QuestStatus.COMPLETED
            self.completed_ids.add(quest_id)
            return True
        return False

    def fail(self, quest_id: str) -> bool:
        qs = self.quests.get(quest_id)
        if qs and qs.status == QuestStatus.ACTIVE:
            qs.status = QuestStatus.FAILED
            return True
        return False

    def progress(self, target_type: str, target_id: str, count: int = 1) -> list[str]:
        """推进所有活跃任务中匹配的目标，返回已完成的任务id列表"""
        completed = []
        for qs in self.quests.values():
            if qs.status != QuestStatus.ACTIVE:
                continue
            for obj in qs.objectives:
                if obj.target_type == target_type and obj.target_id == target_id:
                    obj.current_count = min(obj.target_count,
                                            obj.current_count + count)
            if qs.is_complete:
                qs.status = QuestStatus.COMPLETED
                self.completed_ids.add(qs.quest_id)
                completed.append(qs.quest_id)
        return completed

    def active_quests(self) -> list[QuestState]:
        return [q for q in self.quests.values() if q.status == QuestStatus.ACTIVE]

    def available_quests(self) -> list[QuestState]:
        return [q for q in self.quests.values() if q.status == QuestStatus.AVAILABLE]
