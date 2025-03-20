import os
import requests

# Base URL for IMDb datasets
BASE_URL = 'https://datasets.imdbws.com/'

# List of dataset filenames
DATA_FILES = [
    'name.basics.tsv.gz',
    'title.akas.tsv.gz',
    'title.basics.tsv.gz',
    'title.crew.tsv.gz',
    'title.episode.tsv.gz',
    'title.principals.tsv.gz',
    'title.ratings.tsv.gz'
]

# Directory to save the downloaded files
DOWNLOAD_DIR = './imdb_datasets/'

# Create the download directory if it doesn't exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Function to download a file
def download_file(url, dest_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(dest_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Downloaded: {dest_path}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")

# Download each dataset
for file_name in DATA_FILES:
    file_url = BASE_URL + file_name
    file_path = os.path.join(DOWNLOAD_DIR, file_name)
    download_file(file_url, file_path)
