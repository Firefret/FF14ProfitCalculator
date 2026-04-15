import math
from .config import DEFAULT_QUALITY
from .itemRequest import ItemRequest
from .itemTypes import *
from .xivapi import fetch_top_item_data


@dataclass
class WishlistEntry:
    item: Item
    amount: int
    quality: bool

    def __init__(self, item: Item, amount: int) -> None:
        self.item = item
        self.amount = amount
        self.quality = DEFAULT_QUALITY


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

    @property
    def profit_prognosis(self) -> int:
        profit = 0
        for entry in self.entries.values():
            sales = entry.item.marketable.sales.hq if entry.quality else entry.item.marketable.sales.nq
        return profit

    #todo: log profit prognose with a dynamic mat price sum information (velocity, acceleration) used as a hard floor