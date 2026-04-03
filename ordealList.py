import math

from materialList import *
from dataclasses import dataclass


@dataclass
class Craft:
    list: list[Material]


@dataclass
class MarketEntry:
    material: Material
    price_per_item: int
    overall_price: int

@dataclass
class Market:
    list: list[MarketEntry]
    overall_price: int


@dataclass
class VendorEntry:
    material: Material
    listings: dict[str, tuple[Item, int, int]] #literally a place to use VendorListing, rewrite this
    chosen_listing: tuple[str, tuple[Item, int, int]]

@dataclass
class Vendor:
    list: list[VendorEntry]
    currencies_needed: dict[str, tuple[Item, int]]

@dataclass
class Gather:
    list: list[Material]

@dataclass
class Hunt:
    list: list[Material]
    targets: list[str]



@dataclass
class OrdealList:
    mats: MaterialListDivided

    craft: Craft | None = None
    market: Market | None = None
    vendor: Vendor | None = None
    gather: Gather | None = None
    hunt: Hunt | None = None

    def __init__(self, mats: MaterialListDivided):
        self.mats = mats

        market_entries = []
        vendor_entries = []
        gather_entries = []
        hunt_entries = []
        craft_entries = []

        #LOW MATS
        for mat in self.mats.low_mats.items.values():

            # Market
            if mat.ordeal == Ordeal.market:
                price = None
                if mat.item.marketable.sales.hq: #somehow add NQ HQ toggle
                    price = mat.item.marketable.sales.hq.avg_buying_price
                elif mat.item.marketable.sales.nq:
                    price = mat.item.marketable.sales.nq.avg_buying_price
                else:
                    continue

                entry = MarketEntry(mat, price, price*mat.amount)
                market_entries.append(entry)

            # Vendor
            elif mat.ordeal == Ordeal.vendor:
                listings = {}
                default_listing = None
                # Inside the Vendor loop
                for listing in mat.item.vendorable.listings:
                    currency_name = listing.currency.name
                    # Store the inner tuple
                    listings[currency_name] = (listing.currency, listing.cost, listing.amount)

                    if any(x in currency_name for x in ["Scrip", "Tomestone", "Bicolor"]):
                        # Store as (Key, Value_Tuple)
                        default_listing = (currency_name, listings[currency_name])

                # If no special currency found, take the first one available
                if default_listing is None:
                    first_key = list(listings)[0]
                    default_listing = (first_key, listings[first_key])

                entry = VendorEntry(mat, listings, default_listing)
                vendor_entries.append(entry)

            # Gather
            elif mat.ordeal == Ordeal.gather:
                gather_entries.append(mat)

            # Hunt
            elif mat.ordeal == Ordeal.hunt:
                hunt_entries.append(mat)

        #MID MATS
        for mat in self.mats.mid_mats.items.values():
            # Market
            if mat.ordeal == Ordeal.market:
                price = None
                if mat.item.marketable.sales.hq:  # somehow add NQ HQ toggle
                    price = mat.item.marketable.sales.hq.avg_buying_price
                elif mat.item.marketable.sales.nq:
                    price = mat.item.marketable.sales.nq.avg_buying_price
                else:
                    continue

                entry = MarketEntry(mat, price, price * mat.amount)
                market_entries.append(entry)

            # Vendor
            elif mat.ordeal == Ordeal.vendor:
                listings = {}
                default_listing = None
                # Inside the Vendor loop
                for listing in mat.item.vendorable.listings:
                    currency_name = listing.currency.name
                    # Store the inner tuple
                    listings[currency_name] = (listing.currency, listing.cost, listing.amount)

                    if any(x in currency_name for x in ["Scrip", "Tomestone", "Bicolor"]):
                        # Store as (Key, Value_Tuple)
                        default_listing = (currency_name, listings[currency_name])

                # If no special currency found, take the first one available
                if default_listing is None:
                    first_key = list(listings)[0]
                    default_listing = (first_key, listings[first_key])

                entry = VendorEntry(mat, listings, default_listing)
                vendor_entries.append(entry)

            # Gather
            elif mat.ordeal == Ordeal.gather:
                gather_entries.append(mat)

            # Hunt
            elif mat.ordeal == Ordeal.hunt:
                hunt_entries.append(mat)

            #Craft
            elif mat.ordeal == Ordeal.craft:
                craft_entries.append(mat)

        if market_entries:
            overall_price = 0
            for entry in market_entries:
                overall_price += entry.overall_price

            self.market = Market(market_entries, overall_price)

        if vendor_entries:
            currencies_needed = {}
            for entry in vendor_entries:
                currency_name = entry.chosen_listing[0]
                # inner_tuple = (Currency_Item_Object, Cost_Per_Purchase, Amount_Received_Per_Purchase)
                inner_tuple = entry.chosen_listing[1]

                currency_item = inner_tuple[0]
                cost_per_unit = inner_tuple[1]
                yield_per_unit = inner_tuple[2]

                # How many times do we need to "click buy"?
                purchases_needed = math.ceil(entry.material.amount / yield_per_unit)
                total_currency_cost = purchases_needed * cost_per_unit

                if currency_name in currencies_needed:
                    # Update the accumulated cost (index 1 of our stored tuple)
                    current_item, current_cost = currencies_needed[currency_name]
                    currencies_needed[currency_name] = (current_item, current_cost + total_currency_cost)
                else:
                    # Create new entry
                    currencies_needed[currency_name] = (currency_item, total_currency_cost)

            self.vendor = Vendor(vendor_entries, currencies_needed)

        if gather_entries:
            self.gather = Gather(gather_entries)

        if hunt_entries:
            targets = []
            for mat in hunt_entries:
                target = mat.item.huntable.drops_from[0]
                if target not in targets:
                    targets.append(mat.item.huntable.drops_from[0])
            self.hunt = Hunt(hunt_entries, targets)

        if craft_entries:
            self.craft = Craft(craft_entries)

    def __repr__(self):
        divider = "=" * 60
        sub_div = "-" * 60
        sections = [divider, f"{'ORDEAL LIST SUMMARY':^60}", divider]

        # MARKET SECTION
        if self.market:
            sections.append(f"\n[ MARKET BOARD ] - Total: {self.market.overall_price:,} Gil")
            for m in self.market.list:
                sections.append(f"  x{m.material.amount:<4} {m.material.item.name:<30} @ {m.price_per_item:>8,} Gil")

        # VENDOR SECTION
        if self.vendor:
            sections.append(f"\n[ VENDOR PROCUREMENT ]")
            for currency, (item, cost) in self.vendor.currencies_needed.items():
                sections.append(f"  > Need {cost:,} {currency}")
            for v in self.vendor.list:
                sections.append(f"    - {v.material.item.name:<30} (via {v.chosen_listing[0]})")

        # CRAFT SECTION
        if self.craft:
            sections.append(f"\n[ CRAFTING REQUIRED ]")
            for c in self.craft.list:
                sections.append(f"  x{c.amount:<4} {c.item.name}")

        # GATHER SECTION
        if self.gather:
            sections.append(f"\n[ GATHERING LOG ]")
            for g in self.gather.list:
                sections.append(f"  x{g.amount:<4} {g.item.name}")

        # HUNT SECTION
        if self.hunt:
            sections.append(f"\n[ HUNTING TARGETS ]")
            sections.append(f"  Targets: {', '.join(self.hunt.targets)}")
            for h in self.hunt.list:
                sections.append(f"  x{h.amount:<4} {h.item.name}")

        sections.append("\n" + divider)
        return "\n".join(sections)

