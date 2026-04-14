import math

from .itemRequest import ItemRequest
from .itemTypes import *
from .xivapi import fetch_top_item_data


@dataclass
class WishlistEntry:
    item: Item
    amount: int

    def __init__(self, item: Item, amount: int) -> None:
        self.item = item
        self.amount = amount


@dataclass
class Wishlist:
    entries: dict[str, WishlistEntry]
    server: World

    def add(self, entry: WishlistEntry):
        if entry.item.name not in self.entries:
            self.entries[entry.item.name] = entry
        else:
            self.entries[entry.item.name].amount += entry

    async def process_request(self, request: ItemRequest):
        item = await fetch_top_item_data(request.item_name, request.server)
        amount_of_crafts = math.ceil(request.quantity / item.craftable.item_yield)
        wishlist_entry = WishlistEntry(item, amount_of_crafts)
        self.add(wishlist_entry)