import json

import requests
from .itemCache import *

shakshouka = Item("Shakshouka", 24280, "https://www.garlandtools.org/files/icons/item/24280.png")
dsmg = Item("'Darksteel Mitt Gauntlets", 3724, f"https://www.garlandtools.org/files/icons/item/3724.png")

async def garland_fetch_item(item: Item, session):
    url = f"https://www.garlandtools.org/db/doc/item/en/3/{item.id}.json"
    async with session.get(url) as response:
        if response.status != 200:
            raise ConnectionError(f"Request failed with status code {response.status}")
        garland_item = await response.json()
    return garland_item
#print(json.dumps(garland_fetch_item(shakshouka), indent=4))
#(json.dumps(garland_fetch_item(dsmg), indent=4))

def fetch_item_name_by_id(item_id: int):
    url = f"https://www.garlandtools.org/db/doc/item/en/3/{item_id}.json"
    response = requests.get(url)
    garland_item = json.loads(response.text)
    name = garland_item["item"]["name"]
    return name


"""
["node"]["type"] = 2:  tree      
["node"]["type"] = 3: vegetation
["node"]["type"] = 0: mineral
["node"]["type"] = 1: outcropping
["node"]["type"] = 5: spearfishing
["fishingSpots"].len > 0 = fishing
"""

#Apparenlty garlandtools output can have nodes in partials on nongatherables if its ingredients are gatherable so we got to manually check for such situation
def gathering_sanity_check(garland_item: dict) -> bool:
    nodes = []
    if "ingredients" in garland_item:
        for ingredient in garland_item["ingredients"]:
            if "nodes" in ingredient:
                nodes.append(*ingredient["nodes"])

        for partial in garland_item["partials"]:
            if partial["type"] == "node" and int(partial["id"]) in nodes:
                return False

    return True


async def resolve_gathering_data(garland_item: dict) -> GatheringData | bool:
    if "partials" in garland_item:
        node = next((d for d in garland_item["partials"] if d["type"] == "node"), None)
        if node is not None:
            if not gathering_sanity_check(garland_item):
                return False
            elif node["obj"]["t"] == 0 or node["obj"]["t"] == 1:
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
    else :
        return False

async def is_tradeable(garland_item: dict) -> bool:
    if "unlistable" in garland_item["item"]: #may not always be present
        return not bool(garland_item["item"]["unlistable"]) #if unlistable is 1, tradeability is inversed
    return bool(garland_item["item"]["tradeable"])

async def garland_fetch_mob_name(mob_id: str, session) -> str:
    url = f"https://www.garlandtools.org/db/doc/mob/en/2/{mob_id}.json"
    async with session.get(url) as response:
        if response.status != 200:
            raise ConnectionError(f"Request failed with status code {response.status}")
        garland_item = await response.json()
        return garland_item["mob"]["name"]
# print(garland_fetch_mob_name("65950000005692"))




async def resolve_hunting_data(garland_item: dict, session) -> HuntingData | bool:
    if "drops" in garland_item["item"]:
        mobs = list(await asyncio.gather(
            *(garland_fetch_mob_name(id, session) for id in garland_item["item"]["drops"])
        ))
        hunting_data = HuntingData(mobs)
        return hunting_data
    return False
# print(define_hunting_data(garland_fetch_item(Item("Gagana Egg", 19877))))


async def resolve_vendor_listings(garland_item: dict, server, session) -> VendorData | bool:
    from core.xivapi import fetch_full_item_data
    listings = set()

    if "vendors" in garland_item["item"]:
        amount = 1
        currency = await fetch_full_item_data("Gil", server, session)
        cost = garland_item["item"]["price"]
        listings.add(VendorData.VendorListing(currency, cost, amount))

    if "tradeShops" in garland_item["item"]:
        shops = garland_item["item"]["tradeShops"]

        # Collect all listing metadata first
        pending = []
        for shop in shops:
            for listing in shop["listings"]:
                amount = listing["item"][0]["amount"]
                cost = listing["currency"][0]["amount"]
                currency_id = int(listing["currency"][0]["id"])
                pending.append((amount, cost, currency_id))

        # Resolve all currencies concurrently
        async def resolve_currency(currency_id: int, session) -> Item:
            if 20 <= currency_id <= 22:
                return get_cached_item("Grand Company Seal")
            return await fetch_full_item_data(fetch_item_name_by_id(currency_id), server, session)

        currencies = await asyncio.gather(*(resolve_currency(currency_id, session) for _, _, currency_id in pending))

        for (amount, cost, _), currency in zip(pending, currencies):
            listings.add(VendorData.VendorListing(currency, cost, amount))

    if len(listings) > 0:
        return VendorData(listings)
    return False

async def resolve_icon_url(garland_item: dict) -> str:
    return f"https://www.garlandtools.org/files/icons/item/{garland_item["item"]["icon"]}.png"


async def fetch_garland_data(item: Item, server: World, session):
    garland_item = await garland_fetch_item(item, session)

    tasks = [
        resolve_icon_url(garland_item),
        resolve_gathering_data(garland_item),
        resolve_hunting_data(garland_item, session),
        resolve_vendor_listings(garland_item, server, session),
        is_tradeable(garland_item),
    ]

    results: tuple = await asyncio.gather(*tasks)


    return {"icon": results[0],
            "gathering": results[1],
            "hunting": results[2],
            "vendors": results[3],
            "is_tradeable": results[4]}


def apply_garland_data(item: Item, garland_data: dict):
    item.icon_url = garland_data["icon"]
    if garland_data["gathering"]:
        item.gatherable = garland_data["gathering"]
    if garland_data["hunting"]:
        item.huntable = garland_data["hunting"]
    if garland_data["vendors"]:
        item.vendorable = garland_data["vendors"]
    return item

async def fetch_and_apply_garland_data(item: Item, server: World, session):
    apply_garland_data(item, await fetch_garland_data(item, server, session))
    return item