from shoppingList import ShoppingList
from xivapi import *
from garlandTools import *
from itemRequest import *
from craftingList import *
from shoppingList import *
import aiohttp
import asyncio
import time
from universalis import *

test_server = GameServer("Light", "Raiden")
test_request = ItemRequest("Raiden", "Darksteel Mitt Gauntlets", 3)
crafting_list = CraftingList()

async def fetch_top_item_data(item_name: str, server: GameServer) -> Item | Craftable | Marketable:
    async with aiohttp.ClientSession() as session:
        item = await fetch_item_base(item_name, session)

        # Craftability
        crafting_data = await fetch_crafting_data(item, session)
        if crafting_data:
            ingredients = await asyncio.gather(
                *(fetch_full_item_data(ing.name, server, session) for ing in crafting_data.ingredients[0])
            )
            crafting_data.ingredients = (list(ingredients), crafting_data.ingredients[1])
            item.craftable = crafting_data

        # Sources
        item = await fetch_and_apply_garland_data(item, server, session)
        item.marketable = await fetch_item_market_data(item, server, session)
        cache_item(item)
        return item


async def add_request_to_crafting_list(request: ItemRequest):
    item = await fetch_top_item_data(request.item_name, request.server)
    crafting_list_entry = CraftingListEntry(item, request.quantity)
    crafting_list.add(crafting_list_entry)

def recursive_mat_sweep(item: Item):
    if item is Craftable:
        for ingredient in item.craftable.ingredients[0]:
            recursive_mat_sweep(ingredient)
    else:
        return item

def form_shopping_list(crafting_list: CraftingList) -> ShoppingList:
    for entry in crafting_list.items:



def timed_fetch(item_name: str) -> Item | Craftable | Marketable:
    start = time.perf_counter()
    result = asyncio.run(fetch_top_item_data(item_name, test_server))
    elapsed = time.perf_counter() - start
    print(f"fetch_top_item_data({item_name!r}) took {elapsed:.3f}s")
    return result



#print(timed_fetch("Shakshouka")) #fetch_top_item_data('Shakshouka') took 2.783 s
print(timed_fetch("Darksteel Ingot")) #fetch_top_item_data('Darksteel Mitt Gauntlets') took 2.477s
