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

print(garland_fetch_item(shakshouka))

