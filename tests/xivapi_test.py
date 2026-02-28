import unittest
import xivapi
from gameServer import GameServer
from itemRequest import ItemRequest

game_server = GameServer("EU", "Light", "Raiden")
item_request = ItemRequest(game_server, "Shakshouka", 10)

class XIVApiTest(unittest.TestCase):

    def test_request(self):
        self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()
