"""队伍管理"""

from dataclasses import dataclass, field
from core.character import Character


@dataclass
class Party:
    members: list[Character | None] = field(default_factory=lambda: [None, None, None, None])
    bench: list[Character] = field(default_factory=list)       # 酒馆待命
    gold: int = 0

    def __post_init__(self):
        # 确保members长度=4
        while len(self.members) < 4:
            self.members.append(None)

    # ---- 阵容 ----
    def add_member(self, char: Character, slot: int = -1) -> bool:
        """添加队员，slot=-1自动找空位，返回是否成功"""
        if slot == -1:
            for i, m in enumerate(self.members):
                if m is None:
                    slot = i
                    break
            else:
                return False
        if self.members[slot] is not None:
            return False
        char.slot_index = slot
        self.members[slot] = char
        return True

    def remove_member(self, slot: int) -> Character | None:
        """移除队员到酒馆"""
        if self.members[slot] and not self.members[slot].is_main:
            char = self.members[slot]
            self.members[slot] = None
            self.bench.append(char)
            return char
        return None

    def swap(self, slot: int, bench_index: int) -> bool:
        if 0 <= bench_index < len(self.bench) and 0 <= slot < 4:
            char = self.members[slot]
            if char and char.is_main:
                return False
            self.members[slot], self.bench[bench_index] = \
                self.bench[bench_index], char
            return True
        return False

    def recruit(self, char: Character) -> None:
        """新角色加入——优先填队，否则进酒馆"""
        if not self.add_member(char):
            self.bench.append(char)

    # ---- 查询 ----
    def active_count(self) -> int:
        return sum(1 for m in self.members if m is not None)

    def living(self) -> list[Character]:
        return [m for m in self.members if m is not None and m.is_alive]

    def all_dead(self) -> bool:
        return len(self.living()) == 0

    def get(self, slot: int) -> Character | None:
        return self.members[slot] if 0 <= slot < 4 else None

    def get_living(self, slot: int) -> Character | None:
        m = self.get(slot)
        return m if m and m.is_alive else None

    # ---- 前排/后排 ----
    def front_row(self) -> list[int]:
        """返回前排索引（战士/盗贼优先）"""
        front = []
        for i, m in enumerate(self.members):
            if m and m.is_alive and m.class_id in ("warrior", "rogue"):
                front.append(i)
        for i, m in enumerate(self.members):
            if m and m.is_alive and i not in front:
                front.append(i)
        return front[:2]

    def back_row(self) -> list[int]:
        front = self.front_row()
        return [i for i in range(4) if self.members[i] and self.members[i].is_alive
                and i not in front]

    # ---- 经验分配 ----
    def distribute_xp(self, amount: int, participant_indices: list[int]) -> list[str]:
        """分配经验值，返回升级消息列表"""
        msgs = []
        for i in participant_indices:
            m = self.members[i]
            if m and m.is_alive:
                leveled = m.add_xp(amount)
                if leveled:
                    msgs.append(f"{m.name} 升到 Lv.{m.level}！")
        return msgs

    # ---- 休息 ----
    def rest_all(self) -> None:
        for m in self.members:
            if m:
                m.rest()
