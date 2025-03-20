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

# Directory to save the downloaded files
DOWNLOAD_DIR = './imdb_datasets/'
TSV_DIR = './imdb_tsv/'  # Directory for extracted TSV files

# Create directories if they don't exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(TSV_DIR, exist_ok=True)

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

# Function to decompress .gz files
def decompress_gz(gz_path, tsv_path):
    try:
        with gzip.open(gz_path, 'rb') as f_in:
            with open(tsv_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        print(f"Decompressed: {tsv_path}")
    except Exception as e:
        print(f"Error decompressing {gz_path}: {e}")

# Download and extract each dataset
for file_name in DATA_FILES:
    gz_file_path = os.path.join(DOWNLOAD_DIR, file_name)
    tsv_file_path = os.path.join(TSV_DIR, file_name.replace('.gz', ''))
    
    # Download
    download_file(BASE_URL + file_name, gz_file_path)
    
    # Decompress
    decompress_gz(gz_file_path, tsv_file_path)