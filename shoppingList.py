from itemTypes import *
import re

class Ordeal(Enum):
    craft = "craft"
    vendor = "vendor"
    gather = "gather"
    market = "market"
    hunt = "hunt"

@dataclass
class SourceFlags:
    is_craftable: bool
    is_vendorable: bool
    is_gatherable: bool
    is_huntable: bool
    is_marketable: bool

@dataclass
class Material:
    item: Item
    amount: int
    flags: SourceFlags
    ordeal: Ordeal | None = None

    def set_default_flag(self, priority: list[Ordeal]):
        for ordeal in reversed(priority):
            attr_name = f"is_{ordeal.value}able"
            if getattr(self.flags, attr_name, False):
                self.ordeal = ordeal

@dataclass
class ShoppingList: #let it know about the game server somehow
    items: dict #dict of Material
    purchase_route: list | None = None#or a dict of DC world keys, each element is itself a dict with mat, None for now

    def add(self, mat: Material):
        if mat.item.name in self.items:
            self.items[mat.item.name].amount += mat.amount
        else:
            self.items[mat.item.name] = mat
            self.sort()

    def sort(self):
        items = dict()
        crystals = dict()

        for item in self.items.keys():
            if re.search("^(Fire|Ice|Lightning|Water|Earth|Wind)\s(Shard|Crystal|Cluster)$", item):
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
            if mat.flags.is_vendorable:
                if mat.ordeal == Ordeal.vendor:
                    sources.append("[>Vendor<]")
                else:
                    sources.append("[Vendor]")

            if mat.flags.is_gatherable:
                if mat.ordeal == Ordeal.gather:
                    sources.append("[>Gather<]")
                else:
                    sources.append("[Gather]")

            if mat.flags.is_marketable:
                if mat.ordeal == Ordeal.market:
                    sources.append("[>Market<]")
                else:
                    sources.append("[Market]")

            if mat.flags.is_huntable:
                if mat.ordeal == Ordeal.hunt:
                    sources.append("[>Hunt<]")
                else:
                    sources.append("[Hunt]")

            source_str = " ".join(sources)
            lines.append(f"{mat.amount: >4}x {mat.item.name: <25} {source_str} {mat.item}\n")

        return "\n".join(lines)
