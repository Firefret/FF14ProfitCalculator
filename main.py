import core
import schemas
import asyncio
import aiohttp
from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI, HTTPException

async def test_entry_point():

    async with aiohttp.ClientSession() as session:
        all_worlds, all_dcs = await core.gameServer.form_game_server_info()
        print(all_worlds)
        world_name = "Raiden"
        world = core.gameServer.get_world_by_name(world_name, all_worlds)
        if world is None:
            print(f"Error: Could not find server {world_name}!")
            return
        wishlist = core.wishlist.Wishlist({}, world)

        test_requests = [ItemRequest(world, "Grade 2 Gemdraught of Intelligence", 3),
                         ItemRequest(world, "Ra'Kaznar Ingot", 5),
                         ItemRequest(world, "Courtly Lover's Sword", 4)
                         ]

        # 2. You MUST await these or use gather
        tasks = [wishlist.process_request(req) for req in test_requests]
        await asyncio.gather(*tasks)

        # 3. Now the shopping list will actually have data
        new_endeavor: Endeavor = core.endeavor.Endeavor(wishlist)

        # this is a weird place to put market listing fetch in but it's the earliest we get a list of all mats, and universalis api needs a list of item IDs
        # i could do it one-by-one async, but ratelimit is 30req\s and i would really rather not tackle throttling
        await new_endeavor.low_mats.fetch_and_apply_market_listings(world.dc, session)
        await new_endeavor.mid_mats.fetch_and_apply_market_listings(world.dc, session)


        ordeal_list = core.ordealList.OrdealList(new_endeavor)
        #ordeal_list.remove_flag_craft("Ra'Kaznar Ingot")
        print(ordeal_list.mats)
        print(ordeal_list)
        ordeal_list.mats.mid_mats.items["Ra'Kaznar Ingot"].change_ordeal(core.Ordeal.market)
        print(ordeal_list)
        print(ordeal_list.market.route)
        await ordeal_list.mats.add_items_to_material_list([("Courtly Lover's Labrys", 2)], session, world.dc)
        print(ordeal_list)
        ordeal_list.mats.update_top_item(ordeal_list.mats.wishlist.entries["Courtly Lover's Sword"].item, 2)
        print(ordeal_list)

        #print(await get_item_listings(div_mat_list.mid_mats.items["Grade 4 Gemsap of Vitality"].item.craftable.ingredients[0], world.dc, session))


#print(timed_fetch("Shakshouka")) #fetch_top_item_data('Shakshouka') took 2.783s
#print(timed_fetch("Darksteel Ingot")) #fetch_top_item_data('Darksteel Mitt Gauntlets') took 2.477s
#asyncio.run(test_entry_point())


app = FastAPI()


def custom_openapi():
    # 1. Check if the schema is already cached
    if app.openapi_schema:
        return app.openapi_schema

    # 2. Generate the default schema
    openapi_schema = get_openapi(
        title="Mogul Widget",
        version="1.0.0",
        description="FF14 market profit calculator",
        routes=app.routes,
    )

    # 3. Sort the "components/schemas" dictionary by key
    if "components" in openapi_schema and "schemas" in openapi_schema["components"]:
        schemas = openapi_schema["components"]["schemas"]

        # 1. Map current keys to their 'title' if available
        # This creates a list of (title_or_key, original_key)
        sort_map = []
        for key, value in schemas.items():
            title = value.get("title", key)
            sort_map.append((title, key))

        # 2. Sort the map by the title (A -> A.B -> B)
        sort_map.sort()

        # 3. Rebuild the schema dictionary in that order
        ordered_schemas = {item[1]: schemas[item[1]] for item in sort_map}

        openapi_schema["components"]["schemas"] = ordered_schemas

    app.openapi_schema = openapi_schema
    return openapi_schema


# Apply the override to your FastAPI app instance
app.openapi = custom_openapi

@app.get("/")
async def read_root():
    return {"message": "Hello World"}

@app.post("/newendeavor", response_model=schemas.response.OrdealList, responses={400: {"description": "Invalid server name"},
                                           401: {"description": "Invalid item name"},})
async def new_endeavor(data: schemas.request.Body):
    async with aiohttp.ClientSession() as session:
        all_worlds, all_dcs = await core.gameServer.form_game_server_info()
        world_name = data.world_name
        world = core.gameServer.get_world_by_name(world_name, all_worlds)
        if world is None:
            raise HTTPException(400, f"Error: Could not find server {world_name}!")

        wishlist = core.wishlist.Wishlist({}, world)
        requests = []
        for entry in data.items:
            requests.append(core.ItemRequest(world, entry.name, entry.amount))

        # 2. You MUST await these or use gather
        tasks = [wishlist.process_request(req) for req in requests]
        await asyncio.gather(*tasks)
        # 3. Now the shopping list will actually have data
        new_endeavor: Endeavor = core.Endeavor(wishlist)

        # this is a weird place to put market listing fetch in but it's the earliest we get a list of all mats, and universalis api needs a list of item IDs
        # i could do it one-by-one async, but ratelimit is 30req\s and i would really rather not tackle throttling
        await new_endeavor.low_mats.fetch_and_apply_market_listings(world.dc, session)
        await new_endeavor.mid_mats.fetch_and_apply_market_listings(world.dc, session)

        ordeal_list = core.OrdealList(new_endeavor)


        return schemas.response.OrdealList.model_validate(ordeal_list)

