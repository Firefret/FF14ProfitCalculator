from itemRequest import ItemRequest
from garlandTools import *
from gameServer import *
import aiohttp
import asyncio
from typing import TypeVar

from universalis import fetch_item_market_data

T = TypeVar("T")


game_server = GameServer("Light", "Raiden")
item_request = ItemRequest(game_server, "Darksteel Mitt Gauntlets", 10)

async def fetch_item_base(item_name, session: aiohttp.ClientSession) -> Item:
    request_url = f"https://v2.xivapi.com/api/search?sheets=Item&query=Name%3D%22{item_name}%22"
    async with session.get(request_url) as response:
        if response.status != 200:
            raise ConnectionError(f"Request failed with status code {response.status}")
        item_info = await response.json()
    if not item_info["results"]:
        raise ValueError(f"Could not find item with name {item_name}, please use 'Copy Item Name' in-game")
    item_id = item_info["results"][0]["row_id"]
    item = Item(item_name, item_id)
    return item

async def fetch_is_craftable(item: Item, session: aiohttp.ClientSession) -> bool:
    request_url = f"https://v2.xivapi.com/api/search?sheets=Recipe&query=ItemResult%3D{item.id}"
    async with session.get(request_url) as response:
        if response.status != 200:
            raise ConnectionError(f"Request failed with status code {response.status}")
        recipe_info = await response.json()
    if not recipe_info["results"]:
        return False
    else:
        return True

async def fetch_is_marketable(item: Item, session: aiohttp.ClientSession) -> bool:
    request_url = f"https://v2.xivapi.com/api/sheet/Item/{item.id}"
    async with session.get(request_url) as response:
        if response.status != 200:
            raise ConnectionError(f"Request failed with status code {response.status}")
        item_info = await response.json()
    if "isUntradable" in item_info["fields"]:
        return not item_info["fields"]["IsUntradable"]
    else:
        return False

async def fetch_item_recipe_id(item: Item, session: aiohttp.ClientSession) -> int | bool:
    request_url = f"https://v2.xivapi.com/api/search?sheets=Recipe&query=ItemResult%3D{item.id}"
    async with session.get(request_url) as response:
        if response.status != 200:
            raise ConnectionError(f"Request failed with status code {response.status}")
        recipe_info = await response.json()
    if not recipe_info["results"]:
        return False
    else:
        recipe_id = recipe_info["results"][0]["row_id"]
        print(recipe_id)
        return recipe_id

async def fetch_recipe(recipe_id: int, session: aiohttp.ClientSession) -> tuple[list[Item], list[int], int, Crafter]:
    request_url = f"https://v2.xivapi.com/api/sheet/Recipe/{recipe_id}?fields=Ingredient[].Name,AmountIngredient,AmountResult,CraftType.Name"
    async with session.get(request_url) as response:
        if response.status != 200:
            raise ConnectionError(f"Request failed with status code {response.status}")
        data = await response.json()
    ingredients = list()
    ingredients_json = data["fields"]["Ingredient"]
    for ingredient in ingredients_json:
        if ingredient["value"] <= 0:
            continue
        item_ingredient = Item(ingredient["fields"]["Name"], ingredient["value"])
        ingredients.append(item_ingredient)
    ingredient_amount = [amount for amount in data["fields"]["AmountIngredient"] if amount > 0]
    item_yield = data["fields"]["AmountResult"]
    crafter_string = data["fields"]["CraftType"]["fields"]["Name"]
    print(crafter_string)
    return ingredients, ingredient_amount, item_yield, crafter_string


async def fetch_crafting_data(item: Item, session: aiohttp.ClientSession) -> CraftingData | bool:
    recipe_id = await fetch_item_recipe_id(item, session)
    if not recipe_id:
        return False

    recipe_data = await fetch_recipe(recipe_id, session)
    crafting_data = CraftingData(recipe_id, recipe_data[2], (recipe_data[0], recipe_data[1]), Crafter(recipe_data[3]))
    return crafting_data

async def populate_item_data(item_name: str, server: GameServer, session: aiohttp.ClientSession) -> Item | Craftable:
    item = await fetch_item_base(item_name, session)
    print(f"Retrieving {item.name}. id: {item.id}")

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
    try:
        market_data = await fetch_item_market_data(item, server, session)
        item.marketable = market_data
    except ValueError:
        pass
    cache_item(item)
    return item

async def fetch_full_item_data(item_name: str, server: GameServer, session: aiohttp.ClientSession) -> Item | Craftable:
    # 1. Already fully fetched and cached
    item = get_cached_item(item_name)
    if item:
        return item

    # 2. Already being fetched - subscribe to the task
    if item_name in being_fetched:
        return await being_fetched[item_name]

    # 3. Start a new fetch and register it so others can join it
    task = asyncio.ensure_future(populate_item_data(item_name, server, session))
    being_fetched[item_name] = task
    try:
        return await task
    finally:
        await being_fetched.pop(item_name, None)