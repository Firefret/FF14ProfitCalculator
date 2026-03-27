from shoppingList import ShoppingList
from xivapi import *
from garlandTools import *
from itemRequest import *
from craftingList import *
from shoppingList import *
import aiohttp
import asyncio
import time
import gameServer as server
from universalis import *

crafting_list = CraftingList({})

async def fetch_top_item_data(item_name: str, server: World) -> Item | Craftable | Marketable:
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
    flags = SourceFlags(is_craftable = True if item.craftable else False,
                        is_vendorable = True if item.vendorable else False,
                        is_gatherable = True if item.marketable else False,
                        is_huntable = True if item.huntable else False,
                        is_marketable = True if item.marketable else False)

    return flags

def recursive_mat_sweep_and_add(item: Item, amount: int, shopping_list: ShoppingList):
    # If it's a craftable, we want the raw materials
    if item.craftable:
        for index, ingredient in enumerate(item.craftable.ingredients[0]):
            # ingredient must be an Item object!
            ing_amount = item.craftable.ingredients[1][index]
            recursive_mat_sweep_and_add(ingredient, amount * ing_amount, shopping_list)
    else:
        # If it's not craftable, it's a base material for the shopping list
        flags = get_material_flags_from_item(item)
        mat = Material(item, amount, flags)
        shopping_list.add(mat)

def form_shopping_list(crafting_list: CraftingList) -> ShoppingList:
    shopping_list = ShoppingList(dict())
    for entry in crafting_list.items.values():
        recursive_mat_sweep_and_add(entry.item, entry.amount, shopping_list)
    return shopping_list


def timed_fetch(item_name: str) -> Item | Craftable | Marketable:
    start = time.perf_counter()
    result = asyncio.run(fetch_top_item_data(item_name, test_server))
    elapsed = time.perf_counter() - start
    print(f"fetch_top_item_data({item_name!r}) took {elapsed:.3f}s")
    return result


# main.py

async def test_entry_point():
    async with aiohttp.ClientSession() as session:
        all_worlds, all_dcs = await form_game_server_info()

        print(all_worlds)
        world_name = "Raiden"
        world = get_world_by_name(world_name, all_worlds)
        if world is None:
            print(f"Error: Could not find server {world_name}!")
            return

        test_requests = [ItemRequest(world, "Grade 2 Gemdraught of Intelligence", 3),
                         ItemRequest(world, "Ra'Kaznar Ingot", 5),
                         ItemRequest(world, "Courtly Lover's Sword", 4)
                         ]

        # 2. You MUST await these or use gather
        tasks = [add_request_to_crafting_list(req) for req in test_requests]
        await asyncio.gather(*tasks)

    # 3. Now the shopping list will actually have data
    shopping_list = form_shopping_list(crafting_list)
    print(shopping_list)



#print(timed_fetch("Shakshouka")) #fetch_top_item_data('Shakshouka') took 2.783s
#print(timed_fetch("Darksteel Ingot")) #fetch_top_item_data('Darksteel Mitt Gauntlets') took 2.477s
asyncio.run(test_entry_point())