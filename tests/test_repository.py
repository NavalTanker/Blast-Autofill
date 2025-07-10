import unittest
from data.models import Item
from data.repository import add_item, get_item, _items

class TestRepository(unittest.TestCase):
    def setUp(self):
        # Clear the in-memory store before each test
        _items.clear()

    def test_add_and_get_item(self):
        item = Item(1, "Test Item")
        add_item(item)
        retrieved_item = get_item(1)
        self.assertEqual(retrieved_item.name, "Test Item")

    def test_get_non_existent_item(self):
        retrieved_item = get_item(99)
        self.assertIsNone(retrieved_item)

    def test_add_duplicate_item(self):
        item1 = Item(1, "First Item")
        add_item(item1)
        item2 = Item(1, "Duplicate Item")
        with self.assertRaises(ValueError):
            add_item(item2)

if __name__ == "__main__":
    unittest.main()
