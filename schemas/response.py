from __future__ import annotations
from pydantic import BaseModel, ConfigDict
import core.ordealList

# --- Utility & Global Schemas ---
class World(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True, title="response.World")

class DataCenter(BaseModel):
    name: str
    worlds: list[World]
    model_config = ConfigDict(from_attributes=True, title="response.DataCenter")

class SourceFlags(BaseModel):
    craft: bool
    vendor: bool
    gather: bool
    hunt: bool
    market: bool
    model_config = ConfigDict(from_attributes=True, title="response.SourceFlags")

# --- The "Big" Item Component ---
class Item(BaseModel):
    name: str
    id: int
    icon_url: str | None = None
    model_config = ConfigDict(from_attributes=True, title="response.Item")

    class CraftingData(BaseModel):
        recipe_id: int
        item_yield: int
        ingredients: tuple[list[Item], list[int]]
        model_config = ConfigDict(from_attributes=True, title="response.Item.CraftingData")

    class GatheringData(BaseModel):
        gathering_type: core.ordealList.Gatherer
        model_config = ConfigDict(from_attributes=True, title="response.Item.GatheringData")

    class HuntingData(BaseModel):
        drops_from: list[str]
        model_config = ConfigDict(from_attributes=True, title="response.Item.HuntingData")

    class VendorData(BaseModel):
        class Listing(BaseModel):
            currency: Item
            cost: int
            amount: int
            model_config = ConfigDict(from_attributes=True, title="response.Item.Vendor.Listing")

        listings: list[Listing]
        chosen_listing: tuple[str, Listing] | None = None
        model_config = ConfigDict(from_attributes=True, title="response.Item.Vendor")

    class MarketData(BaseModel):
        class SalesData(BaseModel):
            class ItemSales(BaseModel):
                cheapest_buying_price: int | None = None
                price_dynamics: float | None = None
                selling_velocity: int | None = None
                model_config = ConfigDict(from_attributes=True, title="response.Item.Market.Sales.ItemSales")

            hq: ItemSales | None = None
            nq: ItemSales | None = None
            model_config = ConfigDict(from_attributes=True, title="response.Item.Market.SalesData")

        dc: DataCenter | None = None
        sales: SalesData | None = None
        model_config = ConfigDict(from_attributes=True, title="response.Item.MarketData")

    craftable: CraftingData | None = None
    gatherable: GatheringData | None = None
    marketable: MarketData | None = None
    huntable: HuntingData | None = None
    vendorable: VendorData | None = None

# --- Application Specific Responses ---
class Material(BaseModel):
    item: Item
    amount: int
    flags: SourceFlags
    ordeal: core.ordealList.Ordeal | None = None
    quality: bool | None = None
    is_enough_hq: bool | None = None
    is_enough_nq: bool | None = None
    model_config = ConfigDict(from_attributes=True, title="response.Material")

class MaterialList(BaseModel):
    items: dict[str, Material]
    model_config = ConfigDict(from_attributes=True, title="response.MaterialList")

class Wishlist(BaseModel):
    class Entry(BaseModel):
        item: Item
        amount: int
        model_config = ConfigDict(from_attributes=True, title="response.Wishlist.Entry")

    entries: dict[str, Entry]
    server: World
    model_config = ConfigDict(from_attributes=True, title="response.Wishlist")

class Endeavor(BaseModel):
    wishlist: Wishlist
    player_server: World
    mid_mats: MaterialList
    low_mats: MaterialList
    model_config = ConfigDict(from_attributes=True, title="response.Endeavor")

class OrdealList(BaseModel):
    mats: Endeavor
    model_config = ConfigDict(from_attributes=True, title="response.OrdealList")


# Force Pydantic to finish calculating the nested structures
Item.model_rebuild()
Wishlist.model_rebuild()
Endeavor.model_rebuild()
OrdealList.model_rebuild()