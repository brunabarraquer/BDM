import json
import os
from boxoffice_api import BoxOffice

box_office = BoxOffice(api_key="46f1c1bd")  # Initialize API

# Specify the date (YYYY-MM-DD format)
date = "2024-03-25"  # Replace with the desired date

# Define the directory and file path
save_directory = "./box_office"  # Replace with your actual directory
file_path = os.path.join(save_directory, "box_office_data.json")

try:
    # Fetch daily box office data
    daily_data = box_office.get_daily(date)

    # Ensure the directory exists
    os.makedirs(save_directory, exist_ok=True)

    # Save the data to a JSON file
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(daily_data, file, indent=4)

    print(f"Box office data successfully saved to {file_path}")

except Exception as e:
    print(f"Failed to fetch box office data: {e}")
