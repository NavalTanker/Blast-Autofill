# Main application file

def main():
    """
    Main function to run the application.
    """
    print("Application started.")

    # Example: Integrating layers
    # This is a simplified example. In a real app, you'd likely have a more sophisticated way
    # to handle user input and orchestrate calls between layers.

    from presentation.cli import handle_command as cli_handle_command
    from logic.services import process_data
    from data.models import Item
    from data.repository import add_item, get_item

    # Simulate adding an item through the data layer
    try:
        item1 = Item(id=1, name="My First Item")
        add_item(item1)
        print(f"Added item: {get_item(1)}")
    except ValueError as e:
        print(f"Error adding item: {e}")

    try:
        item2 = Item(id=2, name="Another Item")
        add_item(item2)
        print(f"Added item: {get_item(2)}")
    except ValueError as e:
        print(f"Error adding item: {e}")


    # Simulate processing data using the logic layer
    raw_data = "example data to process"
    processed = process_data(raw_data)
    print(f"Original: '{raw_data}', Processed: '{processed}'")

    # Simulate a command via the presentation layer
    print("\nSimulating CLI command 'greet':")
    cli_handle_command("greet")

    print("\nSimulating CLI command 'add_item 1 SampleCLIItem': (Note: CLI needs update to support this)")
    # For a real CLI interaction for adding items, presentation/cli.py would need to be updated
    # to parse arguments and call a service function, which in turn uses the repository.
    # Now presentation/cli.py has a basic add_item command.
    print("\nSimulating CLI command 'add_item 3 CLIDrivenItem':")
    cli_handle_command("add_item 3 CLIDrivenItem")


    # Using the new services from app.py
    from logic.services import create_item_service, get_item_service

    print("\nUsing services directly from app.py:")
    # Clear repository for cleaner app-level demonstration if needed, or ensure unique IDs
    # from data.repository import _items
    # _items.clear() # Optional: Clears items added by previous direct repo calls or CLI simulations

    print(create_item_service(item_id=100, item_name="AppServiceItem1"))
    item_from_service = get_item_service(100)
    if item_from_service:
        print(f"Retrieved item via service: {item_from_service}")
    else:
        print("Item 100 not found via service.")

    print(create_item_service(item_id=101, item_name="AppServiceItem2"))
    print(get_item_service(101))


    print("\nApplication finished.")


if __name__ == "__main__":
    main()
