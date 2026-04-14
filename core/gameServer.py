from __future__ import annotations

import aiohttp


class DataCenter:
    def __init__(self, name: str):
        self.name = name
        self.worlds: list[World] = []  # Map of Name -> World Object

    def __repr__(self):
        return f"\n<DataCenter {self.name}>"

class World:
    def __init__(self, name: str, dc: DataCenter):
        self.name = name
        self.dc = dc  # This is the "Pointer" back to the parent DC object

    def __repr__(self):
        return f"\n<World {self.name} (DC: {self.dc.name})>"


async def fetch_data_centers(session: aiohttp.ClientSession):
    url = "https://v2.xivapi.com/api/sheet/WorldDCGroupType?fields=Name,IsCloud&limit=999"
    dc_list = list()
    async with session.get(url) as response:
        response.raise_for_status()
        dc_data = await response.json()
    for row in dc_data["rows"]:
        # goofy ahh limits but you gotta do what you gotta do, 0 is some test server, IsCloud = True is virtual DCs they enable for server congestion most probably
        if 0 < row["row_id"] < 999 and not row["fields"]["IsCloud"]:
            dc_list.append(row["fields"]["Name"])

    return dc_list


async def fetch_game_worlds(session: aiohttp.ClientSession):
    url = "https://v2.xivapi.com/api/sheet/World?fields=Name,DataCenter.Name&limit=999"
    world_list = list()
    async with session.get(url) as response:
        response.raise_for_status()
        world_data = await response.json()
    for row in world_data["rows"]:
        name = row["fields"]["Name"]
        dc = row["fields"]["DataCenter"]["fields"]["Name"]
        if (name != "Unknown" and name != "") and (dc != "" and dc != "Unknown"):
            world_list.append({"name": name, "dc": dc})

    return world_list


async def form_game_server_info():
    async with aiohttp.ClientSession() as session:
        raw_dc_names = await fetch_data_centers(session)
        raw_world_data = await fetch_game_worlds(session)

        dc_map = {name: DataCenter(name) for name in raw_dc_names}

        all_worlds = []
        for entry in raw_world_data:
            parent_dc = dc_map.get(entry["dc"])
            if parent_dc:
                new_world = World(entry["name"], parent_dc)
                all_worlds.append(new_world)
                # This handles the "backlink" instantly
                parent_dc.worlds.append(new_world)

        return all_worlds, list(dc_map.values())

#get dc and world objects by name
def get_world_by_name(name: str, world_list: list[World]) -> World | None:
    world = next((world for world in world_list if world.name == name), None)
    return world

def get_dc_by_name(name: str, dc_list) -> DataCenter | None:
    dc = next((dc for dc in dc_list if dc.name == name), None)
    return dc