from gameServer import GameServer

class ItemRequest:
    def __init__(self, server: GameServer, item_name: str, quantity: int):
        self.server = server
        self.item_name = item_name
        self.quantity = quantity