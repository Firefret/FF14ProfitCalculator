import asyncio

from .itemTypes import *


@dataclass
class CacheEntry:
    item: Item
    garland_data: dict | None = None

    def __init__(self, item: Item, garland_data = None):
        self.item = item
        self.garland_data = garland_data if garland_data is not None else None

data = {
    "Fire Shard" : CacheEntry(Item("Fire Shard", 2, f"https://www.garlandtools.org/files/icons/item/2.png")),
    "Ice Shard" : CacheEntry(Item("Ice Shard", 3, "https://www.garlandtools.org/files/icons/item/3.png")),
    "Wind Shard": CacheEntry(Item("Wind Shard", 4, "https://www.garlandtools.org/files/icons/item/4.png")),
    "Earth Shard" : CacheEntry(Item("Earth Shard", 5, "https://www.garlandtools.org/files/icons/item/5.png")),
    "Lightning Shard" : CacheEntry(Item("Lightning Shard", 6, "https://www.garlandtools.org/files/icons/item/6.png")),
    "Water Shard" : CacheEntry(Item("Water Shard", 7, "https://www.garlandtools.org/files/icons/item/7.png")),
    "Fire Crystal" : CacheEntry(Item("Fire Crystal", 8, "https://www.garlandtools.org/files/icons/item/8.png")),
    "Ice Crystal" : CacheEntry(Item("Ice Crystal", 9, "https://www.garlandtools.org/files/icons/item/9.png")),
    "Wind Crystal" : CacheEntry(Item("Wind Crystal", 10, "https://www.garlandtools.org/files/icons/item/10.png")),
    "Earth Crystal" : CacheEntry(Item("Earth Crystal", 11, "https://www.garlandtools.org/files/icons/item/11.png")),
    "Lightning Crystal" : CacheEntry(Item("Lightning Crystal", 12, "https://www.garlandtools.org/files/icons/item/12.png")),
    "Water Crystal" : CacheEntry(Item("Water Crystal", 13, "https://www.garlandtools.org/files/icons/item/13.png")),
    "Fire Cluster" : CacheEntry(Item("Fire Cluster", 14, "https://www.garlandtools.org/files/icons/item/14.png")),
    "Ice Cluster" : CacheEntry(Item("Ice Cluster", 15, f"https://www.garlandtools.org/files/icons/item/15.png")),
    "Wind Cluster" : CacheEntry(Item("Wind Cluster", 16, f"https://www.garlandtools.org/files/icons/item/16.png")),
    "Earth Cluster" : CacheEntry(Item("Earth Cluster", 17, f"https://www.garlandtools.org/files/icons/item/17.png")),
    "Lightning Cluster" : CacheEntry(Item("Lightning Cluster", 18, "https://www.garlandtools.org/files/icons/item/18.png")),
    "Water Cluster" : CacheEntry(Item("Water Cluster", 19, f"https://www.garlandtools.org/files/icons/item/19.png")),
    "Gil" : CacheEntry(Item(name='Gil', id=1, icon_url='https://www.garlandtools.org/files/icons/item/1.png')),
    "Grand Company Seal": CacheEntry(Item("Grand Company Seal", 20, 'https://www.garlandtools.org/files/icons/item/20.png'))
}

being_fetched: dict[str, asyncio.Task] = {}

def get_cached_item(name: str) -> Item | bool:
    if name in data:
        return data[name].item
    else:
        return False

def get_cached_garland_data(name:str):
    if name in data:
        return data[name].garland_data
    else:
        return False

def cache_item(item: Item, garland_data = None):
    if garland_data is None:
        data[item.name] = CacheEntry(item)
    else:
        data[item.name] = CacheEntry(item, garland_data)