from __future__ import annotations

from typing import Union
from pydantic import BaseModel, ConfigDict, model_validator
import core.ordealList
from dataclasses import dataclass, field
from core.itemTypes import SalesData, ListingData, MarketListing
import logging

logger = logging.getLogger(__name__)

class World(BaseModel):
    """Final Fantasy XIV server/shard/world name"""
    name: str
    model_config = ConfigDict(from_attributes=True, title="response.World")


class DataCenter(BaseModel):
    """Final Fantasy XIV datacenter, includes its name and a list of Worlds that belong to it"""
    name: str
    worlds: list[World]
    model_config = ConfigDict(from_attributes=True, title="response.DataCenter")


class SourceFlags(BaseModel):
    """Ordeals, that can be assigned to a Material"""
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
    """Includes a gatherer class, assigned to a Material"""
    gathering_type: Union[core.enums.Gatherer, str]
    model_config = ConfigDict(from_attributes=True, title="response.Item.GatheringData")


class HuntingData(BaseModel):
    """Includes a list or creatures the Material drops from"""
    drops_from: list[str]
    model_config = ConfigDict(from_attributes=True, title="response.Item.HuntingData")


class SharedMarketData(BaseModel):
    """Contains only sale history, drops active marketboard listings."""

    class ItemSales(BaseModel):
        """A list of sale history entries, along with the lowest purchase price, linear
        price dynamics, and selling velocity (items/day)"""
        cheapest_buying_price: int | None = None
        price_dynamics: float | None = None
        selling_velocity: int | None = None
        sale_history: list | None = None
        model_config = ConfigDict(from_attributes=True, title="response.Item.Market.Sales.ItemSales")

    class SalesData(BaseModel):
        """Two instances of ItemSales, each for HQ and LQ item variants"""
        hq: SharedMarketData.ItemSales | None = None
        nq: SharedMarketData.ItemSales | None = None
        model_config = ConfigDict(from_attributes=True, title="response.Item.Market.SalesData")

    dc: DataCenter | None = None
    sales: SalesData | None = None
    model_config = ConfigDict(from_attributes=True, title="response.Item.SharedMarketData")


class FullMarketData(SharedMarketData):
    """Inherits sales tracking and appends heavy real-time marketboard listings from universalis."""

    class MarketListing(BaseModel):
        """Active marketboard listing includes World it is active on, the name of
        the retainer selling it, quantity, overall price, and price per unit"""
        world: World
        retainer_name: str
        quantity: int
        price: int
        price_per_unit: int
        model_config = ConfigDict(from_attributes=True, title="response.Item.Market.MarketListing")

        '''@model_validator(mode="before")
        @classmethod
        def debug_input_object(cls, data):
            """
            Intercepts the incoming raw object *before* Pydantic tries to parse/serialize it.
            If it's an instance of the backend core.itemTypes.MarketListing, we can log it.
            """
            # Print a loud marker so you can see exactly what object tripped the engine
            print("\n=== DEBUG: SERIAlIZING MARKET LISTING OBJECT ===")
            print(f"Raw Input Type: {type(data)}")
            print(f"Raw Input Contents: {data.__dict__ if hasattr(data, '__dict__') else data}")
            print("================================================\n")

            # If your logger is configured, use it too
            logger.warning(f"Pydantic is processing MarketListing object: {data}")

            return data
            '''


    class ListingData(BaseModel):
        """Two instances of MarketListing, each for HQ and LQ item variants"""
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

class SlimMaterial(BaseModel):
    """ This uses SlimItem, for use in Ordeals, so that the full item info does not
    repeat and bloat the API response size"""
    item: SlimItem
    amount: int
    flags: SourceFlags
    ordeal: core.ordealList.Ordeal | None = None
    quality: bool | None = None
    is_enough_hq: bool | None = None
    is_enough_nq: bool | None = None
    model_config = ConfigDict(from_attributes=True, title="response.SlimMaterial")


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
    mid_mats: MaterialList  # Retains full market listing details
    low_mats: MaterialList  # Retains full market listing details
    model_config = ConfigDict(from_attributes=True, title="response.Endeavor")



class OrdealList(BaseModel):
    class Craft(BaseModel):
        entries: list[SlimMaterial]
        model_config = ConfigDict(from_attributes=True, title="response.OrdealList.Craft")

    class Market(BaseModel):
        class MarketRoute(BaseModel):
            total_cost: int
            total_amount: int
            listings: list[FullMarketData.MarketListing]
            model_config = ConfigDict(from_attributes=True, title="response.OrdealList.Market.MarketRoute")

        class MarketEntry(BaseModel):
            material: SlimMaterial
            quality: bool
            route: OrdealList.Market.MarketRoute
            overall_price: int
            model_config = ConfigDict(from_attributes=True, title="response.OrdealList.Market.MarketEntry")

        entries: list[MarketEntry]
        overall_price: int
        route: dict[str, dict[str, list[FullMarketData.MarketListing]]]
        model_config = ConfigDict(from_attributes=True, title="response.OrdealList.Market")

    class Vendor(BaseModel):
        class VendorEntry(BaseModel):
            material: SlimMaterial
            listings: dict[str, SlimItem.VendorData.VendorListing]
            chosen_listing: tuple[str, SlimItem.VendorData.VendorListing]
            model_config = ConfigDict(from_attributes=True, title="response.OrdealList.Vendor.VendorEntry")

        entries: list[VendorEntry]
        currencies_needed: dict[str, tuple[SlimItem, int]]
        model_config = ConfigDict(from_attributes=True, title="response.OrdealList.Vendor")

    class Gather(BaseModel):
        entries: list[SlimMaterial]
        model_config = ConfigDict(from_attributes=True, title="response.OrdealList.Gather")

    class Hunt(BaseModel):
        entries: list[SlimMaterial]
        targets: dict[str, tuple[int, list[str]]]
        model_config = ConfigDict(from_attributes=True, title="response.OrdealList.Hunt")

    endeavor: Endeavor

    craft: Craft
    market: Market
    vendor: Vendor
    gather: Gather
    hunt: Hunt
    model_config = ConfigDict(from_attributes=True, title="response.OrdealList")
    #todo: start working on rudimentary response frontend visualization


# Rebuild schemas to resolve forward declarations and string types
SlimItem.model_rebuild()
Item.model_rebuild()
Wishlist.model_rebuild()
Endeavor.model_rebuild()
OrdealList.model_rebuild()