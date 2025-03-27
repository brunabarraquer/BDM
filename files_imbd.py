import os
import requests
import gzip
import shutil

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

from datetime import datetime
current_date = datetime.today().strftime('%Y-%m-%d')


# Directory to save the downloaded files
DOWNLOAD_DIR = f'./IMDB_datasets/'

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
        return dest_path
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")

def unzip_file(url, dest_path):
    try:
        with gzip.open(url, 'rb') as f_in:
            with open(dest_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    except Exception as e:
        print(f'Error unzip: {e}')

# Download each dataset
for file_name in DATA_FILES:
    file_url = BASE_URL + file_name
    file_path = os.path.join(DOWNLOAD_DIR, file_name)
    dest_path = download_file(file_url, file_path)
    unzip_file(dest_path, os.path.join(DOWNLOAD_DIR, file_name.removesuffix('.gz')))