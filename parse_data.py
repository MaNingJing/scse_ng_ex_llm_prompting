## Import the necessary modules
import json
from pathlib import Path


## Logic for loading and reading from a JSON file.
## The function must return only the items
def load_items(filename):
    try:
        with open(filename, "r") as file:
            data = json.load(file)
        return data["items"]
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: File '{filename}' is not valid JSON.")
        return []
    except KeyError:
        print("Error: JSON file does not contain 'items' key.")
        return []


## Logic for getting only those items that are not yet claimed
## It should return only the items that are unclaimed
def get_unclaimed_items(items):
    unclaimed = []

    for item in items:
        if item["status"] == "unclaimed":
            unclaimed.append(item)

    return unclaimed


## Logic to save the result to a JSON file.
## The function should create the directory if it does not exist and save the result in a JSON format.
def save_result(result, filename):
    try:
        # Use pathlib to handle the path
        path = Path(filename)

        # Create parent directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        # Save the result as JSON
        with path.open("w") as file:
            json.dump(result, file, indent=2)

        return True

    except OSError:
        print(f"Error: Could not save to '{filename}'.")
        return False