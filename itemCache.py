from itemTypes import *

item_cache = {
    "Fire Shard" : Item("Fire Shard", 2),
    "Ice Shard" : Item("Ice Shard", 3),
    "Wind Shard": Item("Wind Shard", 4),
    "Earth Shard" : Item("Earth Shard", 5),
    "Lightning Shard" : Item("Lightning Shard", 6),
    "Water Shard" : Item("Water Shard", 7),
    "Fire Crystal" : Item("Fire Crystal", 8),
    "Ice Crystal" : Item("Ice Crystal", 9),
    "Wind Crystal" : Item("Wind Crystal", 10),
    "Earth Crystal" : Item("Earth Crystal", 11),
    "Lightning Crystal" : Item("Lightning Crystal", 12),
    "Water Crystal" : Item("Water Crystal", 13),
    "Fire Cluster" : Item("Fire Cluster", 14),
    "Ice Cluster" : Item("Ice Cluster", 15),
    "Wind Cluster" : Item("Wind Cluster", 16),
    "Earth Cluster" : Item("Earth Cluster", 17),
    "Lightning Cluster" : Item("Lightning Cluster", 18),
    "Water Cluster" : Item("Water Cluster", 19),
}


def get_cached_item(name: str) -> Item | bool:
    if name in item_cache:
        return item_cache[name]
    else:
        return False

def cache_item(item: Item) -> bool:
    if item.name not in item_cache:
        item_cache[item.name] = Item
        return True
    else:
        return False