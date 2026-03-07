from __future__ import annotations
from typing import Protocol
from dataclasses import dataclass
from enum import Enum

class Crafter(Enum):
    BSM = "Smithing"
    ARM = "Armorcraft"
    ALC = "Alchemy"
    GSM = "Goldsmithing"
    WVR = "Clothcraft"
    CUL = "Cooking"
    CRP = "Woodworking"
    LTW = "Leatherworking"



@dataclass
class CraftingData:
    recipe_id: int
    item_yield: int
    ingredients: tuple[list[Item | Craftable], list[int]]
    craft_class: Crafter

class Craftable(Protocol):
    craftable: CraftingData

@dataclass
class GatheringData:
    is_gatherable: bool

class Gatherable(Protocol):
    gatherable: GatheringData

@dataclass
class MarketData:
    __is_tradeable__: bool
    price: int | None = None
    server: str | None = None
    price_dynamics: float | None = None

class Marketable(Protocol):
    marketable: MarketData

@dataclass
class Item:
    name: str
    id: int
    craftable: CraftingData | None = None
    gatherable: GatheringData | None = None
    marketable: MarketData | None = None


def is_craftable(item: Item) -> bool:
    if item.craftable:
        return True
    else:
        return False

def is_gatherable(item: Item) -> bool:
    if item.gatherable:
        return True
    else:
        return False

def is_marketable(item: Item) -> bool:
    if item.marketable:
        return True
    else:
        return False
