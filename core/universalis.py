from datetime import datetime

import aiohttp

from .gameServer import get_world_by_name
from .itemTypes import *
from pathlib import Path
import json

#need to get sale data to calculate only the income from selling the top item

def save_raw_response_log(data: dict, filename: str = "universalis_response_debug.json"):
    """
    Safely saves the API response to a file in a local 'logs' directory.
    Handles folder creation automatically.
    """
    try:
        # Create a 'logs' directory relative to the current working directory if it doesn't exist
        log_dir = Path.cwd() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        file_path = log_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[DEBUG LOG] Successfully saved raw response to: {file_path}")
    except Exception as e:
        print(f"[DEBUG LOG ERROR] Failed to save log file: {e}")

#this one will use world name as you can't sell on other worlds
async def fetch_item_sale_history_month(item: Item, server: World, session: aiohttp.ClientSession):
    month_in_milliseconds = 2592000000
    url = f"https://universalis.app/api/v2/history/{server.name}/{item.id}?entriesWithin={month_in_milliseconds}&minSalePrice=0&maxSalePrice=2147483647"
    async with session.get(url) as response:
        if response.status != 200:
            raise ValueError(f"The world/DC ({server.name}) or item ({item.name}) requested is invalid. ")
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

def resolve_cheapest(data: dict) -> int:
    cheapest = 0
    if "minListing" in data:
        listing = data["minListing"]
        if "world" in listing:
            cheapest = listing["world"]["price"]
        elif "dc" in listing:
            cheapest = listing["dc"]["price"]
        elif "region" in listing:
            cheapest = listing["region"]["price"]
    elif "recentPurchase" in data:
        listing = data["minListing"]
        if "world" in listing:
            cheapest = listing["world"]["price"]
        elif "dc" in listing:
            cheapest = listing["dc"]["price"]
        elif "region" in listing:
            cheapest = listing["region"]["price"]
    elif "averageSalePrice" in data:
        listing = data["minListing"]
        if "world" in listing:
            cheapest = int(listing["world"]["price"])
        elif "dc" in listing:
            cheapest = int(listing["dc"]["price"])
        elif "region" in listing:
            cheapest = int(listing["region"]["price"])
    else:
        pass
    return cheapest

async def fetch_current_cheapest(item: Item, server: World, session: aiohttp.ClientSession) -> tuple[int, int]:
    url = f"https://universalis.app/api/v2/aggregated/{server.name}/{item.id}"
    async with session.get(url) as response:
        if response.status == 400:
            raise ValueError("The parameters were invalid.")
        if response.status == 404:
            raise ValueError(f"The world/DC or item requested is invalid (World: {server}, Item: {Item}. When requesting multiple items at once, an invalid item ID will not trigger this. Instead, the returned list of unresolved item IDs will contain the invalid item ID or IDs. Request URL: {url}")
        response.raise_for_status()
        data = await response.json()
        #World > Region > DC lookup
        nq_cheapest = 0
        hq_cheapest = 0
        if data["results"][0]["nq"]:
            nq_cheapest = resolve_cheapest(data["results"][0]["nq"])
        if data["results"][0]["hq"]:
            hq_cheapest = resolve_cheapest(data["results"][0]["hq"])

        return nq_cheapest, hq_cheapest


def analyze_sale_info(sale_info: dict, cheapest: tuple[int, int]) -> tuple[ItemSales | None, ItemSales | None]:
    entries = sale_info["entries"]
    if len(entries) == 0:
        raise ValueError(f"No sale info for {sale_info['name']}")
    nq_data, hq_data = separate_nq_hq_sale_data(entries)

    nq_market_data, hq_market_data = None, None

    if nq_data:
        nq_dynamics = calculate_price_dynamics(nq_data)
        nq_sale_velocity = sale_info["nqSaleVelocity"]
        nq_market_data = ItemSales(cheapest[0], nq_dynamics, int(nq_sale_velocity))

    if hq_data:
        hq_dynamics = calculate_price_dynamics(hq_data)
        hq_sale_velocity = sale_info["hqSaleVelocity"]
        hq_market_data = ItemSales(cheapest[1], hq_dynamics, int(hq_sale_velocity))

    return nq_market_data, hq_market_data

async def fetch_item_sale_data(item: Item, server: World, session: aiohttp.ClientSession) -> MarketData:
    sale_info = await fetch_item_sale_history_month(item, server, session)
    print(f"fetched {item.name} sale history")
    cheapest = await fetch_current_cheapest(item, server, session)
    nq_market_data, hq_market_data, = analyze_sale_info(sale_info, cheapest)
    sales_data = SalesData(hq_market_data, nq_market_data)
    return MarketData(server.dc, sales_data)

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


async def get_item_listings(all_item_list: list['Item'], dc: 'DataCenter', session: aiohttp.ClientSession) -> list[
    'ListingData']:
    item_ids = list(map(lambda item: item.id, all_item_list))
    item_lists = separate_ids_by_100s(item_ids)
    final_result = []

    for item_list in item_lists:
        item_list_copy = item_list.copy()
        id_string = ",".join(map(str, item_list))
        print(f"id_string = {id_string}")

        url = f"https://universalis.app/api/v2/{dc.name}/{id_string}?entries=0"
        async with session.get(url) as response:
            if response.status == 400:
                raise ValueError(f"400: The parameters are invalid")
            if response.status == 404:
                raise ValueError(f"404: The world/DC or item requested is invalid.")
            if response.status != 200:
                response.raise_for_status()

            raw_json = await response.json()

            # --- SAFEGUARD: LOGGING RAW DATA ---
            save_raw_response_log(raw_json)
            # -----------------------------------

            # --- DETECT AND NORMALIZE SINGLE ITEM VS MULTI-ITEM ---
            if "items" in raw_json:
                # Scenario A: Multi-item response
                items_dict = raw_json["items"]

                # Check for unresolved items only if the field exists
                if "unresolvedItems" in raw_json and len(raw_json["unresolvedItems"]) > 0:
                    unresolved = raw_json["unresolvedItems"]
                    raise ValueError(f"Some items were unresolved: {unresolved}")
            else:
                # Scenario B: Single-item response (Flattened layout)
                # We extract the itemID from the root, stringify it to match JSON key standards,
                # and wrap the raw_json payload to mirror the multi-item structure.
                single_item_id = str(raw_json.get("itemID", item_list[0]))
                items_dict = {single_item_id: raw_json}
            # -----------------------------------------------------

            # Now this loop runs perfectly uniform whether you requested 1 item or 100
            for item_id, item_data in items_dict.items():
                item_index = item_list_copy.index(int(item_id))
                listings = item_data.get("listings", [])
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

                # Create arrays for marketboard ordeal routes
                hq_amount = sum(listing.quantity for listing in item_list_copy[item_index].hq)
                nq_amount = sum(listing.quantity for listing in item_list_copy[item_index].nq)

                item_list_copy[item_index].nq_routes = [None] * nq_amount
                item_list_copy[item_index].hq_routes = [None] * hq_amount

        final_result = [*final_result, *item_list_copy]

    return final_result










