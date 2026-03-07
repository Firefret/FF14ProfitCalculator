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

def garland_fetch_mob_name(mob_id:str):
    url = f"https://www.garlandtools.org/db/doc/mob/en/2/{mob_id}.json"
    response = requests.get(url)
    response.raise_for_status()
    garland_item = json.loads(response.text)
    return garland_item["mob"]["name"]

#print(garland_fetch_mob_name("65950000005692"))

def garland_fetch_gathering_type(node_id: int):
    url = f"https://www.garlandtools.org/db/doc/node/en/2/{node_id}.json"
    response = requests.get(url)
    response.raise_for_status()
    garland_item = json.loads(response.text)
    #match garland_item[]:
