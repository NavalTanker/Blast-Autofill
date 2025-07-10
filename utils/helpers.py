# Utility functions

def format_response(data, status_code=200):
    """
    Formats a response object.
    """
    return {
        "statusCode": status_code,
        "data": data
    }

if __name__ == "__main__":
    # Example usage
    response = format_response("Success!")
    print(response)
