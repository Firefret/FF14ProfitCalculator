from xivapi import *
from garlandTools import *
from itemRequest import *
from wishlist import *
from ordealList import *
import time
import math
from universalis import *
from config import FLAG_PRIORITY, DEFAULT_QUALITY
from materialList import *


async def add_request_to_wishlist(request: ItemRequest, wishlist: Wishlist):
    item = await fetch_top_item_data(request.item_name, request.server)
    amount_of_crafts = math.ceil(request.quantity / item.craftable.item_yield)
    wishlist_entry = WishlistEntry(item, amount_of_crafts)
    wishlist.add(wishlist_entry)


def form_divided_material_list(wishlist: Wishlist) -> MaterialListDivided:
    mat_list_div = MaterialListDivided(MaterialList({}), MaterialList({}), [], wishlist.server)
    mat_list_div.low_mats.parent = mat_list_div
    mat_list_div.mid_mats.parent = mat_list_div

    # Store top-level items for recalculation
    #mat_list_div.top_items = []
    for entry in wishlist.items.values():
        mat_list_div.top_items.append((entry.item, entry.amount))
        mat_list_div.recursive_mat_sweep_and_add(entry.item, entry.amount, FLAG_PRIORITY)
    return mat_list_div

async def mat_list_fetch_and_apply_market_listings(mat_list: MaterialList, dc: DataCenter, session: aiohttp.ClientSession):
    # get a list of all tradeable mats
    item_list = []
    for name, mat in mat_list.items.items():
        garland_data = get_cached_garland_data(name)
        if garland_data is None:
            print(f"No garland_data for {name}")
            continue
        if garland_data["is_tradeable"]:
            item_list.append(mat.item)
        else:
            print(f"{name} does not seem to be tradeable, garlandData view: {garland_data}")
    listings = await get_item_listings(item_list, dc, session)
    for index, item in enumerate(item_list):
        mat = mat_list.items[item.name]
        market_data = MarketData(dc=dc, listings=listings[index])
        mat.item.marketable = market_data


def timed_fetch(item_name: str) -> Item | Craftable | Marketable:
    start = time.perf_counter()
    result = asyncio.run(fetch_top_item_data(item_name, test_server))
    elapsed = time.perf_counter() - start
    print(f"fetch_top_item_data({item_name!r}) took {elapsed:.3f}s")
    return result


async def test_entry_point():

    async with aiohttp.ClientSession() as session:
        all_worlds, all_dcs = await form_game_server_info()
        print(all_worlds)
        world_name = "Raiden"
        world = get_world_by_name(world_name, all_worlds)
        if world is None:
            print(f"Error: Could not find server {world_name}!")
            return
        wishlist = Wishlist({}, world)

        test_requests = [ItemRequest(world, "Grade 2 Gemdraught of Intelligence", 3),
                         ItemRequest(world, "Ra'Kaznar Ingot", 5),
                         ItemRequest(world, "Courtly Lover's Sword", 4)
                         ]

        # 2. You MUST await these or use gather
        tasks = [add_request_to_wishlist(req, wishlist) for req in test_requests]
        await asyncio.gather(*tasks)

        # 3. Now the shopping list will actually have data
        div_mat_list: MaterialListDivided = form_divided_material_list(wishlist)

        # this is a weird place to put market listing fetch in but it's the earliest we get a list of all mats, and universalis api needs a list of item IDs
        # i could do it one-by-one async, but ratelimit is 30req\s and i would really rather not tackle throttling
        await mat_list_fetch_and_apply_market_listings(div_mat_list.low_mats, world.dc, session)
        await mat_list_fetch_and_apply_market_listings(div_mat_list.mid_mats, world.dc, session)


        ordeal_list = OrdealList(div_mat_list)
        #ordeal_list.remove_flag_craft("Ra'Kaznar Ingot")
        print(ordeal_list.mats)
        print(ordeal_list)
        ordeal_list.mats.mid_mats.items["Ra'Kaznar Ingot"].change_ordeal(Ordeal.market)
        print(ordeal_list)
        print(ordeal_list.market.route)
        await ordeal_list.mats.add_item_to_material_list("Courtly Lover's Labrys", 2)
        print(ordeal_list)

        #print(await get_item_listings(div_mat_list.mid_mats.items["Grade 4 Gemsap of Vitality"].item.craftable.ingredients[0], world.dc, session))


#print(timed_fetch("Shakshouka")) #fetch_top_item_data('Shakshouka') took 2.783s
#print(timed_fetch("Darksteel Ingot")) #fetch_top_item_data('Darksteel Mitt Gauntlets') took 2.477s
asyncio.run(test_entry_point())
