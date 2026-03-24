from itemTypes import *

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

@dataclass
class ShoppingList: #let it know about the game server somehow
    items: dict #dict of Material
    purchase_route: list | None = None#or a dict of DC world keys, each element is itself a dict with mat, None for now

    def add(self, mat: Material):
        if mat.item.name in self.items:
            self.items[mat.item.name].amount += mat.amount
        else:
            self.items[mat.item.name] = mat

