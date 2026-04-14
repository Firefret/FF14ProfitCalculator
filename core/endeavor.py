from __future__ import annotations

import asyncio
from dataclasses import dataclass
from .ordealList import *
from .wishlist import Wishlist
from .materialList import MaterialList

@dataclass
class Endeavor:
    def __init__(self, wishlist: Wishlist):
        from .config import FLAG_PRIORITY
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
            from .config import FLAG_PRIORITY
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
        from .config import FLAG_PRIORITY

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
