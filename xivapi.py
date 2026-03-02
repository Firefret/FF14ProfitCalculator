from gameServer import GameServer
from itemRequest import ItemRequest
from itemTypes import *
import requests


game_server = GameServer("EU", "Light", "Raiden")
item_request = ItemRequest(game_server, "Darksteel Mitt Gauntlets", 10)

def get_item_base(item_name) -> Item:
    request_url = f"https://v2.xivapi.com/api/search?sheets=Item&query=Name%3D%22{item_name}%22"
    response = requests.get(request_url)
    if response.status_code != 200:
        raise ConnectionError(f"Request failed with status code {response.status_code}")
    item_info = response.json()
    if not item_info["results"]:
        raise ValueError(f"Could not find item with name {item_name}, please use 'Copy Item Name' in-game")
    item_id = item_info["results"][0]["row_id"]
    item = Item(item_name, item_id)
    return item

def get_craftability(item: Item) -> bool:
    request_url = f"https://v2.xivapi.com/api/search?sheets=Recipe&query=ItemResult%3D{item.id}"
    response = requests.get(request_url)
    if response.status_code != 200:
        raise ConnectionError(f"Request failed with status code {response.status_code}")
    recipe_info = response.json()
    if not recipe_info["results"]:
        return False
    else:
        return True

def get_item_recipe_id(item: Item) -> int:
    request_url = f"https://v2.xivapi.com/api/search?sheets=Recipe&query=ItemResult%3D{item.id}"
    response = requests.get(request_url)
    if response.status_code != 200:
        raise ConnectionError(f"Request failed with status code {response.status_code}")
    recipe_info = response.json()
    recipe_id = recipe_info["results"][0]["row_id"]
    return recipe_id

def get_recipe_ingredients(recipe_id: int) -> list[Item]:
    request_url = f"https://v2.xivapi.com/api/sheet/Recipe/{recipe_id}?fields=Ingredient[].Name"
    response = requests.get(request_url)
    if response.status_code != 200:
        raise ConnectionError(f"Request failed with status code {response.status_code}")
    ingredients = list()
    ingredients_json = response.json()["fields"]["Ingredient"]
    for ingredient in ingredients_json:
        if ingredient["value"] <= 0:
            continue
        item_ingredient = Item(ingredient["fields"]["Name"], ingredient["value"])
        ingredients.append(item_ingredient)
    return ingredients

def get_full_item_data(item_name: str) -> Item | Craftable: #will be expanded
    item = get_item_base(item_name)
    print(f"Retrieving {item.name}. id: {item.id}")
    if get_craftability(item):
        recipe_id = get_item_recipe_id(item)
        ingredients = get_recipe_ingredients(recipe_id)
        ingredients = [get_full_item_data(ing.name) for ing in ingredients]
        crafting_info = CraftingInfo(recipe_id, ingredients)
        item.craftable = crafting_info # set craftable field
    return item

def get_top_item_info(item_name: str) -> Craftable:
    item = get_item_base(item_name)
    if get_craftability(item):
        item = get_full_item_data(item_name)
    else:
        raise TypeError(f"{item_name} is not a craftable")
    return item

print(get_full_item_data("Fire Shard"))
print(get_full_item_data("Water Shard"))
print(get_full_item_data("Wind Shard"))
print(get_full_item_data("Earth Shard"))
print(get_full_item_data("Ice Shard"))
print(get_full_item_data("Lightning Shard"))

print(get_full_item_data("Fire Crystal"))
print(get_full_item_data("Water Crystal"))
print(get_full_item_data("Wind Crystal"))
print(get_full_item_data("Earth Crystal"))
print(get_full_item_data("Ice Crystal"))
print(get_full_item_data("Lightning Crystal"))

print(get_full_item_data("Fire Cluster"))
print(get_full_item_data("Water Cluster"))
print(get_full_item_data("Wind Cluster"))
print(get_full_item_data("Earth Cluster"))
print(get_full_item_data("Ice Cluster"))
print(get_full_item_data("Lightning Cluster"))
