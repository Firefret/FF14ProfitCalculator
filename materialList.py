from __future__ import annotations
import dataclasses
import math

from itemTypes import *
from enum import Enum
import re

from itemTypes import SourceFlags


class Ordeal(Enum):
    craft = "craft"
    vendor = "vendor"
    gather = "gather"
    market = "market"
    hunt = "hunt"


@dataclass
class Material:

    item: Item
    amount: int
    flags: SourceFlags
    ordeal: Ordeal | None = None
    quality: bool  | None = None
    parent: MaterialList | None = None
    is_enough_hq: bool | None = None

    def __init__(self, item: Item, amount:int, parent = None):
        self.item = item
        self.amount = amount
        self.parent = parent

    def __eq__(self, other):
        if self.item.name == other.item.name and self.amount == other.amount:
            return True
        return False

    def is_crystal(self):
        if re.search(r"^(Fire|Ice|Lightning|Water|Earth|Wind)\s(Shard|Crystal|Cluster)$", self.item.name):
            return True
        return False

    def set_default_ordeal(self, priority: list[Ordeal]):
        if self.is_crystal():
            return
        for ordeal in reversed(priority):
            attr_name = ordeal.value
            if attr_name == "market" and hasattr(self.flags, attr_name):
                #print(self.item.name)
                if self.available_amount_handler(priority):
                    self.ordeal = Ordeal.market
                #break #because available_amount_handler() has its own set_default_ordeal call with market excluded from ordeal priority
            if getattr(self.flags, attr_name):
                self.ordeal = ordeal

        # Removal is now handled by recalculate_amounts — no action needed here

    def set_ordeal(self, ordeal: Ordeal) -> bool:
        if not hasattr(self.flags, ordeal.value):
            return False

        if ordeal.value == "market" and not self.is_enough_hq and not self.is_enough_nq:
            return False

        self.ordeal = ordeal
        return True

    def get_possible_ordeals(self) -> list[Ordeal]:
        ordeals = []
        for flag, value in dataclasses.asdict(self.flags).items():
            if flag == "market" and value and self.available_amount_handler():
                ordeals.append(Ordeal.market)
                continue
            if value:
                ordeals.append(Ordeal(flag))
        return ordeals


    @property
    def is_enough_nq(self) -> bool:
        amount_needed = self.amount
        nq_amount = 0
        is_nq_enough = False
        for listing in self.item.marketable.listings.nq:
            nq_amount += listing.quantity
            if nq_amount >= amount_needed:
                is_nq_enough = True
                break
        return is_nq_enough

    @property
    def is_enough_hq(self) -> bool:
        amount_needed = self.amount
        hq_amount = 0
        is_hq_enough = False
        for listing in self.item.marketable.listings.hq:
            hq_amount += listing.quantity
            if hq_amount >= amount_needed:
                is_hq_enough = True
                break
        return is_hq_enough

    def available_amount_handler(self, priority = None): #checks if there's enough nq or hq mats, if not,
        if not self.is_enough_nq and not self.is_enough_hq:
            if priority is None:
                from config import FLAG_PRIORITY
                priority = FLAG_PRIORITY
            priority.remove(Ordeal.market)
            self.ordeal = None
            self.set_default_ordeal(priority)
            if self.ordeal is None:
                raise ValueError(f"Not enough {self.item.name} on market ({self.amount}) and no other item sources found! ({self.flags})")
            return False
        return True

    def set_quality(self, quality = None) -> bool:
        from config import DEFAULT_QUALITY
        if quality is None: #this sets default or the other one available
            quality = DEFAULT_QUALITY

            if quality: #True if default is HQ
                if self.is_enough_hq:
                    self.quality = True
                    return True
                elif self.is_enough_nq:
                    self.quality = False
                    return True
            else:
                if self.is_enough_nq:
                    self.quality = False
                    return True
                elif self.is_enough_hq:
                    self.quality = True
                    return True
            return False
        else: #this sets what was provided if possible, returns False if not
            if quality and self.is_enough_hq:
                self.quality = True
                return True
            elif not quality and self.is_enough_nq:
                self.quality = False
                return True
            else:
                return False

    @property
    def flags(self) -> SourceFlags:
        flags = SourceFlags(craft=True if self.item.craftable else False,
                            vendor=True if self.item.vendorable else False,
                            gather=True if self.item.gatherable else False,
                            hunt=True if self.item.huntable else False,
                            market=True if self.item.marketable else False)

        return flags


@dataclass
class MaterialList: #let it know about the game server somehow
    items: dict[str, Material]
    parent : MaterialListDivided | None = None

    def add(self, mat: Material, amount = None):
        if mat in self.items.values():
            if amount is None:
                self.items[mat.item.name].amount += mat.amount
            else:
                self.items[mat.item.name].amount += amount
        else:
            self.items[mat.item.name] = mat
            self.sort()

    def remove(self, mat_name, amount):
        if mat_name not in self.items:
            return False

        if amount > self.items[mat_name].amount:
            raise ValueError(f"Not enough {mat_name} to remove.")

        self.items[mat_name].amount -= amount
        return True

    def sort(self):
        items = dict()
        crystals = dict()

        for item in self.items.keys():
            if re.search(r"^(Fire|Ice|Lightning|Water|Earth|Wind)\s(Shard|Crystal|Cluster)$", item):
                crystals[item] = self.items[item]
            else:
                items[item] = self.items[item]

        items = dict(sorted(items.items()))
        crystals = dict(sorted(crystals.items()))
        self.items = {**items, **crystals}

    def __str__(self):
        if not self.items:
            return "Shopping List is empty."

        lines = []
        for mat in self.items.values():
            sources = []
            if mat.flags.vendor:
                if mat.ordeal == Ordeal.vendor:
                    sources.append(">Vendor<")
                else:
                    sources.append("[Vendor]")

            if mat.flags.gather:
                if mat.ordeal == Ordeal.gather:
                    sources.append(">Gather<")
                else:
                    sources.append("[Gather]")

            if mat.flags.market:
                if mat.ordeal == Ordeal.market:
                    sources.append(">Market<")
                else:
                    sources.append("[Market]")

            if mat.flags.hunt:
                if mat.ordeal == Ordeal.hunt:
                    sources.append(">Hunt<")
                else:
                    sources.append("[Hunt]")

            if mat.flags.craft:
                if mat.ordeal == Ordeal.craft:
                    sources.append(">Craft<")
                else:
                    sources.append("[Craft]")

            source_str = " ".join(sources)
            lines.append(f"{mat.amount: >4}x {mat.item.name: <25} {source_str} {mat.item}\n")

        return "\n".join(lines)

@dataclass
class MaterialListDivided:
    mid_mats: MaterialList
    low_mats: MaterialList
    top_items: list[tuple] = None  # list of (Item, amount) for top-level recipes

    def __repr__(self):
        return f"\n--MID MATS--\n{self.mid_mats.__str__()}\n--LOW MATS--\n{self.low_mats.__str__()}"

    def recalculate_amounts(self):
        """Zero out all amounts, then re-expand from top-level items,
        stopping at mid_mats whose ordeal is not 'craft'."""
        if not self.top_items:
            return

        # Zero out everything
        for mat in self.mid_mats.items.values():
            mat.amount = 0
        for mat in self.low_mats.items.values():
            mat.amount = 0

        # Re-expand each top-level item
        for item, amount in self.top_items:
            self._expand_item(item, amount, depth=0)

    def _expand_item(self, item: Item, amount: int, depth: int):
        """Recursively expand a recipe tree, respecting ordeal decisions."""
        if item.craftable:
            if depth > 0:
                # Add to mid_mats
                if item.name in self.mid_mats.items:
                    self.mid_mats.items[item.name].amount += amount

                    # If this mid_mat is NOT being crafted, stop here —
                    # the player will obtain it by other means
                    if self.mid_mats.items[item.name].ordeal != Ordeal.craft \
                            and self.mid_mats.items[item.name].ordeal is not None:
                        return

            # Calculate crafts needed
            craft_yield = item.craftable.item_yield
            amount_of_crafts = math.ceil(amount / craft_yield)

            # Expand ingredients
            for ingredient, ing_per_craft in zip(item.craftable.ingredients[0], item.craftable.ingredients[1]):
                total_ing_needed = amount_of_crafts * ing_per_craft
                self._expand_item(ingredient, total_ing_needed, depth + 1)
        else:
            # Leaf node — add to low_mats
            if item.name in self.low_mats.items:
                self.low_mats.items[item.name].amount += amount

    def recursively_remove_materials(self, mat: Material, amount=None):
        """Recalculate everything instead of trying to incrementally remove."""
        self.recalculate_amounts()

    def recursively_add_materials(self, mat: Material, amount=None):
        """Recalculate everything instead of trying to incrementally add."""
        self.recalculate_amounts()


