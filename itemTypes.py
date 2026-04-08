from __future__ import annotations
from typing import Protocol
from dataclasses import dataclass
from enum import Enum
from gameServer import *



class Crafter(Enum):
    BSM = "Smithing"
    ARM = "Armorcraft"
    ALC = "Alchemy"
    GSM = "Goldsmithing"
    WVR = "Clothcraft"
    CUL = "Cooking"
    CRP = "Woodworking"
    LTW = "Leatherworking"

class Gatherer(Enum):
    BTN = "Botanist"
    MIN = "Miner"
    FSH = "Fisher"


@dataclass
class CraftingData:
    recipe_id: int
    item_yield: int
    ingredients: tuple[list[Item], list[int]]
    craft_class: Crafter

class Craftable(Protocol):
    craftable: CraftingData

@dataclass
class GatheringData:
    gathering_type: Gatherer

class Gatherable(Protocol):
    gatherable: GatheringData

@dataclass
class ItemSales:
    avg_buying_price: int | None = None #for visual purposes only, all the None fields are populated las, when universalis data is processed
    price_dynamics: float | None = None
    selling_velocity: float | None = None

class MarketListing:
    world: World
    retainer_name: str
    quantity: int
    price: int
    price_per_unit: int

    def __init__(self, world: World, retainer_name: str, quantity: int, price: int):
        self.world = world
        self.retainer_name = retainer_name
        self.quantity = quantity
        self.price = price
        self.price_per_unit = round(self.price / self.quantity)

@dataclass
class MarketRoute:
    total_cost: int
    total_amount: int
    listings: list[MarketListing]

@dataclass
class ListingData:
    hq: list[MarketListing | None]
    nq: list[MarketListing | None]
    nq_routes: list[MarketRoute | None] | None = None
    hq_routes: list[MarketRoute | None] | None = None

    def __repr__(self):
        return f"{len(self.hq)} HQ listings and {len(self.nq)} NQ listings"

@dataclass
class SalesData:
    hq: ItemSales | None = None
    nq: ItemSales | None = None


@dataclass
class MarketData:
    dc: DataCenter | None = None
    sales: SalesData | None = None
    listings: ListingData | None = None

class Marketable(Protocol):
    marketable: MarketData

@dataclass
class HuntingData:
    drops_from: list[str]

class Huntable(Protocol):
    hunting: HuntingData

@dataclass(frozen=True)
class VendorListing:
    currency: Item
    cost: int
    amount: int

@dataclass
class SourceFlags:
    craft: bool
    vendor: bool
    gather: bool
    hunt: bool
    market: bool

@dataclass
class VendorData:
    listings: set[VendorListing]
    chosen_listing: tuple[str, VendorListing] | None = None

    def choose_listing(self, vendor_listing: VendorListing | None) -> bool:
        if vendor_listing in self.listings:
            self.chosen_listing = (vendor_listing.currency.name, vendor_listing)
            return True
        else:
            return False

class Vendorable(Protocol):
    vendorable: VendorData


@dataclass
class Item:
    name: str
    id: int
    icon_url: str | None = None
    craftable: CraftingData | None = None
    gatherable: GatheringData | None = None
    marketable: MarketData | None = None
    huntable: HuntingData | None = None
    vendorable: VendorData | None = None

    def __hash__(self) -> int:
        return hash(self.id)


def is_craftable(item: Item) -> bool:
    if item.craftable:
        return True
    else:
        return False

def is_gatherable(item: Item) -> bool:
    if item.gatherable:
        return True
    else:
        return False

def is_marketable(item: Item) -> bool:
    if item.marketable:
        return True
    else:
        return False



