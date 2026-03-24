from itemTypes import *

@dataclass
class Material:
    item: Item
    amount: int

@dataclass
class ShoppingList: #let it know about the game server somehow
    items: dict #dict of Material
    purchase_route: list #or a dict of DC world keys, each element is itself a dict with mat

    def add(self, mat: Material):
        if mat.item.name in self.items:
            self.items[mat.item.name].amount += mat.amount
        else:
            self.items[mat.item.name] = mat

