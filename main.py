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

        # Gatherability, Vendorability, Huntability, Icon
        item = await fetch_and_apply_garland_data(item, server, session)
        # Marketability
        item.marketable = await fetch_item_market_data(item, server, session)
        cache_item(item)
        return item


async def add_request_to_crafting_list(request: ItemRequest):
    item = await fetch_top_item_data(request.item_name, request.server)
    crafting_list_entry = CraftingListEntry(item, request.quantity)
    crafting_list.add(crafting_list_entry)

def get_material_flags_from_item(item) -> SourceFlags:
    flags = SourceFlags(craftable = True if isinstance(item, Craftable) else False,
                        vendotable = True if isinstance(item, Vendorable) else False,
                        gatherable = True if isinstance(item, Gatherable) else False,
                        huntable = True if isinstance(item, Huntable) else False,
                        marketable = True if isinstance(item, Marketable) else False)

    return flags

def recursive_mat_sweep_and_add(item: Item, amount: int, shopping_list: ShoppingList):
    if isinstance(item, Craftable):
        for index, ingredient in enumerate(item.craftable.ingredients[0]):
            return recursive_mat_sweep(ingredient, amount*item.craftable.ingredients[1][index])
    flags = get_material_flags_from_item(item)
    mat = Material(item, amount, flags)
    shopping_list.add(mat)

def form_shopping_list(crafting_list: CraftingList) -> ShoppingList:
    shopping_list = ShoppingList(dict())
    for entry in crafting_list.items:
        recursive_mat_sweep_and_add(entry.item, entry.amount, shopping_list)
    return shopping_list


def timed_fetch(item_name: str) -> Item | Craftable | Marketable:
    start = time.perf_counter()
    result = asyncio.run(fetch_top_item_data(item_name, test_server))
    elapsed = time.perf_counter() - start
    print(f"fetch_top_item_data({item_name!r}) took {elapsed:.3f}s")
    return result



#print(timed_fetch("Shakshouka")) #fetch_top_item_data('Shakshouka') took 2.783 s
print(timed_fetch("Darksteel Ingot")) #fetch_top_item_data('Darksteel Mitt Gauntlets') took 2.477s
