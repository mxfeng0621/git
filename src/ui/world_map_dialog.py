"""两级分层世界地图对话框"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QWidget, QGridLayout,
)
from PySide6.QtCore import Qt, Signal

# ================================================================
# 地图数据
# ================================================================
REGIONS = {
    "eastern_valley": {
        "name": "东部谷地",
        "description": "艾尔德拉大陆东部的河谷平原，河畔镇所在之处。气候温和，是王国的主要农业区。",
        "icon": "🌾",
        "locations": [
            {"id": "river_town", "name": "河畔镇", "desc": "河边小镇，冒险的起点", "icon": "🏘️",
             "known": True},
            {"id": "dark_forest", "name": "幽暗森林", "desc": "地精肆虐的古老林地", "icon": "🌲",
             "known": True},
            {"id": "elf_ruins", "name": "精灵遗迹", "desc": "失落精灵文明的废墟", "icon": "🏛️",
             "known": True},
            {"id": "abandoned_mine", "name": "废弃矿洞", "desc": "矮人留下的矿坑", "icon": "⛏️",
             "known": True},
        ],
    },
    "kingdom_heart": {
        "name": "王国腹地",
        "description": "艾尔德拉王国的核心地带，王城所在地。繁华的商贸中枢，冒险者公会的总部也在此。",
        "icon": "🏰",
        "locations": [
            {"id": "royal_city", "name": "王城艾尔", "desc": "王国的首都", "icon": "👑",
             "known": False},
            {"id": "adventurer_guild", "name": "冒险者公会", "desc": "冒险者的聚集地", "icon": "⚔️",
             "known": False},
        ],
    },
    "northern_mountains": {
        "name": "北方山脉",
        "description": "横亘北境的高山群峰，矮人王国的所在地。据说龙脊山脉深处沉睡着一头上古巨龙。",
        "icon": "⛰️",
        "locations": [
            {"id": "dwarf_city", "name": "矮人之城", "desc": "矮人族的首都，凿山而建", "icon": "🏔️",
             "known": False},
            {"id": "dragon_peak", "name": "龙脊山峰", "desc": "传说中的上古龙巢", "icon": "🐉",
             "known": False},
        ],
    },
    "western_hills": {
        "name": "西部丘陵",
        "description": "连绵起伏的丘陵地带，精灵族的古老家园。神秘的石阵散布其间。",
        "icon": "🌿",
        "locations": [
            {"id": "elf_forest", "name": "精灵之森", "desc": "精灵族的隐秘家园", "icon": "🧝",
             "known": False},
        ],
    },
    "southern_coast": {
        "name": "南海岸",
        "description": "面向无尽之海的南部海岸线。港口城市船来船往，海盗和走私者在此出没。",
        "icon": "🌊",
        "locations": [
            {"id": "port_city", "name": "海港城", "desc": "南方的贸易港口", "icon": "⚓",
             "known": False},
        ],
    },
    "black_castle": {
        "name": "黑石城堡",
        "description": "矗立在东部谷地与王国腹地之间的黑暗要塞。传言是龙之影的巢穴之一。",
        "icon": "🏯",
        "locations": [
            {"id": "black_castle", "name": "黑石城堡", "desc": "被诅咒的黑暗要塞", "icon": "💀",
             "known": False},
        ],
    },
}


class WorldMapDialog(QDialog):
    travel_requested = Signal(str)  # scene_id to travel to

    def __init__(self, current_scene: str, parent=None):
        super().__init__(parent)
        self._current_scene = current_scene
        self.setWindowTitle("世界地图")
        self.resize(620, 500)
        self.setStyleSheet(
            "QDialog { background: #16213e; } "
            "QScrollArea { background: transparent; border: none; }"
        )

        self._root = QVBoxLayout(self)

        # 面包屑导航
        self._breadcrumb = QHBoxLayout()
        self._root.addLayout(self._breadcrumb)

        # 内容区
        self._stack = QVBoxLayout()
        self._root.addLayout(self._stack)

        # 显示第一级：大陆总览
        self._show_regions()

    def _show_regions(self) -> None:
        self._clear_content()
        self._clear_breadcrumb()
        self._breadcrumb.addWidget(self._crumb("🗺 艾尔德拉大陆", active=True))

        hdr = QLabel("艾尔德拉大陆 — 已知区域")
        hdr.setStyleSheet("font-size: 16px; font-weight: bold; color: #c9a96e; padding: 8px 0;")
        self._stack.addWidget(hdr)

        grid = QGridLayout()
        grid.setSpacing(10)

        for i, (rid, region) in enumerate(REGIONS.items()):
            card = self._region_card(region, rid)
            grid.addWidget(card, i // 2, i % 2)

        self._stack.addLayout(grid)
        self._stack.addStretch()

    def _show_region(self, region_id: str) -> None:
        self._clear_content()
        self._clear_breadcrumb()

        region = REGIONS.get(region_id)
        if not region:
            return

        self._breadcrumb.addWidget(self._btn_crumb("🗺 艾尔德拉", self._show_regions))
        self._breadcrumb.addWidget(QLabel(" ▸ "))
        self._breadcrumb.addWidget(self._crumb(f"{region['icon']} {region['name']}", active=True))

        hdr = QLabel(f"{region['icon']} {region['name']}")
        hdr.setStyleSheet("font-size: 16px; font-weight: bold; color: #c9a96e; padding: 4px 0;")
        self._stack.addWidget(hdr)

        desc = QLabel(region["description"])
        desc.setStyleSheet("font-size: 12px; color: #8a8fa0;")
        desc.setWordWrap(True)
        self._stack.addWidget(desc)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("QFrame { color: #3a3f55; }")
        self._stack.addWidget(sep)

        loc_hdr = QLabel("📍 地标")
        loc_hdr.setStyleSheet("font-size: 13px; font-weight: bold; color: #8ecae6;")
        self._stack.addWidget(loc_hdr)

        for loc in region["locations"]:
            row = QHBoxLayout()
            icon = loc["icon"] if loc["known"] else "❓"
            name = loc["name"] if loc["known"] else "？？？"
            desc = loc["desc"] if loc["known"] else "尚未探索"

            lbl = QLabel(f"{icon}  {name}")
            lbl.setStyleSheet(
                f"font-size: 13px; color: {'#d4c5a9' if loc['known'] else '#4a3f35'}; "
                f"min-width: 120px;"
            )
            row.addWidget(lbl)

            dl = QLabel(desc)
            dl.setStyleSheet("font-size: 11px; color: #6c757d;")
            dl.setWordWrap(True)
            row.addWidget(dl, stretch=1)

            if loc["known"] and loc["id"] != self._current_scene:
                btn = QPushButton("快速旅行")
                btn.setFixedHeight(24)
                btn.setStyleSheet(
                    "QPushButton { background: #2d5a27; color: #d4c5a9; border: none; "
                    "border-radius: 3px; font-size: 11px; padding: 2px 10px; } "
                    "QPushButton:hover { background: #3a7a35; }"
                )
                btn.clicked.connect(
                    lambda checked, lid=loc["id"]: self._travel(lid))
                row.addWidget(btn)

            self._stack.addLayout(row)

        self._stack.addStretch()

    def _travel(self, scene_id: str) -> None:
        self.travel_requested.emit(scene_id)
        self.accept()

    def _region_card(self, region: dict, region_id: str) -> QFrame:
        card = QPushButton()
        card.setFixedHeight(90)
        known_count = sum(1 for l in region["locations"] if l["known"])
        total = len(region["locations"])
        text = (f"{region['icon']}  {region['name']}\n"
                f"{region['description'][:60]}…\n"
                f"已探索 {known_count}/{total} 处")
        card.setText(text)
        card.setStyleSheet(
            "QPushButton { text-align: left; background: rgba(22,33,62,0.9); "
            "color: #d4c5a9; border: 1px solid #3a3f55; border-radius: 8px; "
            "padding: 12px; font-size: 12px; } "
            "QPushButton:hover { border-color: #c9a96e; background: rgba(22,33,62,1); }"
        )
        card.clicked.connect(lambda: self._show_region(region_id))
        return card

    def _clear_content(self) -> None:
        while self._stack.count():
            item = self._stack.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _clear_breadcrumb(self) -> None:
        while self._breadcrumb.count():
            item = self._breadcrumb.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _crumb(self, text: str, active: bool = False) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet(
            f"font-size: 13px; color: {'#c9a96e' if active else '#8a8fa0'}; "
            f"{'font-weight: bold;' if active else ''}"
        )
        return l

    def _btn_crumb(self, text: str, slot) -> QPushButton:
        btn = QPushButton(text)
        btn.setFlat(True)
        btn.setStyleSheet(
            "QPushButton { color: #8ecae6; font-size: 13px; border: none; } "
            "QPushButton:hover { color: #fff; text-decoration: underline; }"
        )
        btn.clicked.connect(slot)
        return btn
