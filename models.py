from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from core.ordealList import *


class ItemEntry(BaseModel):
    name: str
    amount: int

class RequestBody(BaseModel):
    world_name: str
    items: list[ItemEntry]


class MaterialResponse(BaseModel):
    item: ItemResponse
    amount: int
    flags: SourceFlagsResponse
    ordeal: Ordeal | None = None
    quality: bool | None = None
    is_enough_hq: bool | None = None
    is_enough_nq: bool | None = None
    model_config = ConfigDict(from_attributes=True)

class SourceFlagsResponse(BaseModel):
    craft: bool
    vendor: bool
    gather: bool
    hunt: bool
    market: bool
    model_config = ConfigDict(from_attributes=True)

class WishlistResponse(BaseModel):
    entries: dict[str, WishlistEntryResponse]
    server: WorldResponse
    model_config = ConfigDict(from_attributes=True)

class WishlistEntryResponse(BaseModel):
    item: ItemResponse
    amount: int
    model_config = ConfigDict(from_attributes=True)

class ItemResponse(BaseModel):
    name: str
    id: int
    icon_url: str
    model_config = ConfigDict(from_attributes=True)

class MaterialListResponse(BaseModel):
    items: dict[str, MaterialResponse]
    model_config = ConfigDict(from_attributes=True)

class DataCenterResponse(BaseModel):
    name: str
    worlds: list[WorldResponse]
    model_config = ConfigDict(from_attributes=True)

class WorldResponse(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)


class EndeavorResponse(BaseModel):
    wishlist: WishlistResponse
    player_server: WorldResponse
    mid_mats: MaterialListResponse
    low_mats: MaterialListResponse
    model_config = ConfigDict(from_attributes=True)

class OrdealListResponse(BaseModel):
    mats: EndeavorResponse
    #craft: Craft | None = None
    #market: Market | None = None
    #vendor: Vendor | None = None
    #gather: Gather | None = None
    #hunt: Hunt | None = None
    model_config = ConfigDict(from_attributes=True)
    # todo: find a way to deserialize ordeal structures

