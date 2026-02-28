from gameServer import GameServer
from itemRequest import ItemRequest
from itemTypes import *
import requests
from typing import Any, Protocol, TypeGuard
import json

from itemTypes import CraftableItem, Item

game_server = GameServer("EU", "Light", "Raiden")
item_request = ItemRequest(game_server, "Darksteel Mitt Gauntlets", 10)

def get_item_base(item_name) -> ItemBase:
    request_url = f"https://v2.xivapi.com/api/search?sheets=Item&query=Name%3D%22{item_name}%22"
    response = requests.get(request_url)
    if response.status_code != 200:
        raise ConnectionError(f"Request failed with status code {response.status_code}")
    item_info = response.json()
    if not item_info["results"]:
        raise ValueError(f"Could not find item with name {item_name}, please use 'Copy Item Name' in-game")
    item_id = item_info["results"][0]["row_id"]
    item_base = ItemBase(item_name, item_id)
    return item_base

def is_craftable(item: Item) -> bool:
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
        print(f"Found ingredient {ingredient}")
        item_ingredient = ItemBase(ingredient["fields"]["Name"], ingredient["value"])
        ingredients.append(item_ingredient)
    return ingredients

def get_full_item_info(item: Item) -> CraftableItem | Item:
    if is_craftable(item):
        print(f"Craftable item {item.name} found")
        recipe_id = get_item_recipe_id(item)
        print(f"{item.name} recipe ID: {recipe_id}")
        ingredients = get_recipe_ingredients(recipe_id)
        print("DUCK")
        ingredients = [get_full_item_info(ing) for ing in ingredients]
        craft_info = CraftInfo(recipe_id, ingredients)
        craftable_item = CraftableItem(item, craft_info)
        return craftable_item
    else:
        print(f"Non-craftable item {item.name} found")
        return item

def get_top_item_info(name: str) -> CraftableItem:
    item_base = get_item_base(name)
    if not is_craftable(item_base):
        raise ValueError(f"{name} is not craftable")

    item = get_full_item_info(item_base)
    return item

print(get_top_item_info("Darksteel Mitt Gauntlets"))


