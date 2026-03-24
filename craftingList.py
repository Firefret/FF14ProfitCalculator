from itemTypes import *

@dataclass
class CraftingListEntry:
    item: Craftable | Item
    amount: int

@dataclass
class CraftingList:
    items: dict

    def add(self, entry: CraftingListEntry):
        if entry.item.name not in self.items:
            self.items[entry.item.name] = entry
        else:
            self.items[entry.item.name].amount += entry