from __future__ import annotations
import math
from .itemRequest import ItemRequest
from .itemTypes import *
from .xivapi import fetch_top_item_data


@dataclass
class WishlistEntry:
    item: Item
    amount: int
    quality: bool

    def __init__(self, item: Item, amount: int, quality: bool) -> None:
        from core.config import DEFAULT_QUALITY
        self.item = item
        self.amount = amount
        self.quality = quality # todo: this should be set by user, got in an api request

    def __add__(self, other: WishlistEntry):
        if self.item.id != other.item.id:
            raise ValueError(f"Cannot add different items: {self.item.name} and {other.item.name}")

        self.amount += other.amount
        return self

    def __iadd__(self, other: WishlistEntry):
        if self.item.id != other.item.id:
            raise ValueError(f"Cannot add different items: {self.item.name} and {other.item.name}")

        self.amount += other.amount
        return self



@dataclass
class Wishlist:
    entries: dict[str, WishlistEntry]
    server: World

    def add(self, entry: WishlistEntry):
        if entry.item.name not in self.entries:
            self.entries[entry.item.name] = entry
        else:
            self.entries[entry.item.name] += entry

    async def process_request(self, request: ItemRequest):
        item = await fetch_top_item_data(request.item_name, request.server)
        amount_of_crafts = math.ceil(request.quantity / item.craftable.item_yield)
        wishlist_entry = WishlistEntry(item, amount_of_crafts, request.quality)
        self.add(wishlist_entry)

    @property
    def profit_prognosis(self) -> int:
        profit = 0
        for entry in self.entries.values():
            sales = entry.item.marketable.sales.hq if entry.quality else entry.item.marketable.sales.nq
        return profit

    #todo: log profit prognose with a dynamic mat price sum information (velocity, acceleration) used as a hard floor