from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Protocol
from .gameServer import DataCenter, World, World  # Explicit imports are cleaner

# --- 1. Enums & Utility Protocols ---
class Crafter(Enum):
    BSM, ARM, ALC, GSM, WVR, CUL, CRP, LTW = (
        "Smithing", "Armorcraft", "Alchemy", "Goldsmithing",
        "Clothcraft", "Cooking", "Woodworking", "Leatherworking"
    )

class Gatherer(Enum):
    BTN, MIN, FSH = "Botanist", "Miner", "Fisher"

@dataclass
class SourceFlags:
    craft: bool
    vendor: bool
    gather: bool
    hunt: bool
    market: bool

# --- 2. Market & Sales Components ---
@dataclass
class ItemSales:
    cheapest_buying_price: int | None = None
    price_dynamics: float | None = None
    selling_velocity: int | None = None

class MarketListing:
    def __init__(self, world: World, retainer_name: str, quantity: int, price: int):
        self.world = world
        self.retainer_name = retainer_name
        self.quantity = quantity
        self.price = price
        self.price_per_unit = round(self.price / self.quantity) if quantity > 0 else 0

    def __repr__(self):
        return f"{self.quantity} from {self.retainer_name} on {self.world.name} for {self.price}\n"

@dataclass
class MarketRoute:
    total_cost: int
    total_amount: int
    listings: list[MarketListing]

@dataclass
class ListingData:
    hq: list[MarketListing] | None = None
    nq: list[MarketListing] | None = None
    nq_routes: list[MarketRoute] | None = None
    hq_routes: list[MarketRoute] | None = None

@dataclass
class SalesData:
    hq: ItemSales | None = None
    nq: ItemSales | None = None

@dataclass
class MarketData:
    dc: DataCenter | None = None
    sales: SalesData | None = None
    listings: ListingData | None = None

# --- 3. Source-Specific Data ---
@dataclass
class CraftingData:
    recipe_id: int
    item_yield: int
    ingredients: tuple[list[Item], list[int]]
    craft_class: Crafter

@dataclass
class GatheringData:
    gathering_type: Gatherer

@dataclass
class HuntingData:
    drops_from: list[str]

@dataclass
class VendorData:
    listings: set[VendorListing]
    chosen_listing: tuple[str, VendorListing] | None = None

    @dataclass(frozen=True)
    class VendorListing:
        currency: Item
        cost: int
        amount: int

    def choose_listing(self, vendor_listing: VendorListing | None) -> bool:
        if vendor_listing and vendor_listing in self.listings:
            self.chosen_listing = (vendor_listing.currency.name, vendor_listing)
            return True
        return False

# --- 4. Protocols (Interfaces) ---
class Craftable(Protocol): craftable: CraftingData
class Gatherable(Protocol): gatherable: GatheringData
class Marketable(Protocol): marketable: MarketData
class Huntable(Protocol): huntable: HuntingData
class Vendorable(Protocol): vendorable: VendorData

# --- 5. The Core Entity ---
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

    def __eq__(self, other):
        if not isinstance(other, Item): return False
        return self.id == other.id