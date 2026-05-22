"""世界地图 — 场景拓扑与导航"""

from world.scenes import SCENES, Scene


class WorldMap:
    """管理场景连接与移动"""

    def __init__(self):
        self._scenes: dict[str, Scene] = dict(SCENES)

    def get(self, scene_id: str) -> Scene | None:
        return self._scenes.get(scene_id)

    def get_name(self, scene_id: str) -> str:
        scene = self.get(scene_id)
        return scene.name if scene else scene_id

    def get_description(self, scene_id: str) -> str:
        scene = self.get(scene_id)
        return scene.description if scene else "未知的地点。"

    def get_connections(self, scene_id: str) -> dict[str, str]:
        scene = self.get(scene_id)
        return dict(scene.connections) if scene else {}

    def move(self, scene_id: str, direction: str) -> str | None:
        """返回目标scene_id，无法移动返回None"""
        scene = self.get(scene_id)
        if not scene:
            return None

        # 精确匹配
        if direction in scene.connections:
            return scene.connections[direction]

        # 模糊匹配（方向包含关系）
        for key, target in scene.connections.items():
            if key in direction or direction in key:
                return target

        return None

    def monster_spawn(self, scene_id: str) -> list[str] | None:
        """返回随机遇敌的怪物id列表，无遇敌返回None"""
        import random
        scene = self.get(scene_id)
        if not scene or scene.is_safe or not scene.monster_spawns:
            return None

        for spawn in scene.monster_spawns:
            if random.random() * 100 < spawn["chance"]:
                count = random.randint(spawn.get("min_count", 1),
                                      spawn.get("max_count", 1))
                repeated = spawn["enemy_ids"] * (count // len(spawn["enemy_ids"]) + 1)
                return repeated[:count]

        return None

    @property
    def all_scenes(self) -> dict[str, Scene]:
        return dict(self._scenes)
