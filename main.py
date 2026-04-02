from materialList import MaterialList
from xivapi import *
from garlandTools import *
from itemRequest import *
from wishlist import *
from materialList import *
from ordealList import *
import aiohttp
import asyncio
import time
import gameServer as server
import math
from universalis import *

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


async def add_request_to_wishlist(request: ItemRequest, wishlist: Wishlist):
    item = await fetch_top_item_data(request.item_name, request.server)
    amount_of_crafts = math.ceil(request.quantity / item.craftable.item_yield)
    wishlist_entry = WishlistEntry(item, amount_of_crafts)
    wishlist.add(wishlist_entry)

def get_material_flags_from_item(item) -> SourceFlags:
    flags = SourceFlags(is_craftable = True if item.craftable else False,
                        is_vendorable = True if item.vendorable else False,
                        is_gatherable = True if item.gatherable else False,
                        is_huntable = True if item.huntable else False,
                        is_marketable = True if item.marketable else False)

    return flags


def recursive_mat_sweep_and_add(item: Item, amount: int, mat_list_div: MaterialListDivided, flag_priority=None, depth = None):
    if flag_priority is None:
        flag_priority = [Ordeal.craft, Ordeal.market, Ordeal.gather, Ordeal.hunt, Ordeal.vendor]

    if depth is None:
        depth = 0

    # 1. Handle Mid Mats (Those that CAN be crafted)
    if item.craftable:
        if depth > 0: #Don't need topmost items, those are the ones you gonna craft
            # Create and add the current item to mid_mats
            flags = get_material_flags_from_item(item)
            mat = Material(item, amount, flags)
            mat.set_default_flag(flag_priority)
            mat_list_div.mid_mats.add(mat)

        # 2. Now calculate how many crafts we need to satisfy the amount
        craft_yield = item.craftable.item_yield
        amount_of_crafts = math.ceil(amount / craft_yield)

        # 3. Dig into ingredients
        for index, ingredient in enumerate(item.craftable.ingredients[0]):
            ing_per_craft = item.craftable.ingredients[1][index]
            # Total ingredients needed = (crafts needed) * (items per craft)
            total_ing_needed = amount_of_crafts * ing_per_craft

            recursive_mat_sweep_and_add(ingredient, total_ing_needed, mat_list_div, flag_priority, depth+1)

    else:
        flags = get_material_flags_from_item(item)
        mat = Material(item, amount, flags)
        mat.set_default_flag(flag_priority)
        mat_list_div.low_mats.add(mat)

def form_divided_material_list(wishlist: Wishlist) -> MaterialListDivided:
    mat_list_div = MaterialListDivided(MaterialList({}), MaterialList({}))
    for entry in wishlist.items.values():
        recursive_mat_sweep_and_add(entry.item, entry.amount, mat_list_div)

    return mat_list_div


def timed_fetch(item_name: str) -> Item | Craftable | Marketable:
    start = time.perf_counter()
    result = asyncio.run(fetch_top_item_data(item_name, test_server))
    elapsed = time.perf_counter() - start
    print(f"fetch_top_item_data({item_name!r}) took {elapsed:.3f}s")
    return result


# main.py

async def test_entry_point():
    wishlist = Wishlist({})
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
        tasks = [add_request_to_wishlist(req, wishlist) for req in test_requests]
        await asyncio.gather(*tasks)

        # 3. Now the shopping list will actually have data
        div_mat_list = form_divided_material_list(wishlist)
        ordeal_list = OrdealList(div_mat_list)
        print(div_mat_list)
        print(ordeal_list)
        print(await get_item_listings(div_mat_list.mid_mats.items["Grade 4 Gemsap of Vitality"].item.craftable.ingredients[0], world.dc, session))




#todo: marketable materials amount universalis scan for cheapest and server travel route
#todo: material flag toggles, dependent on which the cost and needed mats will be recalculated


#print(timed_fetch("Shakshouka")) #fetch_top_item_data('Shakshouka') took 2.783s
#print(timed_fetch("Darksteel Ingot")) #fetch_top_item_data('Darksteel Mitt Gauntlets') took 2.477s
asyncio.run(test_entry_point())
