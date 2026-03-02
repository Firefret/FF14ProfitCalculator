from __future__ import annotations
from typing import Protocol
from dataclasses import dataclass


@dataclass
class CraftingInfo:
    recipe_id: int
    ingredients: list[Item]

class Craftable(Protocol):
    craftable: CraftingInfo

@dataclass
class GatheringInfo:
    is_gatherable: bool

class Gatherable(Protocol):
    gatherable: GatheringInfo

@dataclass
class MarketInfo:
    price: int
    server: str
    price_dynamics: float

class Marketable(Protocol):
    marketable: MarketInfo

@dataclass
class Item:
    name: str
    id: int
    craftable: CraftingInfo | None = None
    gatherable: GatheringInfo | None = None
    marketable: MarketInfo | None = None

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
