from gameServer import *

class ItemRequest:
    def __init__(self, server: World, item_name: str, quantity: int):
        self.server = server
        self.dc = server.dc
        self.item_name = item_name
        self.quantity = quantity