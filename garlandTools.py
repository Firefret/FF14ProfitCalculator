import requests
import json
from itemTypes import *

shakshouka = Item("Shakshouka", 24280)
dsmg = Item("'Darksteel Mitt Gauntlets", 3724)

def garland_fetch_item(item: Item):
    url = f"https://www.garlandtools.org/db/doc/item/en/3/{item.id}.json"
    response = requests.get(url)
    response.raise_for_status()
    garland_item = json.loads(response.text)
    return garland_item

#print(json.dumps(garland_fetch_item(shakshouka), indent=4))
#(json.dumps(garland_fetch_item(dsmg), indent=4))

"""
["node"]["type"] = 2:  tree      
["node"]["type"] = 3: vegetation
["node"]["type"] = 0: mineral
["node"]["type"] = 1: outcropping
["node"]["type"] = 5: spearfishing
["fishingSpots"].len > 0 = fishing
"""
def define_gathering_data(garland_item: dict) -> GatheringData | bool:
    node = next((d for d in garland_item["partials"] if d["type"] == "node"), None)
    if node is not None:
        if node["obj"]["t"] == 0 or node["obj"]["t"] == 1:
            return GatheringData(Gatherer.MIN)
        elif node["obj"]["t"] == 2 or node["obj"]["t"] == 3:
            return GatheringData(Gatherer.BTN)
        elif node["obj"]["t"] == 5:
            return GatheringData(Gatherer.FSH)
        else:
            return False
    elif "fishingSpots" in garland_item["item"]:
        return GatheringData(Gatherer.FSH)
    else:
        return False

def define_hunting_data(garland_item: dict) -> HuntingData | bool:
    if "drops" in garland_item["item"]:
        mobs = list(map(garland_fetch_mob_name, garland_item["item"]["drops"]))
        hunting_data = HuntingData(mobs)
        return hunting_data
    return False

def garland_fetch_mob_name(mob_id: str) -> str:
    url = f"https://www.garlandtools.org/db/doc/mob/en/2/{mob_id}.json"
    response = requests.get(url)
    response.raise_for_status()
    garland_item = json.loads(response.text)
    return garland_item["mob"]["name"]


# print(garland_fetch_mob_name("65950000005692"))


def fetch_item_sources(item: Item):
    garland_item = garland_fetch_item(item)

    #Gathering
    gathering_type = define_gathering_data(garland_item)
    if gathering_type:
        item.gatherable = gathering_type

    #Hunting
    hunting_data = define_hunting_data(garland_item)
    if hunting_data:
        item.hunting = hunting_data

    #Vendoring
