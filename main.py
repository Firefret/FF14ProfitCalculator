from xivapi import *
from garlandTools import *
import aiohttp
import asyncio
import time

async def fetch_top_item_data(item_name: str) -> Item | Craftable | Marketable:
    async with aiohttp.ClientSession() as session:
        item = await fetch_item_base(item_name, session)

        crafting_data = await fetch_crafting_data(item, session)
        if crafting_data:
            ingredients = await asyncio.gather(
                *(fetch_full_item_data(ing.name, session) for ing in crafting_data.ingredients[0])
            )
            crafting_data.ingredients = (list(ingredients), crafting_data.ingredients[1])
            item.craftable = crafting_data
        else:
            raise TypeError(f"{item_name} is not a craftable")

        if await fetch_is_marketable(item, session):
            marketable = MarketData(True)
            item.marketable = marketable

        cache_item(item)
        return item

def timed_fetch(item_name: str) -> Item | Craftable | Marketable:
    start = time.perf_counter()
    result = asyncio.run(fetch_top_item_data(item_name))
    elapsed = time.perf_counter() - start
    print(f"fetch_top_item_data({item_name!r}) took {elapsed:.3f}s")
    return result

print(timed_fetch("Shakshouka")) #fetch_top_item_data('Shakshouka') took 2.783s
print(timed_fetch("Darksteel Mitt Gauntlets")) #fetch_top_item_data('Darksteel Mitt Gauntlets') took 2.477s
