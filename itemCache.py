from itemTypes import *

item_cache = {
    "Fire Shard" : Item("Fire Shard", 2, f"https://www.garlandtools.org/files/icons/item/2.png"),
    "Ice Shard" : Item("Ice Shard", 3, "https://www.garlandtools.org/files/icons/item/3.png"),
    "Wind Shard": Item("Wind Shard", 4, "https://www.garlandtools.org/files/icons/item/4.png"),
    "Earth Shard" : Item("Earth Shard", 5, "https://www.garlandtools.org/files/icons/item/5.png"),
    "Lightning Shard" : Item("Lightning Shard", 6, "https://www.garlandtools.org/files/icons/item/6.png"),
    "Water Shard" : Item("Water Shard", 7, "https://www.garlandtools.org/files/icons/item/7.png"),
    "Fire Crystal" : Item("Fire Crystal", 8, "https://www.garlandtools.org/files/icons/item/8.png"),
    "Ice Crystal" : Item("Ice Crystal", 9, "https://www.garlandtools.org/files/icons/item/9.png"),
    "Wind Crystal" : Item("Wind Crystal", 10, "https://www.garlandtools.org/files/icons/item/10.png"),
    "Earth Crystal" : Item("Earth Crystal", 11, "https://www.garlandtools.org/files/icons/item/11.png"),
    "Lightning Crystal" : Item("Lightning Crystal", 12, "https://www.garlandtools.org/files/icons/item/12.png"),
    "Water Crystal" : Item("Water Crystal", 13, "https://www.garlandtools.org/files/icons/item/13.png"),
    "Fire Cluster" : Item("Fire Cluster", 14, "https://www.garlandtools.org/files/icons/item/14.png"),
    "Ice Cluster" : Item("Ice Cluster", 15, f"https://www.garlandtools.org/files/icons/item/15.png"),
    "Wind Cluster" : Item("Wind Cluster", 16, f"https://www.garlandtools.org/files/icons/item/16.png"),
    "Earth Cluster" : Item("Earth Cluster", 17, f"https://www.garlandtools.org/files/icons/item/17.png"),
    "Lightning Cluster" : Item("Lightning Cluster", 18, "https://www.garlandtools.org/files/icons/item/18.png"),
    "Water Cluster" : Item("Water Cluster", 19, f"https://www.garlandtools.org/files/icons/item/19.png"),
    "Gil" : Item(name='Gil', id=1, icon_url='https://www.garlandtools.org/files/icons/item/1.png', craftable=None, gatherable=None, marketable=MarketData(__is_tradeable__=True, price=None, server=None, price_dynamics=None), huntable=None, vendorable=None)
}


def get_cached_item(name: str) -> Item | bool:
    if name in item_cache:
        return item_cache[name]
    else:
        return False

def cache_item(item: Item) -> bool:
    if item.name not in item_cache:
        item_cache[item.name] = item
        return True
    else:
        return False