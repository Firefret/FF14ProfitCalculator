from itemTypes import *

@dataclass
class WishlistEntry:
    item: Craftable | Item
    amount: int

@dataclass
class Wishlist:
    items: dict
    server: World

    def add(self, entry: WishlistEntry):
        if entry.item.name not in self.items:
            self.items[entry.item.name] = entry
        else:
            self.items[entry.item.name].amount += entry