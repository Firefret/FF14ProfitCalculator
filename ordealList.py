from __future__ import annotations

import math
from materialList import *
from dataclasses import dataclass


class Craft:
    def __init__(self, parent: OrdealList):
        self.parent = parent

    @property
    def list(self)  -> list[Material]:
        mats = []
        for mat in self.parent.mats.mid_mats.items.values():
            if mat.ordeal == Ordeal.craft and mat.amount > 0:
                mats.append(mat)
        return mats

class MarketEntry: #
    def __init__(self, material: Material, parent: Market):
        self.material = material
        self.parent = parent
        self.set_quality()
        self.quality = self.material.quality if self.material.quality is not None else None

    @property
    def nq(self) -> bool:
        amount_needed = self.material.amount
        nq_amount = 0
        is_nq_enough = False
        for listing in self.material.item.marketable.listings.nq:
            nq_amount += listing.quantity
            if nq_amount >= amount_needed:
                is_nq_enough = True
                break
        return is_nq_enough

    @property
    def hq(self) -> bool:
        amount_needed = self.material.amount
        hq_amount = 0
        is_hq_enough = False
        for listing in self.material.item.marketable.listings.hq:
            hq_amount += listing.quantity
            if hq_amount >= amount_needed:
                is_hq_enough = True
                break
        return is_hq_enough

    #def resolve_quality(self):

    def set_quality(self, quality = None) -> bool:
        from config import DEFAULT_QUALITY
        if quality is None: #this sets default or the other one available
            quality = DEFAULT_QUALITY

            if quality: #True if default is HQ
                if self.hq:
                    self.material.quality = True
                    return True
                elif self.nq:
                    self.material.quality = False
                    return True
            else:
                if self.nq:
                    self.material.quality = False
                    return True
                elif self.hq:
                    self.material.quality = True
                    return True
            return False
        else: #this sets what was provided if possible, returns False if not
            if quality and self.hq:
                self.material.quality = True
                return True
            elif not quality and self.nq:
                self.material.quality = False
                return True
            else:
                return False

    def available_amount_handler(self):
        from config import FLAG_PRIORITY
        if not self.nq and not self.hq:
            priority = FLAG_PRIORITY
            priority.remove(Ordeal.market)
            self.material.ordeal = None
            self.material.set_default_ordeal(priority)
            if self.material.ordeal is None:
                raise ValueError(f"Not enough {self.material.item.name} on market ({self.material.amount}) and no other item sources found! ({self.material.flags})")
            return False
        return True

    @property
    def resolve_best_listings(self):
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
        result = []
        cur = best_amount

        while cur > 0:
            i = int(choice[cur])
            result.append(listings[i])
            cur = prev[cur]

        return {"total_cost": min_cost[best_amount], "total_amount": best_amount, "listings": result}



@dataclass
class Market:
    def __init__(self, parent: OrdealList):
        self.parent = parent
        market_list = self.list
    @property
    def list(self)  -> list[MarketEntry]:
        market_entries = []
        joined_list = list(self.parent.mats.low_mats.items.values()) + list(self.parent.mats.mid_mats.items.values())
        for mat in joined_list:
            if mat.ordeal == Ordeal.market and mat.amount > 0:
                market_entry = (MarketEntry(mat, self))
                is_enough = market_entry.available_amount_handler()
                if is_enough:
                    market_entries.append(market_entry)
        return market_entries


    @property
    def overall_price(self) -> int:
        result = 0
        for entry in self.list:
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
                total_currency_cost += dictionary[entry.chosen_listing[0]][1]
                dictionary[entry.chosen_listing[0]] = (entry.chosen_listing[1].currency, total_currency_cost)
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


        self.market = Market(self)

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

        self.craft = Craft(self)

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
        if not mat_name in mat_list:
            return False
        if mat_list[mat_name].ordeal == Ordeal.craft and next((mat for mat in self.craft.list if mat.item.name == mat_name), None): #is craft ordeal set on mat and is mat in a craft list?
            return False
        mat = mat_list[mat_name]
        mat.ordeal = None

        self.recursively_remove_materials(mat)
        return True

    def add_flag_craft(self, mat_name: str):
        mat_list = self.mats.mid_mats.items
        if not mat_name in mat_list:
            return False
        #No craft flag check because if it is in mid-mats, mat.flags.is_craftable should be true already
        if not mat_list[mat_name].ordeal == Ordeal.craft and not next((mat for mat in self.craft.list if mat.item.name == mat_name), None): #is craft ordeal not set on mat and is mat not in a craft list?
            return False

    #todo: continue here

