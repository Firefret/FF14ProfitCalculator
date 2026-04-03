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

    def set_ordeal(self, ordeal: Ordeal) -> bool:
        if not hasattr(self.flags, f"is_{ordeal.value}able"):
            return False

        self.ordeal = ordeal
        return True

@dataclass
class MaterialList: #let it know about the game server somehow
    items: dict[str, Material]


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
            if mat.flags.is_vendorable:
                if mat.ordeal == Ordeal.vendor:
                    sources.append(">Vendor<")
                else:
                    sources.append("[Vendor]")

            if mat.flags.is_gatherable:
                if mat.ordeal == Ordeal.gather:
                    sources.append(">Gather<")
                else:
                    sources.append("[Gather]")

            if mat.flags.is_marketable:
                if mat.ordeal == Ordeal.market:
                    sources.append(">Market<")
                else:
                    sources.append("[Market]")

            if mat.flags.is_huntable:
                if mat.ordeal == Ordeal.hunt:
                    sources.append(">Hunt<")
                else:
                    sources.append("[Hunt]")

            if mat.flags.is_craftable:
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

    def __repr__(self):
        return f"\n--MID MATS--\n{self.mid_mats.__str__()}\n--LOW MATS--\n{self.low_mats.__str__()}"
