# Command-line interface

def handle_command(command):
    """
    Handles user commands.
    """
    parts = command.split()
    action = parts[0]

    if action == "greet":
        print("Hello, user!")
    elif action == "add_item":
        # This is a basic example. A real implementation would have better error handling
        # and would call a service in the logic layer.
        if len(parts) == 3:
            try:
                item_id = int(parts[1])
                item_name = parts[2]
                # In a real app, this would call a service:
                # from logic.services import create_item_service
                # result = create_item_service(item_id, item_name)
                # print(result)
                print(f"CLI: Received add_item command for ID {item_id}, Name '{item_name}'. (Implementation pending in services)")
            except ValueError:
                print("Invalid item ID. Must be an integer.")
        else:
            print("Usage: add_item <id> <name>")
    else:
        print("Unknown command.")

if __name__ == "__main__":
    # Example usage
    while True:
        user_input = input("Enter command (e.g., 'greet', 'add_item 1 MyItem', 'exit'): ")
        if user_input.lower() == "exit":
            break
        handle_command(user_input)
