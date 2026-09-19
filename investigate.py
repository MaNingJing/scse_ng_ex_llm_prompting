## Import the necessary modules
import json
from pathlib import Path
from ollama import chat

## Import the function from the module parse_data
from parse_data import load_items, get_unclaimed_items, save_result


## Build your prompt based on the description the user provides
## and the items that are available in the lost-and-found database.
def build_prompt(description, available_items):
    # Convert available_items into a JSON string
    items_json = json.dumps(available_items, indent=2)

    system_prompt = (
        "You are a campus lost-and-found assistant. "
        "Your job is to match a user's description of a lost item "
        "against a database of found items.\n\n"
        "RULES:\n"
        "1. Use ONLY the given JSON database of found items.\n"
        "2. Not all details must match to be a possible match.\n"
        "3. Return ONLY valid JSON, with EXACTLY this structure:\n"
        '{"matches": ["ITEM_ID"], "confidence": "LOW"}\n'
        "4. 'matches' contains all possible matching item IDs.\n"
        "5. 'confidence' must be exactly one of: LOW, MEDIUM, HIGH.\n"
        "6. If there is no match, return an empty list: "
        '{"matches": [], "confidence": "LOW"}\n'
        "7. Do NOT include any explanation, markdown, or extra text. "
        "Return ONLY the JSON object."
    )

    user_prompt = (
        f"Available items in the lost-and-found database:\n"
        f"{items_json}\n\n"
        f"The user is describing the item they lost:\n"
        f"\"{description}\"\n\n"
        f"Return the JSON result."
    )

    return system_prompt, user_prompt


## Logic to ask Qwen for all the possible matches based on the system prompt and user prompt.
## The function should return the response from Qwen.
def ask_qwen(system_prompt, user_prompt):
    try:
        response = chat(
            model="qwen3:8b",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )
        return response.message.content
    except Exception as error:
        print(f"Error: Could not get response from Qwen: {error}")
        return None


## Logic to parse the response from Qwen and return the result.
## You may need to use json.loads() to convert the response string into a suitable Python data structure.
def parse_response(response_text):
    if response_text is None:
        return None

    cleaned = response_text.strip()

    # Remove markdown code fences if present
    if cleaned.startswith("```"):
        # Remove first line (```json or ```)
        first_newline = cleaned.find("\n")
        if first_newline != -1:
            cleaned = cleaned[first_newline + 1:]

        # Remove trailing ```
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

    cleaned = cleaned.strip()

    try:
        result = json.loads(cleaned)
        return result
    except json.JSONDecodeError:
        print("Error: Could not parse response as JSON.")
        print(f"Raw response:\n{response_text}")
        return None


## Logic to validate the result returned by Qwen.
def validate_result(result, available_items):
    # Check result is a dictionary
    if not isinstance(result, dict):
        return False

    # Check required keys
    if "matches" not in result:
        return False

    if "confidence" not in result:
        return False

    # Check "matches" is a list
    if not isinstance(result["matches"], list):
        return False

    # Check "confidence" is a string and one of LOW, MEDIUM, HIGH
    if not isinstance(result["confidence"], str):
        return False

    if result["confidence"] not in ["LOW", "MEDIUM", "HIGH"]:
        return False

    # Build a set of valid item IDs
    valid_ids = set()
    for item in available_items:
        valid_ids.add(item["id"])

    # Check all IDs in "matches" are valid
    for item_id in result["matches"]:
        if item_id not in valid_ids:
            return False

    return True


## Logic to display the matches found by Qwen in a user-friendly format.
def display_matches(result, available_items):
    print()
    print("MATCH RESULT")
    print("-" * 50)
    print(f"Confidence: {result['confidence']}")
    print()

    if len(result["matches"]) == 0:
        print("No matches found.")
        return

    print("Possible matches:")
    print()

    # Build a lookup dictionary: id -> item
    lookup = {}
    for item in available_items:
        lookup[item["id"]] = item

    for item_id in result["matches"]:
        item = lookup.get(item_id)

        if item is not None:
            print(f"ID: {item['id']}")
            print(f"Item: {item['item']}")
            print(f"Color: {item['color']}")
            print(f"Location: {item['location']}")
            print(f"Date found: {item['date']}")
            print()


## Control center for the entire program.
def main():
    # Print the header
    print("CAMPUS LOST-AND-FOUND ASSISTANT")
    print("=" * 50)
    print()

    # Ask the user for a description
    description = input("Describe the item you lost: ").strip()

    if description == "":
        print("Error: Description cannot be empty.")
        return

    print()
    print("Searching for possible matches...")

    # Load items from the JSON file
    all_items = load_items("found_items.json")

    if len(all_items) == 0:
        print("Error: No items could be loaded.")
        return

    # Filter only unclaimed items
    available_items = get_unclaimed_items(all_items)

    # Build the prompts
    system_prompt, user_prompt = build_prompt(description, available_items)

    # Ask Qwen
    response_text = ask_qwen(system_prompt, user_prompt)

    if response_text is None:
        print("Error: Failed to get response from the model.")
        return

    # Parse the response
    result = parse_response(response_text)

    if result is None:
        print("Error: Failed to parse the model's response.")
        return

    # Validate the result
    if not validate_result(result, available_items):
        print("Error: The model returned an invalid result.")
        return

    # Display the matches
    display_matches(result, available_items)

    # Save the result
    output_filename = "output/match_result.json"
    saved = save_result(result, output_filename)

    if saved:
        print(f"Result saved to {output_filename}")


if __name__ == "__main__":
    main()