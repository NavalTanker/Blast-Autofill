# Data repository

# Example in-memory storage
_items = {}

def get_item(item_id):
    """
    Retrieves an item by its ID.
    """
    return _items.get(item_id)

def add_item(item):
    """
    Adds an item to the repository.
    """
    if item.id in _items:
        raise ValueError(f"Item with ID {item.id} already exists.")
    _items[item.id] = item
    return item

if __name__ == "__main__":
    from models import Item
    # Example usage
    item1 = Item(1, "First Item")
    add_item(item1)
    retrieved_item = get_item(1)
    print(f"Retrieved item: {retrieved_item}")
