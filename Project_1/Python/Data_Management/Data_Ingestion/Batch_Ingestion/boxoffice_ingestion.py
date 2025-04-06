import json
import os
from boxoffice_api import BoxOffice
from datetime import datetime, timedelta


# Function to get the data and store into Temporal folder with the prefix of API source
def boxOffice_daily_ingestion(temporal_folder_path):

    box_office = BoxOffice(api_key="46f1c1bd")  # Initialize API

    # Specify the date (YYYY-MM-DD format)
    date = (datetime.today() - timedelta(days=2)).strftime('%Y-%m-%d')

    file_path = os.path.join(temporal_folder_path, "boxoffice_movie_data.json")

    try:
        # Fetch daily box office data
        daily_data = box_office.get_daily(date)

        # Ensure the directory exists
        os.makedirs(temporal_folder_path, exist_ok=True)

        # Save the data to a JSON file
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(daily_data, file, indent=4)

        print('All data ingested in the Temporal Folder')

    except Exception as e:
        print(f"Failed to fetch box office data: {e}")
        return

# boxOffice_daily_ingestion(temporal_folder_path)
