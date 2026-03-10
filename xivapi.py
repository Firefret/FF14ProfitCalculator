from gameServer import GameServer
from itemRequest import ItemRequest
from itemCache import *
from itemTypes import *
import requests
import time
from typing import Callable, TypeVar, Tuple, Any


T = TypeVar("T")


game_server = GameServer("EU", "Light", "Raiden")
item_request = ItemRequest(game_server, "Darksteel Mitt Gauntlets", 10)

def _time_call(fn: Callable[..., T], /, *args: Any, **kwargs: Any) -> Tuple[T, float]:
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed_s = time.perf_counter() - start
    return result, elapsed_s

def print_timed_call(label: str, fn: Callable[..., T], /, *args: Any, **kwargs: Any) -> T:
    result, elapsed_s = _time_call(fn, *args, **kwargs)
    print(f"{label} took {elapsed_s:.6f} seconds")
    return result

def fetch_item_base(item_name) -> Item:
    request_url = f"https://v2.xivapi.com/api/search?sheets=Item&query=Name%3D%22{item_name}%22"
    response = requests.get(request_url)
    if response.status_code != 200:
        raise ConnectionError(f"Request failed with status code {response.status_code}")
    item_info = response.json()
    if not item_info["results"]:
        raise ValueError(f"Could not find item with name {item_name}, please use 'Copy Item Name' in-game")
    item_id = item_info["results"][0]["row_id"]
    icon_url = f"https://www.garlandtools.org/files/icons/item/{item_id}.png"
    item = Item(item_name, item_id, icon_url)
    return item

def fetch_is_craftable(item: Item) -> bool:
    request_url = f"https://v2.xivapi.com/api/search?sheets=Recipe&query=ItemResult%3D{item.id}"
    response = requests.get(request_url)
    if response.status_code != 200:
        raise ConnectionError(f"Request failed with status code {response.status_code}")
    recipe_info = response.json()
    if not recipe_info["results"]:
        return False
    else:
        return True

def fetch_is_marketable(item: Item) -> bool:
    request_url = f"https://v2.xivapi.com/api/sheet/Item/{item.id}"
    response = requests.get(request_url)
    if response.status_code != 200:
        raise ConnectionError(f"Request failed with status code {response.status_code}")
    item_info = response.json()
    return not item_info["fields"]["IsUntradable"]

def fetch_item_recipe_id(item: Item) -> int | bool:
    request_url = f"https://v2.xivapi.com/api/search?sheets=Recipe&query=ItemResult%3D{item.id}"
    response = requests.get(request_url)
    if response.status_code != 200:
        raise ConnectionError(f"Request failed with status code {response.status_code}")
    recipe_info = response.json()
    if not recipe_info["results"]:
        return False
    else:
        recipe_id = recipe_info["results"][0]["row_id"]
        print(recipe_id)
        return recipe_id

def fetch_recipe(recipe_id: int) -> tuple[list[Item], list[int], int, Crafter]:
    request_url = f"https://v2.xivapi.com/api/sheet/Recipe/{recipe_id}?fields=Ingredient[].Name,AmountIngredient,AmountResult,CraftType.Name"
    response = requests.get(request_url)
    if response.status_code != 200:
        raise ConnectionError(f"Request failed with status code {response.status_code}")
    ingredients = list()
    ingredients_json = response.json()["fields"]["Ingredient"]
    for ingredient in ingredients_json:
        if ingredient["value"] <= 0:
            continue
        item_ingredient = Item(ingredient["fields"]["Name"], ingredient["value"], f"https://www.garlandtools.org/files/icons/item/{ingredient["value"]}.png")
        ingredients.append(item_ingredient)
    ingredient_amount = [amount for amount in response.json()["fields"]["AmountIngredient"] if amount > 0]
    item_yield = response.json()["fields"]["AmountResult"]
    crafter_string = response.json()["fields"]["CraftType"]["fields"]["Name"]
    print(crafter_string)
    return ingredients, ingredient_amount, item_yield, crafter_string


def fetch_crafting_data(item: Item) -> CraftingData | bool:
    recipe_id = fetch_item_recipe_id(item)
    if not recipe_id:
        return False

    recipe_data = fetch_recipe(recipe_id)
    crafting_data = CraftingData(recipe_id, recipe_data[2], (recipe_data[0], recipe_data[1]), Crafter(recipe_data[3]))
    return crafting_data

def fetch_full_item_data(item_name: str) -> Item | Craftable: #will be expanded
    item = get_cached_item(item_name)
    if item:
        return item

    item = fetch_item_base(item_name)
    print(f"Retrieving {item.name}. id: {item.id}")

    # Craftability
    crafting_data = fetch_crafting_data(item)
    if crafting_data:
        ingredients = [fetch_full_item_data(ing.name) for ing in crafting_data.ingredients[0]]
        crafting_data.ingredients = (ingredients, crafting_data.ingredients[1])
        item.craftable = crafting_data

    # Marketability
    if fetch_is_marketable(item):
        marketable = MarketData(True)
        item.marketable = marketable

    cache_item(item)
    return item

def fetch_top_item_data(item_name: str) -> Item | Craftable | Marketable:
    item = fetch_item_base(item_name)

    crafting_data = fetch_crafting_data(item)
    if crafting_data:
        ingredients = [fetch_full_item_data(ing.name) for ing in crafting_data.ingredients[0]]
        crafting_data.ingredients = (ingredients, crafting_data.ingredients[1])
        item.craftable = crafting_data
    else:
        raise TypeError(f"{item_name} is not a craftable")

    if fetch_is_marketable(item):
        marketable = MarketData(True)
        item.marketable = marketable
    else:
        raise TypeError(f"{item_name} is not sellable on the marketboard")

    cache_item(item) #expand upon caching later
    return item


# No cache: fetch_top_item_data("Darksteel Mitt Gauntlets") took 8.321257 seconds (some repeated nested recipes)
# No cache: fetch_top_item_data("Shakshouka") took 3.873055 seconds (no nested recipes)
# With cache: fetch_top_item_data("Darksteel Mitt Gauntlets") took 3.760396 seconds (some repeated nested recipes)
# With cache: fetch_top_item_data("Shakshouka") took 2.946904 seconds (no nested recipes)
# With call optimization: fetch_top_item_data("Darksteel Mitt Gauntlets") took 3.360651 seconds
# With call optimization: fetch_top_item_data("Shakshouka") took 2.752322 seconds

#print(fetch_top_item_data("Darksteel Mitt Gauntlets"))
#print(fetch_is_marketable(fetch_full_item_data("Shakshouka")))
#print(fetch_is_marketable(fetch_full_item_data("Breach Coin")))
#print(fetch_full_item_data("Gagana Egg"))