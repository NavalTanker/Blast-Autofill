# Data models

class Item:
    """
    Represents an item in the system.
    """
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self):
        return f"Item(id={self.id}, name='{self.name}')"

if __name__ == "__main__":
    # Example usage
    item = Item(1, "Sample Item")
    print(item)
