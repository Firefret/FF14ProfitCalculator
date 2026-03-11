from xivapi import *
from garlandTools import *
import aiohttp
import asyncio


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

print(asyncio.run(fetch_top_item_data("Rarefied Tacos de Carne Asada")))
print(asyncio.run(fetch_top_item_data("Egg Foo Young")))
print(asyncio.run(fetch_top_item_data("Darksteel Mitt Gauntlets")))
