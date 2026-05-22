"""对话树系统"""

from dataclasses import dataclass, field


@dataclass
class DialogueOption:
    text: str                              # 显示给玩家的选项文本
    next_id: str = ""                      # 下一段对话id，空=结束
    condition: str = ""                    # 条件表达式（如 "level>=5" / "has_item:ring"）
    effects: dict = field(default_factory=dict)  # {"affinity": 10, "start_quest": "q001"}
    one_shot: bool = False                 # 只能选一次


@dataclass
class DialogueNode:
    node_id: str
    speaker: str                           # NPC名
    text: str                              # NPC说的话
    options: list[DialogueOption] = field(default_factory=list)
    on_enter: dict = field(default_factory=dict)  # 进入节点时的效果


@dataclass
class DialogueTree:
    npc_id: str
    npc_name: str
    greeting_node: str                     # 默认起始节点id
    nodes: dict[str, DialogueNode] = field(default_factory=dict)
    affinity: int = 0                      # 好感度 0-100


@dataclass
class DialogueManager:
    trees: dict[str, DialogueTree] = field(default_factory=dict)
    _used_options: set[str] = field(default_factory=set)       # "npc_id:node_id:option_idx"

    def register(self, tree: DialogueTree) -> None:
        self.trees[tree.npc_id] = tree

    def start(self, npc_id: str) -> DialogueNode | None:
        tree = self.trees.get(npc_id)
        if not tree:
            return None
        return tree.nodes.get(tree.greeting_node)

    def choose(self, npc_id: str, node: DialogueNode,
               option_index: int) -> DialogueNode | None:
        if option_index < 0 or option_index >= len(node.options):
            return None
        option = node.options[option_index]
        tree = self.trees.get(npc_id)
        if not tree:
            return None

        # one_shot 检查
        key = f"{npc_id}:{node.node_id}:{option_index}"
        if option.one_shot and key in self._used_options:
            return None
        self._used_options.add(key)

        # 好感度
        if "affinity" in option.effects:
            tree.affinity = max(0, min(100,
                                       tree.affinity + option.effects["affinity"]))

        if option.next_id:
            return tree.nodes.get(option.next_id)
        return None
