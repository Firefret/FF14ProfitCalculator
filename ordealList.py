from __future__ import annotations
import math
from materialList import *
from dataclasses import dataclass


class Craft:
    parent: OrdealList
    entries: list[MarketEntry]

    def __init__(self, parent: OrdealList):
        self.parent = parent

    @property
    def entries(self)  -> list[Material]:
        mats = []
        for mat in self.parent.mats.mid_mats.items.values():
            if mat.ordeal == Ordeal.craft and mat.amount > 0:
                mats.append(mat)
        return mats

class MarketEntry: #
    def __init__(self, material: Material):
        self.material = material
        material.set_quality()

    @property
    def quality(self):
        if self.material.quality is not None:
            return self.material.quality
        else:
            return None

    @property
    def route(self):
        if self.quality:
            routes = self.material.item.marketable.listings.hq_routes
        else:
            routes = self.material.item.marketable.listings.nq_routes

        if routes[self.material.amount] is None:
            routes[self.material.amount] = self.resolve_best_listings()
        return routes[self.material.amount]

    @property
    def overall_price(self) -> int:
        return self.route.total_cost

    def resolve_best_listings(self) -> MarketRoute:
        target_amount = self.material.amount
        quality = self.quality

        if quality:
            listings = self.material.item.marketable.listings.hq
        else:
            listings = self.material.item.marketable.listings.nq

        # largest single listing size
        biggest_amount = max([listing.quantity for listing in listings])

        # maxAmount = upper bound of items we care about
        # Why: once we pass targetAmount, the last jump adds at most biggestAmount,
        # so any useful solution must lie between targetAmount and targetAmount + biggestAmount
        max_amount = target_amount + biggest_amount

        # minCost[x] = cheapest cost to get exactly x items
        # start with unknown (inf)
        min_cost = [float("inf")] * (max_amount+1)

        # choice[x] = index of listing used to reach x items
        # This lets us reconstruct WHICH listings we picked later
        choice = [float("inf")] * (max_amount+1)

        # prev[x] = previous amount before adding the chosen listing
        # This lets us trace back the path
        prev = [float("inf")] * (max_amount+1)

        # base case
        min_cost[0] = 0

        for index, listing in enumerate(listings):
            amount, price = listing.quantity, listing.price

            # IMPORTANT: iterate backwards, it prevents reusing the same listing multiple times in one pass
            for current in range(max_amount - amount, -1, -1):
                # Skip if we don't know how to reach this amount yet
                if math.isinf(min_cost[current]):
                    continue

                new_amount = current + amount
                new_cost = min_cost[current] + price

                # if this gives a cheaper way to reach new_amount, update it
                if new_cost < min_cost[new_amount]:
                    min_cost[new_amount] = new_cost
                    choice[new_amount] = index
                    prev[new_amount] = current

        best_amount = target_amount
        for x in range(target_amount, max_amount + 1):
            # Pick the amount with the lowest cost
            if min_cost[x] < min_cost[best_amount]:
                best_amount = x

        # reconstruct the listings used
        result: list[MarketListing] = []
        cur = best_amount

        while cur > 0:
            i = int(choice[cur])
            result.append(listings[i])
            cur = prev[cur]

        result.sort(key=lambda listing: (listing.world.name, listing.quantity))

        return MarketRoute(int(min_cost[best_amount]), best_amount, result)



@dataclass
class Market:
    parent: OrdealList
    entries: list[MarketEntry]

    def __init__(self, parent: OrdealList):
        self.parent = parent

    @property
    def entries(self)  -> list[MarketEntry]:
        market_entries = []
        joined_list = list(self.parent.mats.low_mats.items.values()) + list(self.parent.mats.mid_mats.items.values())
        for mat in joined_list:
            print(f"listing {mat.item.name}, ordeal is {mat.ordeal}, flags are {mat.flags}, amount is {mat.amount}")
            if mat.ordeal == Ordeal.market and mat.amount > 0:

                print(f"{mat.item.name} added to market ordeal list")
                market_entry = (MarketEntry(mat))
                market_entries.append(market_entry)
        return market_entries

    def __repr__(self):
        return f"Market({self.entries})"


    @property
    def overall_price(self) -> int:
        result = 0
        for entry in self.entries:
            result += entry.overall_price
        return result

    @overall_price.setter
    def overall_price(self, value):
        pass



class VendorEntry:
    material: Material
    listings: dict[str, VendorListing]
    chosen_listing: tuple[str, VendorListing]

    def __init__(self, mat: Material):
        self.material = mat

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

    @property
    def chosen_listing(self) -> tuple[str, VendorListing]:
        listing = self.material.item.vendorable.chosen_listing
        if listing is None:
            first_key = next(iter(self.listings))
            chosen_listing = (first_key, self.listings[first_key])
            for name, listing in self.listings.items():
                if any(x in name for x in ["Scrip", "Tomestone", "Bicolor"]):
                    chosen_listing = (name, listing)
            self.material.item.vendorable.chosen_listing = chosen_listing
        return self.material.item.vendorable.chosen_listing



@dataclass
class Vendor:
    parent: OrdealList
    entries: list[VendorEntry]
    currencies_needed: dict[str, tuple[Item, int]]

    def __init__(self, parent: OrdealList):
        self.parent = parent

    @property
    def entries(self) -> list[VendorEntry]:
        vendor_entries = []
        joined_list = list(self.parent.mats.low_mats.items.values()) + list(
            self.parent.mats.mid_mats.items.values())
        for mat in joined_list:
            if mat.ordeal == Ordeal.vendor and mat.amount > 0:
                vendor_entry = (VendorEntry(mat))
                vendor_entries.append(vendor_entry)
        return vendor_entries

    @property
    def currencies_needed(self) -> dict[str, tuple[Item, int]]:
        dictionary = {}
        for entry in self.entries:
            purchases_needed = math.ceil(entry.material.amount / entry.chosen_listing[1].amount)
            cost_per_purchase = entry.chosen_listing[1].cost
            total_currency_cost = purchases_needed * cost_per_purchase
            if entry.chosen_listing[0] in dictionary:
                total_currency_cost += dictionary[entry.chosen_listing[0]][1]
                dictionary[entry.chosen_listing[0]] = (entry.chosen_listing[1].currency, total_currency_cost)
            else:
                dictionary[entry.chosen_listing[0]] = (entry.chosen_listing[1].currency, total_currency_cost)
        return dictionary



@dataclass
class Gather:
    parent: OrdealList
    entries: entries[Material]

    def __init__(self, parent: OrdealList):
        self.parent = parent

    @property
    def entries(self)  -> entries[Material]:
        mats = []
        joined_list = list(self.parent.mats.low_mats.items.values()) + list(self.parent.mats.mid_mats.items.values())
        for mat in joined_list:
            if mat.ordeal == Ordeal.gather and mat.amount > 0:
                mats.append(mat)
        return mats

@dataclass
class Hunt:
    parent: OrdealList
    entries: list[Material]
    targets: dict[str, tuple[int, list[str]]]

    def __init__(self, parent: OrdealList):
        self.parent = parent

    @property
    def entries(self) -> list[Material]:
        mats = []
        joined_list = list(self.parent.mats.low_mats.items.values()) + list(self.parent.mats.mid_mats.items.values())
        for mat in joined_list:
            if mat.ordeal == Ordeal.hunt and mat.amount > 0:
                mats.append(mat)
        return mats

    @property
    def targets(self) -> dict[str, tuple[int, list[str]]]:
        targets_dict = {}
        for mat in self.entries:
            targets = (mat.amount, mat.item.huntable.drops_from)
            targets_dict[mat.item.name] = targets
        return targets_dict





@dataclass
class OrdealList:
    mats: MaterialListDivided

    craft: Craft | None = None
    market: Market | None = None
    vendor: Vendor | None = None
    gather: Gather | None = None
    hunt: Hunt | None = None

    def __init__(self, mats: MaterialListDivided, priority = None):
        self.mats = mats
        if priority is None:
            from config import FLAG_PRIORITY
            priority = FLAG_PRIORITY

        for mat in (self.mats.mid_mats.items|self.mats.low_mats.items).values():
            mat.set_default_ordeal(priority)

        self.market = Market(self)
        self.vendor = Vendor(self)
        self.gather = Gather(self)
        self.hunt = Hunt(self)
        self.craft = Craft(self)

    def __repr__(self):
        divider = "=" * 60
        sub_div = "-" * 60
        sections = [divider, f"{'ORDEAL LIST SUMMARY':^60}", divider]

        # MARKET SECTION
        if self.market:
            sections.append(f"\n[ MARKET BOARD ] - Total: {self.market.overall_price:,} Gil")
            for m in self.market.entries:
                if m.material.amount == 0:
                    continue
                sections.append(f"  x{m.material.amount:<4} {m.material.item.name:<30} @ {m.overall_price:>8,} Gil")

        # VENDOR SECTION
        if self.vendor:
            sections.append(f"\n[ VENDOR PROCUREMENT ]")
            for currency, (item, cost) in self.vendor.currencies_needed.items():
                sections.append(f"  > Need {cost:,} {currency}")
            for v in self.vendor.entries:
                sections.append(f"    - {v.material.item.name:<30} (x{math.ceil(v.material.amount/v.chosen_listing[1].amount)*v.chosen_listing[1].cost} {v.chosen_listing[0]})")

        # CRAFT SECTION
        if self.craft:
            sections.append(f"\n[ CRAFTING REQUIRED ]")
            for c in self.craft.entries:
                sections.append(f"  x{c.amount:<4} {c.item.name}")

        # GATHER SECTION
        if self.gather:
            sections.append(f"\n[ GATHERING LOG ]")
            for g in self.gather.entries:
                sections.append(f"  x{g.amount:<4} {g.item.name}")

        # HUNT SECTION
        if self.hunt:
            sections.append(f"\n[ HUNTING TARGETS ]")
            for mat_name, targets in self.hunt.targets.items():
                sections.append(f"  x{targets[0]:<4} {mat_name}: {targets[1]}")

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

    def recursively_add_materials(self, mat: Material, amount=None):
        if amount is None:
            amount = mat.amount

        mid_mats = self.mats.mid_mats
        low_mats = self.mats.low_mats
        for ingredient, ing_amount in zip(mat.item.craftable.ingredients[0], mat.item.craftable.ingredients[1]):
            total_amount = amount * ing_amount
            if ingredient.craftable:

                self.recursively_add_materials(mid_mats.items[ingredient.name], total_amount)
                mid_mats.add(mid_mats.items[ingredient.name], total_amount)
            else:
                low_mats.add(low_mats.items[ingredient.name], total_amount)


    def remove_flag_craft(self, mat_name: str):
        mat_list = self.mats.mid_mats.items
        if not mat_name in mat_list:
            return False
        if mat_list[mat_name].ordeal == Ordeal.craft: #is craft ordeal set on mat?
            mat = mat_list[mat_name]
            mat.ordeal = None

            self.recursively_remove_materials(mat)
            return True
        return False

    def add_flag_craft(self, mat_name: str):
        mat_list = self.mats.mid_mats.items
        if not mat_name in mat_list:
            return False
        #No craft flag check because if it is in mid-mats, mat.flags.is_craftable should be true already
        if not mat_list[mat_name].ordeal == Ordeal.craft: #is craft ordeal not set on mat, and is mat not in a craft list?
            mat = mat_list[mat_name]
            mat.ordeal = None

            self.recursively_add_materials(mat)

        return False

    #todo: continue here

