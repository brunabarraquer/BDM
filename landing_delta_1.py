import os
import requests
import gzip
import shutil
from pyspark.sql import SparkSession

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

# Directory to save the downloaded and processed files
DOWNLOAD_DIR = './imdb_datasets/'
TSV_DIR = './imdb_tsv/'  # Directory for extracted TSV files
DELTA_DIR = './delta_tables/'  # Directory for Delta Tables

# Create directories if they don't exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(TSV_DIR, exist_ok=True)
os.makedirs(DELTA_DIR, exist_ok=True)

# Initialize Spark session with Delta support
# Initialize Spark session with Delta support
spark = SparkSession.builder \
    .appName("DeltaLakeIMDb") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.jars.packages", "io.delta:delta-core_2.12:2.1.0") \
    .getOrCreate()

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

# Download, extract, and save as Delta
for file_name in DATA_FILES:
    gz_file_path = os.path.join(DOWNLOAD_DIR, file_name)
    tsv_file_path = os.path.join(TSV_DIR, file_name.replace('.gz', ''))
    delta_table_path = os.path.join(DELTA_DIR, file_name.replace('.tsv.gz', ''))
    
    # Download
    download_file(BASE_URL + file_name, gz_file_path)
    
    # Decompress
    decompress_gz(gz_file_path, tsv_file_path)
    
    # Load TSV into Spark DataFrame
    df = spark.read.option("header", "true").option("sep", "\t").csv(tsv_file_path)
    
    # Save DataFrame as Delta Table
    df.write.format("delta").mode("overwrite").save(delta_table_path)
    print(f"Saved to Delta Lake: {delta_table_path}")

print("✅ All files processed and saved in Delta Lake!")
