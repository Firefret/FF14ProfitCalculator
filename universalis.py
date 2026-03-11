import requests
import json
import aiohttp
import asyncio
from itemTypes import *
from gameServer import *

async def fetch_item_sale_history_month_world(item: Item, server: GameServer, session: aiohttp.ClientSession):
    month_in_milliseconds = 2592000000
    url = f"https://universalis.app/api/v2/history/{server.world}/{item.id}?statsWithin={month_in_milliseconds}&minSalePrice=0&maxSalePrice=2147483647"
    async with session.get(url) as response:
        if response.status != 200:
            raise ConnectionError(f"Request failed with status code {response.status}")
        sale_info = await response.json()

    if sale_info is None:
        raise ValueError(f"No sale info for {item.name}")

    return sale_info

