from itemTypes import *
from xivapi import *
from garlandTools import *



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
    #else:
        #raise TypeError(f"{item_name} is not sellable on the marketboard")

    cache_item(item) #expand upon caching later
    return item

print(fetch_top_item_data("Rarefied Tacos de Carne Asada"))
print(fetch_top_item_data("Egg Foo Young"))
