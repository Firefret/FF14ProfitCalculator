from __future__ import annotations
import dataclasses
import math
import re

from itemCache import get_cached_garland_data
from universalis import get_item_listings
from wishlist import *
from xivapi import fetch_top_item_data


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
    quality: bool | None = None
    parent: MaterialList | None = None
    is_enough_hq: bool | None = None

    def __init__(self, item: Item, amount: int, parent=None):
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
        if self.ordeal is not None:
            return
        if self.is_crystal():
            return
        for ordeal in reversed(priority):
            attr_name = ordeal.value
            if attr_name == "market" and hasattr(self.flags, attr_name):
                # print(self.item.name)
                if self.available_amount_handler(priority):
                    self.ordeal = Ordeal.market
                # break #because available_amount_handler() has its own set_default_ordeal call with market excluded from ordeal priority
            if getattr(self.flags, attr_name):
                self.ordeal = ordeal

        # Removal is now handled by recalculate_amounts — no action needed here

    def change_ordeal(self, ordeal: Ordeal):  # only do based on get_possible_ordeals() output
        mat_list = self.parent.parent
        self.ordeal = ordeal
        mat_list.recalculate_amounts()

    def get_possible_ordeals(self) -> list[Ordeal]:
        ordeals = []
        for flag, value in dataclasses.asdict(self.flags).items():
            if flag == "market" and value and (self.is_enough_hq or self.is_enough_nq):
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

    def available_amount_handler(self, priority=None):  # checks if there's enough nq or hq mats, if not,
        if not self.is_enough_nq and not self.is_enough_hq:
            if priority is None:
                from config import FLAG_PRIORITY
                priority = FLAG_PRIORITY
            temp_priority = priority.copy()
            temp_priority.remove(Ordeal.market)
            self.set_default_ordeal(temp_priority)
            if self.ordeal is None:
                raise ValueError(
                    f"Not enough {self.item.name} on market ({self.amount}) and no other item sources found! ({self.flags})")
            return False
        return True

    def set_quality(self, quality=None) -> bool:
        from config import DEFAULT_QUALITY
        if quality is None:  # this sets default or the other one available
            quality = DEFAULT_QUALITY

            if quality:  # True if default is HQ
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
        else:  # this sets what was provided if possible, returns False if not
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
class MaterialList:
    items: dict[str, Material]
    parent: Endeavor | None = None

    def __init__(self, items: dict[str, Material]):
        self.items = items

    async def fetch_and_apply_market_listings(self, dc: DataCenter, session: aiohttp.ClientSession):
        # get a list of all tradeable mats
        item_list = []
        for name, mat in self.items.items():
            garland_data = get_cached_garland_data(name)
            if garland_data is None:
                print(f"No garland_data for {name}")
                continue
            if garland_data["is_tradeable"]:
                item_list.append(mat.item)
            else:
                print(f"{name} does not seem to be tradeable, garlandData view: {garland_data}")
        listings = await get_item_listings(item_list, dc, session)
        for index, item in enumerate(item_list):
            mat = self.items[item.name]
            market_data = MarketData(dc=dc, listings=listings[index])
            mat.item.marketable = market_data

    def add(self, mat: Material, amount=None):
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
class Endeavor:
    def __init__(self, wishlist: Wishlist):
        from config import FLAG_PRIORITY
        self.wishlist = wishlist
        self.player_server = wishlist.server

        # 1. INITIALIZE the attributes FIRST
        self.mid_mats = MaterialList({})
        self.low_mats = MaterialList({})

        # 2. Set the parent references
        self.mid_mats.parent = self
        self.low_mats.parent = self

        # 3. NOW run the sweep (which uses self.low_mats and self.mid_mats)
        for entry in wishlist.entries.values():
            self.recursive_mat_sweep_and_add(entry.item, entry.amount, FLAG_PRIORITY)

        # 4. Run the first math pass
        self.recalculate_amounts()

    def __repr__(self):
        return f"\n--MID MATS--\n{self.mid_mats.__str__()}\n--LOW MATS--\n{self.low_mats.__str__()}"

    def recalculate_amounts(self):
        if not self.wishlist:
            return

        # 1. Reset all existing material amounts to zero
        for mat in self.mid_mats.items.values():
            mat.amount = 0
        for mat in self.low_mats.items.values():
            mat.amount = 0

        # 2. Iterate through the root goals in the wishlist
        for entry in self.wishlist.entries.values():
            # We start depth at 0 for the final products
            self._expand_item(entry.item, entry.amount, depth=0)

    def _expand_item(self, item: Item, amount: int, depth: int):
        """Recursively expand a recipe tree, respecting ordeal decisions."""

        # If we are at depth > 0, we are looking at a component/ingredient
        if depth > 0:
            # Check mid_mats first (craftable components)
            if item.name in self.mid_mats.items:
                mat = self.mid_mats.items[item.name]
                mat.amount += amount

                # DECISION GATE:
                # If we chose NOT to craft this, stop recursion here.
                # We also check for None in case it's a new item not yet initialized.
                if mat.ordeal != Ordeal.craft and mat.ordeal is not None:
                    return

            # Check low_mats (raw materials that aren't craftable)
            elif item.name in self.low_mats.items:
                self.low_mats.items[item.name].amount += amount
                return  # Raw mats have no ingredients, so stop recursion

        # 3. Handle the Crafting Logic
        # We reach this point if:
        # a) It's a depth 0 item (we are making the final product)
        # b) It's a mid_mat set to Ordeal.craft
        if item.craftable:
            craft_yield = item.craftable.item_yield
            # How many times do we need to hit 'Synthesize'?
            num_crafts = math.ceil(amount / craft_yield)

            # Zip ingredients and their counts per-craft
            for ingredient, qty_per in zip(item.craftable.ingredients[0],
                                           item.craftable.ingredients[1]):
                total_needed = num_crafts * qty_per
                self._expand_item(ingredient, total_needed, depth + 1)

    def update_top_item(self, item: Item, new_amount: int):
        existing_entry = next((entry for entry in self.wishlist.entries.values() if entry.item.name == item.name), None)
        if existing_entry:
            existing_entry.amount = new_amount
            self.recalculate_amounts()
            return True
        else:
            return False

    def remove_top_item(self, item_to_remove: Item):
        if self.wishlist is None:
            return False

        # Wrap (key, entry) in parentheses to fix the SyntaxError
        found = next(
            ((key, entry) for key, entry in self.wishlist.entries.items()
             if entry.item.name == item_to_remove.name),
            None
        )

        if found:
            key, _ = found  # Unpack the tuple
            self.wishlist.entries.pop(key)
            self.recalculate_amounts()
            return True
        return False

    def recursive_mat_sweep_and_add(self, item: Item, amount: int, flag_priority=None, depth=0):
        newly_added_names = set()

        if flag_priority is None:
            from config import FLAG_PRIORITY
            flag_priority = FLAG_PRIORITY

        if item.craftable:
            if depth > 0:
                if item.name not in self.mid_mats.items:
                    mat = Material(item, 0, parent=self.mid_mats)
                    # We DO NOT set ordeal here yet because we don't have market listings
                    self.mid_mats.items[item.name] = mat
                    newly_added_names.add(item.name)

            for ingredient in item.craftable.ingredients[0]:
                child_new_names = self.recursive_mat_sweep_and_add(ingredient, 0, flag_priority, depth + 1)
                newly_added_names.update(child_new_names)
        else:
            if item.name not in self.low_mats.items:
                mat = Material(item, 0, parent=self.low_mats)
                self.low_mats.items[item.name] = mat
                newly_added_names.add(item.name)

        return newly_added_names

    async def add_items_to_material_list(self, additions: list[tuple[str, int]], session: aiohttp.ClientSession,
                                         dc: DataCenter):
        from config import FLAG_PRIORITY

        # 1. Fetch top-level items and process requests
        requests = [ItemRequest(self.player_server, name, amt) for name, amt in additions]
        tasks = [self.wishlist.process_request(req) for req in requests]
        await asyncio.gather(*tasks)

        # 2. Sweep: Identify only brand-new material names
        all_new_names = set()
        addition_names = {name for name, _ in additions}
        new_top_entries = [entry for name, entry in self.wishlist.entries.items() if name in addition_names]

        for entry in new_top_entries:
            # This only builds the dictionary keys for things we haven't seen
            newly_discovered = self.recursive_mat_sweep_and_add(entry.item, 0, FLAG_PRIORITY)
            all_new_names.update(newly_discovered)

        # 3. Fetch Listings: Refresh prices for the whole list
        # We refresh everything so your 'is_enough_nq/hq' checks are accurate
        await self.mid_mats.fetch_and_apply_market_listings(dc, session)
        await self.low_mats.fetch_and_apply_market_listings(dc, session)

        # 4. Set Default Ordeals: ONLY for the items marked as new
        for name in all_new_names:
            mat = self.mid_mats.items.get(name) or self.low_mats.items.get(name)
            if mat:
                # Material.set_default_ordeal now has the 'if self.ordeal is not None' guard
                mat.set_default_ordeal(FLAG_PRIORITY)

        # 5. Recalculate: Distribute amounts based on the recipe tree
        # Since ordeals are now "locked" (old ones kept, new ones set),
        # this will correctly stop at market-bought mid-mats.
        self.recalculate_amounts()