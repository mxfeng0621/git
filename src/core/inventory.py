"""背包与装备管理"""

from dataclasses import dataclass, field
from data.items import ItemTemplate, ItemType, ITEMS


@dataclass
class InventoryItem:
    item_id: str
    quantity: int = 1
    equipped_by: int = 0              # 0=背包, >0=装备在member_id上

    @property
    def template(self) -> ItemTemplate:
        return ITEMS.get(self.item_id)


@dataclass
class Inventory:
    items: list[InventoryItem] = field(default_factory=list)
    gold: int = 0

    # ---- 增删改 ----
    def add(self, item_id: str, qty: int = 1) -> None:
        existing = next((i for i in self.items
                         if i.item_id == item_id and i.equipped_by == 0), None)
        if existing:
            existing.quantity += qty
        else:
            self.items.append(InventoryItem(item_id=item_id, quantity=qty))

    def remove(self, item_id: str, qty: int = 1) -> bool:
        item = next((i for i in self.items
                     if i.item_id == item_id and i.equipped_by == 0), None)
        if item and item.quantity >= qty:
            item.quantity -= qty
            if item.quantity <= 0:
                self.items.remove(item)
            return True
        return False

    def count(self, item_id: str) -> int:
        return sum(i.quantity for i in self.items if i.item_id == item_id)

    # ---- 装备 ----
    def equip(self, item_id: str, member_id: int) -> bool:
        tmpl = ITEMS.get(item_id)
        if not tmpl or tmpl.item_type == ItemType.CONSUMABLE:
            return False
        # 卸下同部位旧装备
        self.unequip_slot(tmpl.slot, member_id)
        # 从背包扣除
        if not self.remove(item_id, 1):
            return False
        self.items.append(InventoryItem(item_id=item_id, equipped_by=member_id))
        return True

    def unequip(self, item_id: str, member_id: int) -> bool:
        item = next((i for i in self.items
                     if i.item_id == item_id and i.equipped_by == member_id), None)
        if item:
            item.equipped_by = 0
            return True
        return False

    def unequip_slot(self, slot: str, member_id: int) -> None:
        for item in self.items:
            if item.equipped_by == member_id:
                tmpl = item.template
                if tmpl and tmpl.slot == slot:
                    item.equipped_by = 0

    def equipped_of(self, member_id: int) -> list[InventoryItem]:
        return [i for i in self.items if i.equipped_by == member_id]

    def backpack_items(self) -> list[InventoryItem]:
        return [i for i in self.items if i.equipped_by == 0]

    # ---- 消耗品使用 ----
    def use_consumable(self, item_id: str, member_id: int) -> dict | None:
        """返回效果dict或None"""
        tmpl = ITEMS.get(item_id)
        if not tmpl or tmpl.item_type != ItemType.CONSUMABLE:
            return None
        if not self.remove(item_id, 1):
            return None
        effect = {}
        if tmpl.heal_hp:
            effect["heal_hp"] = tmpl.heal_hp
        if tmpl.heal_mp:
            effect["heal_mp"] = tmpl.heal_mp
        if tmpl.temp_attr_bonus:
            effect["temp_attr"] = dict(tmpl.temp_attr_bonus)
            effect["duration"] = tmpl.duration_turns
        return effect

    # ---- 装备属性汇总 ----
    def equipment_bonuses(self, member_id: int) -> dict:
        """返回该成员所有装备的属性加成汇总"""
        bonuses = {"armor": 0, "str": 0, "dex": 0, "con": 0,
                   "int": 0, "wis": 0, "cha": 0, "hp": 0, "mp": 0,
                   "damage_dice": "1d4"}
        for item in self.equipped_of(member_id):
            tmpl = item.template
            if not tmpl:
                continue
            bonuses["armor"] += tmpl.armor_value
            bonuses["hp"] += tmpl.hp_bonus
            bonuses["mp"] += tmpl.mp_bonus
            if tmpl.damage_dice:
                bonuses["damage_dice"] = tmpl.damage_dice
            for attr, val in tmpl.attr_bonus.items():
                bonuses[attr] += val
        return bonuses
