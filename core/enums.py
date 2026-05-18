from enum import Enum


class Ordeal(Enum):
    craft = "craft"
    vendor = "vendor"
    gather = "gather"
    market = "market"
    hunt = "hunt"

class Crafter(Enum):
    BSM, ARM, ALC, GSM, WVR, CUL, CRP, LTW = (
        "Smithing", "Armorcraft", "Alchemy", "Goldsmithing",
        "Clothcraft", "Cooking", "Woodworking", "Leatherworking"
    )

class Gatherer(Enum):
    BTN, MIN, FSH = "Botanist", "Miner", "Fisher"
