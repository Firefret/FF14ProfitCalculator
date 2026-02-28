import json
from typing import Protocol

class Item(Protocol):
    name: str
    id: int

class Craftable(Protocol):
    recipe_id: int
    ingredients: list

class ItemBase:
    def __init__(self, name: str, item_id: int):
        self.name = name
        self.id = item_id

    def __repr__(self):
        return json.dumps(self.__dict__, indent=4, cls=SmartEncoder)

class CraftInfo:
    def __init__(self, recipe: int, ingredients: list[Item]):
        self.recipe_id = recipe
        self.ingredients = ingredients

    def __repr__(self):
        return json.dumps(self.__dict__, indent=4, cls=SmartEncoder)

class CraftableItem:
    def __init__(self, item: Item, craftable: Craftable):
        self.name = item.name
        self.id = item.id
        self.recipe_id = craftable.recipe_id
        self.ingredients = craftable.ingredients

    def __repr__(self):
        return json.dumps(self.__dict__, indent=4, cls=SmartEncoder)

class SmartEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)
