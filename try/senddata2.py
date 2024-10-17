import json
import time

def load_existing_data(filename):
    """Load existing data from JSON file, or return an empty list if file doesn't exist."""
    try:
        with open(filename, "r") as infile:
            return json.load(infile)
    except FileNotFoundError:
        return []

def save_data_to_json(filename, data):
    """Save updated data to JSON file with indentation for readability."""
    with open(filename, "w") as outfile:
        json.dump(data, outfile, indent=4)

def generate_dummy_data(count):
    """Generate dummy data as input."""
    return {
        "no": count,
        "batch": count % 12 + 1,
        "speed" : count,
        "Tanggal": "11-11-2020",
        "thickness": count * 0.2,
        "diameter": count,
        "hardness": count
    }

def main():
    filename = "testobat.json"
    count = 1

    while count <= 200:
        # Load existing data from file
        data_list = load_existing_data(filename)

        # Generate new dummy data
        new_data = generate_dummy_data(count)

        # Add new data to the list
        data_list.append(new_data)

        # Save updated data to file
        save_data_to_json(filename, data_list)

        # Inform user about the data addition
        print(f"Data ke-{count} telah ditambahkan: {new_data}")

        # Increment counter and wait for 5 seconds before adding next data
        count += 1
        time.sleep(2)

if __name__ == "__main__":
    main()