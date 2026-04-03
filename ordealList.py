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
    def __init__(self, list: list[MarketEntry]):
        self.list = list

    @property
    def overall_price(self) -> int:
        result = 0
        for entry in self.list:
            result += entry.overall_price
        return result

    @overall_price.setter
    def overall_price(self, value):
        pass



@dataclass
class VendorEntry:
    material: Material
    listings: dict[str, VendorListing]
    chosen_listing: tuple[str, VendorListing]

    def __init__(self, mat: Material):
        self.material = mat
        first_key = next(iter(self.listings))
        chosen_listing = (first_key, self.listings[first_key])
        for name, listing in self.listings.items():
            if any(x in name for x in ["Scrip", "Tomestone", "Bicolor"]):
                chosen_listing = (name, listing)
        self.chosen_listing = chosen_listing

    @property
    def listings(self) -> dict[str, VendorListing]:
        dictionary = {}
        listing_set = self.material.item.vendorable.listings
        for listing in listing_set:
            dictionary[listing.currency.name] = listing
        return dictionary
    @listings.setter
    def listings(self, value):
        pass



@dataclass
class Vendor:
    list: list[VendorEntry]
    currencies_needed: dict[str, tuple[Item, int]]

    def __init__(self, list: list[VendorEntry]):
        self.list = list

    @property
    def currencies_needed(self) -> dict[str, tuple[Item, int]]:
        dictionary = {}
        for entry in self.list:
            purchases_needed = math.ceil(entry.material.amount / entry.chosen_listing[1].amount)
            cost_per_purchase = entry.chosen_listing[1].cost
            total_currency_cost = purchases_needed * cost_per_purchase
            if entry.chosen_listing[0] in dictionary:
                dictionary[entry.chosen_listing[0]][1] += total_currency_cost
            else:
                dictionary[entry.chosen_listing[0]] = (entry.chosen_listing[1].currency, total_currency_cost)
        return dictionary


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
                entry = VendorEntry(mat)
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
                entry = VendorEntry(mat)
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
            self.market = Market(market_entries)

        if vendor_entries:
            self.vendor = Vendor(vendor_entries)

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
                if m.material.amount == 0:
                    continue
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

    def recursively_remove_materials(self, mat: Material, amount=None):
        if amount is None:
            amount = mat.amount

        mid_mats = self.mats.mid_mats
        low_mats = self.mats.low_mats
        for ingredient, ing_amount in zip(mat.item.craftable.ingredients[0], mat.item.craftable.ingredients[1]):
            total_amount = amount * ing_amount
            if ingredient.craftable:
                self.recursively_remove_materials(mid_mats.items[ingredient.name], total_amount)
                mid_mats.remove(ingredient.name, total_amount)
            else:
                low_mats.remove(ingredient.name, total_amount)

    def remove_flag_craft(self, mat_name: str):
        mat_list = self.mats.mid_mats.items
        low_mats = self.mats.low_mats.items
        if not mat_name in mat_list:
            return False
        if not mat_list[mat_name].ordeal == Ordeal.craft and next((mat for mat in self.craft.list if mat.item.name == mat_name), None): #is craft ordeal set on mat and is mat in a craft list?
            return False
        mat = mat_list[mat_name]
        self.craft.list.remove(mat)
        mat.ordeal = None

        self.recursively_remove_materials(mat)
        return True

    #todo: continue here

