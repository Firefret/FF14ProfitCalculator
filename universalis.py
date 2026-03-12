import requests
import json
import aiohttp
import asyncio
from itemTypes import *
from gameServer import *
from datetime import datetime, timedelta

#need to get sale data to calculate only the income from selling the top item



#this one will use world name as you can,t sell on other worlds
async def fetch_item_sale_history_month(item: Item, server: GameServer, session: aiohttp.ClientSession):
    month_in_milliseconds = 2592000000
    url = f"https://universalis.app/api/v2/history/{server.world}/{item.id}?statsWithin={month_in_milliseconds}&minSalePrice=0&maxSalePrice=2147483647"
    async with session.get(url) as response:
        if response.status != 200:
            raise ConnectionError(f"Request failed with status code {response.status}")
        sale_info = await response.json()

    if not sale_info["entries"]:
        raise ValueError(f"No sale info for {item.name}")
    return sale_info

def separate_nq_hq_sale_data(entries: dict) -> tuple[list, list]:
    hq_data = []
    nq_data = []
    for sale in entries:
        if sale["hq"]:
            hq_data.append({"quantity": sale["quantity"], "price": sale["pricePerUnit"], "timestamp": sale["timestamp"]})
        else:
            nq_data.append({"quantity": sale["quantity"], "price": sale["pricePerUnit"], "timestamp": sale["timestamp"]})
    return nq_data, hq_data

def calculate_price_dynamics(sale_data) -> float:
    sale_period_start = datetime.fromtimestamp(sale_data[-1]["timestamp"])
    sale_period_end = datetime.fromtimestamp(sale_data[0]["timestamp"])

    sale_period = sale_period_end - sale_period_start

    price_difference = sale_data[0]["price"] - sale_data[-1]["price"]  # 7000 - 5000 = 2000
    gil_dynamics_per_day = price_difference / sale_period.days  # 2000 / 8 = 250
    percent = sale_data[-1]["price"] / 100  # 7000 / 100 = 70
    percent_dynamics_per_day = round(gil_dynamics_per_day / percent, 2)
    return percent_dynamics_per_day

def analyze_sale_info(sale_info: dict):
    entries = sale_info["entries"]
    if len(entries) == 0:
        raise ValueError(f"No sale info for {sale_info['name']}")
    nq_data, hq_data = separate_nq_hq_sale_data(entries)

    nq_market_data, hq_market_data = None, None

    if nq_data:
        nq_dynamics = calculate_price_dynamics(nq_data)
        nq_sale_velocity = sale_info["nqSaleVelocity"]
        nq_last_sale_price = nq_data[0]["price"]
        nq_market_data = SalesData(nq_last_sale_price, nq_dynamics, nq_sale_velocity)

    if hq_data:
        hq_dynamics = calculate_price_dynamics(hq_data)
        hq_sale_velocity = sale_info["hqSaleVelocity"]
        hq_last_sale_price = hq_data[0]["price"]
        hq_market_data = SalesData(hq_last_sale_price, hq_dynamics, hq_sale_velocity)

    return nq_market_data, hq_market_data

async def fetch_item_market_data(item: Item, server: GameServer, session: aiohttp.ClientSession) -> MarketData:
    sale_info = await fetch_item_sale_history_month(item, server, session)
    nq_market_data, hq_market_data, = analyze_sale_info(sale_info)

    return MarketData(True, server, nq_market_data, hq_market_data)




