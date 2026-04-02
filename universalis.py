import requests
import json
import aiohttp
import asyncio

from urllib3.util import url

from itemTypes import *
from gameServer import *
from datetime import datetime, timedelta

#need to get sale data to calculate only the income from selling the top item



#this one will use world name as you can't sell on other worlds
async def fetch_item_sale_history_month(item: Item, server: World, session: aiohttp.ClientSession):
    month_in_milliseconds = 2592000000
    url = f"https://universalis.app/api/v2/history/{server.name}/{item.id}?statsWithin={month_in_milliseconds}&minSalePrice=0&maxSalePrice=2147483647"
    async with session.get(url) as response:
        if response.status != 200:
            raise ValueError(f"No sale data for {item.name}, code {response.status}")
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
    if not sale_data or len(sale_data) < 2:
        return 0.0

    sale_period_start = datetime.fromtimestamp(sale_data[-1]["timestamp"])
    sale_period_end = datetime.fromtimestamp(sale_data[0]["timestamp"])

    sale_period = sale_period_end - sale_period_start

    # total_seconds to avoid 0 days.
    # max() to ensure we never divide by zero even if timestamps are identical

    seconds = max(sale_period.total_seconds(), 1)
    days_float = seconds / 86400
    price_difference = sale_data[0]["price"] - sale_data[-1]["price"]
    gil_dynamics_per_day = price_difference / days_float

    percent = sale_data[-1]["price"] / 100

    # Guard against 0 price items (unlikely but safe)
    if percent == 0: return 0.0

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

async def fetch_item_market_data(item: Item, server: World, session: aiohttp.ClientSession) -> MarketData:
    sale_info = await fetch_item_sale_history_month(item, server, session)
    nq_market_data, hq_market_data, = analyze_sale_info(sale_info)

    return MarketData(server.name, nq_market_data, hq_market_data)

def separate_ids_by_100s(item_id_list:list):
    separated_lists = []
    temp_list = []

    while item_id_list:
        if len(temp_list) == 100:
            separated_lists.append(temp_list)
            temp_list = []

        temp_list.append(item_id_list.pop(0))
    if temp_list:
        separated_lists.append(temp_list)

    return separated_lists

async def get_item_listings(all_item_list: list[Item], dc: DataCenter, session: aiohttp.ClientSession):
    item_ids = list(map(lambda item: item.id, all_item_list))
    item_lists = separate_ids_by_100s(item_ids) # Universalis can accept 100 IDs at once, so we'll do it by 100's
    listings = []
    for item_list in item_lists:
        item_list_copy = item_list.copy()
        id_string = ",".join(map(str, item_list))
        url = f"https://universalis.app/api/v2/{dc.name}/{id_string}?entries=0"
        async with session.get(url) as response:
            if response.status == 400:
                raise ValueError(f"400: The parameters are invalid")
            if response.status == 404:
                raise ValueError(f"404: The world/DC or item requested is invalid.")# When requesting multiple items at once, an invalid item ID will not trigger this.
                                                                                    # Instead, the returned list of unresolved item IDs will contain the invalid item ID or IDs.
            if response.status != 200:
                response.raise_for_status()

            listing_data = await response.json()

            if listing_data["unresolvedItems"]:
                raise ValueError(f"Some items were unresolved: {listing_data['unresolvedItems']}")

            for item_id, listing_data in listing_data["items"].items():
                item_index = item_list_copy.index(int(item_id)) # get the index of the item we are inspecting the listings of, because the response item order is random
                listings = listing_data["listings"]
                hq = []
                nq = []

                for listing in listings:
                    world = get_world_by_name(listing["worldName"], dc.worlds)
                    retainer_name = listing["retainerName"]
                    quantity = listing["quantity"]
                    price = listing["total"]
                    market_listing = MarketListing(world, retainer_name, quantity, price)
                    if listing["hq"]:
                        hq.append(market_listing)
                    else:
                        nq.append(market_listing)

                item_list_copy[item_index] = ListingData(hq, nq)

        listings = [*listings, *item_list_copy]

    return listings











