from __future__ import annotations

from typing import Union
from pydantic import BaseModel, ConfigDict
import core.ordealList
from dataclasses import dataclass, field
from core.itemTypes import SalesData, ListingData, MarketListing


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


# ===========================================================================
# Reusable Nested Classes
# ===========================================================================

class GatheringData(BaseModel):
    gathering_type: Union[core.enums.Gatherer, str]
    model_config = ConfigDict(from_attributes=True, title="response.Item.GatheringData")


class HuntingData(BaseModel):
    drops_from: list[str]
    model_config = ConfigDict(from_attributes=True, title="response.Item.HuntingData")


class SharedMarketData(BaseModel):
    """Contains only metadata or sales, but drops heavy active market board listings."""

    class ItemSales(BaseModel):
        cheapest_buying_price: int | None = None
        price_dynamics: float | None = None
        selling_velocity: int | None = None
        sale_history: list | None = None
        model_config = ConfigDict(from_attributes=True, title="response.Item.Market.Sales.ItemSales")

    class SalesData(BaseModel):
        hq: SharedMarketData.ItemSales | None = None
        nq: SharedMarketData.ItemSales | None = None
        model_config = ConfigDict(from_attributes=True, title="response.Item.Market.SalesData")

    dc: DataCenter | None = None
    sales: SalesData | None = None
    model_config = ConfigDict(from_attributes=True, title="response.Item.SharedMarketData")


class FullMarketData(SharedMarketData):
    """Inherits sales tracking and appends heavy real-time world-by-world listing tables."""

    class MarketListing(BaseModel):
        world: World
        retainer_name: str
        quantity: int
        price: int
        price_per_unit: int
        model_config = ConfigDict(from_attributes=True, title="response.Item.Market.MarketListing")

    class ListingData(BaseModel):
        hq: list[FullMarketData.MarketListing] | None = None
        nq: list[FullMarketData.MarketListing] | None = None
        model_config = ConfigDict(from_attributes=True, title="response.Item.Market.ListingData")

    listings: ListingData | None = None
    model_config = ConfigDict(from_attributes=True, title="response.Item.FullMarketData")


# ===========================================================================
# Item Schema Variants
# ===========================================================================

class SlimItem(BaseModel):
    """
    Used everywhere inside crafting loops and sub-mats to prevent deep nested duplication.
    """
    name: str
    id: int
    icon_url: str | None = None

    class CraftingData(BaseModel):
        recipe_id: int
        item_yield: int
        # Notice we reference SlimItem here to stop recursive payload bloat
        ingredients: tuple[list[SlimItem], list[int]]
        craft_class: Union[core.enums.Crafter, str]
        model_config = ConfigDict(from_attributes=True, title="response.Item.CraftingData")

    class VendorData(BaseModel):
        class VendorListing(BaseModel):
            currency: SlimItem  # Keeps currencies tiny too
            cost: int
            amount: int
            model_config = ConfigDict(from_attributes=True, title="response.Item.Vendor.Listing")

        listings: list[VendorListing]
        chosen_listing: tuple[str, VendorListing] | None = None
        model_config = ConfigDict(from_attributes=True, title="response.Item.Vendor")

    craftable: CraftingData | None = None
    gatherable: GatheringData | None = None
    marketable: SharedMarketData | None = None  # Drops active listings table
    huntable: HuntingData | None = None
    vendorable: VendorData | None = None
    model_config = ConfigDict(from_attributes=True, title="response.SlimItem")


class Item(SlimItem):
    """
    The original Item model. Includes heavy full active listings directly.
    We swap the field structure to handle FullMarketData.
    """
    marketable: FullMarketData | None = None  # Appends the deep active data block
    model_config = ConfigDict(from_attributes=True, title="response.Item")


# ===========================================================================
# Application Specific Responses
# ===========================================================================

class Material(BaseModel):
    # This uses the Item class, meaning it receives full active board listings
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
        item: Item  # Keeps top level wishlist targets clean but loaded
        amount: int
        model_config = ConfigDict(from_attributes=True, title="response.Wishlist.Entry")

    entries: dict[str, Entry]
    server: World
    model_config = ConfigDict(from_attributes=True, title="response.Wishlist")


class Endeavor(BaseModel):
    wishlist: Wishlist
    player_server: World
    mid_mats: MaterialList  # Retains full market listing details on raw mats
    low_mats: MaterialList  # Retains full market listing details on raw mats
    model_config = ConfigDict(from_attributes=True, title="response.Endeavor")


class OrdealList(BaseModel):
    endeavor: Endeavor
    model_config = ConfigDict(from_attributes=True, title="response.OrdealList")


# Rebuild schemas to resolve forward declarations and string types
SlimItem.model_rebuild()
Item.model_rebuild()
Wishlist.model_rebuild()
Endeavor.model_rebuild()
OrdealList.model_rebuild()