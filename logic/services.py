# Business services

def process_data(data):
    """
    Processes the given data.
    """
    # Example processing
    processed_data = data.upper()
    return processed_data

# Example service that uses the repository
from data.models import Item
from data.repository import add_item as repo_add_item, get_item as repo_get_item

def create_item_service(item_id, item_name):
    """
    Service to create a new item.
    It encapsulates the logic of creating an Item object and adding it via the repository.
    """
    try:
        item = Item(id=item_id, name=item_name)
        added_item = repo_add_item(item)
        return f"Service: Item '{added_item.name}' added successfully with ID {added_item.id}."
    except ValueError as e:
        return f"Service Error: {str(e)}"
    except Exception as e:
        # Log error e
        return f"Service Error: An unexpected error occurred: {str(e)}"

def get_item_service(item_id):
    """
    Service to retrieve an item.
    """
    item = repo_get_item(item_id)
    if item:
        return item
    else:
        return None


if __name__ == "__main__":
    # Example usage of process_data
    result = process_data("sample data")
    print(f"Processed data: {result}")

    # Example usage of item services
    print(create_item_service(10, "Service Item 1"))
    print(create_item_service(11, "Service Item 2"))
    print(create_item_service(10, "Duplicate Service Item")) # Test duplicate

    retrieved = get_item_service(10)
    if retrieved:
        print(f"Retrieved via service: {retrieved}")
    else:
        print("Item 10 not found via service.")

    retrieved_non_existent = get_item_service(999)
    if retrieved_non_existent:
        print(f"Retrieved via service: {retrieved_non_existent}")
    else:
        print("Item 999 not found via service.")
