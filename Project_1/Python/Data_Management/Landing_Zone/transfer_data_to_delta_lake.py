import pyspark
from delta import *
import os


# Function to clean column names for JSON file
def clean_column_names(df):
    for col_name in df.columns:
        new_name = col_name.replace(" ", "_").replace("%", "percent").replace("±", "plus_minus")  # Modify as needed
        df = df.withColumnRenamed(col_name, new_name)
    return df


# Function to start the Spark
def start_spark(app_name="LocalDeltaTable"):
    try:
        builder = pyspark.sql.SparkSession.builder.appName(app_name) \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.driver.memory", "8g") \
        .config("spark.executor.memory", "6g") \
        .config("spark.memory.offHeap.enabled", "true") \
        .config("spark.memory.offHeap.size", "2g") \
        .config("spark.sql.shuffle.partitions", "10") \
        .config("spark.network.timeout", "800s") \
        .config("spark.executor.heartbeatInterval", "400s") \
        .config("spark.driver.maxResultSize", "4g") \
        .config("spark.kryoserializer.buffer.max", "1g") \
        .config("spark.sql.broadcastTimeout", "600") \
        .config("spark.rpc.message.maxSize", "512")
        return configure_spark_with_delta_pip(builder).getOrCreate()
    except Exception as e:
        print(f'Cannot start Spark due to configuration error: {e}')
        return False


# Function to transfer data from Temporal folder to Persisten folder (Delta Lake)
def transfer_data_to_delta_lake(spark, temporal_folder_path, persistent_folder_path):
    for filename in os.listdir(temporal_folder_path):
        if '_' in filename:
            datasource = filename.split('_')[0]

            try:
                # Create destination folder: persistent_folder_path/datasource/
                datasource_folder_path = persistent_folder_path / datasource
                datasource_folder_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f'Error occurred to creating the datasource folder: {e}')
                return False

            file_path = os.path.join(temporal_folder_path, filename)

            try:
                if filename.endswith('.csv'):
                    df = spark.read.format('csv').option('header', True).load(file_path)
                    df.write.format('delta').mode('overwrite').save(str(datasource_folder_path / filename.removesuffix('.csv')))

                elif filename.endswith('.tsv'):
                    df = spark.read.format('csv').option('header', True).option('delimiter', '\t').load(file_path)
                    df.write.format('delta').mode('overwrite').save(str(datasource_folder_path / filename.removesuffix('.tsv')))

                else:
                    df = spark.read.format("json").option("multiline", "true").load(file_path)
                    df = clean_column_names(df)
                    df.write.format('delta').mode('overwrite').option('mergeSchema', True).save(str(datasource_folder_path / filename.removesuffix('.json')))
                # df.show()
            except Exception as e:
                print(f"Error reading {filename}: {e}")
                return False
    return True


# Function to create the delta tables for the data files
def create_delta_tables(temporal_folder_path, persistent_folder_path):
    try:
        spark = start_spark()
        if spark == False:
            return False
        successful_transfer = transfer_data_to_delta_lake(spark, temporal_folder_path, persistent_folder_path)
        if not successful_transfer:
            return False
    except Exception as e:
        print(f'Error to create delta tables: {e}')
        return False
    return True

# from pathlib import Path
# project_folder = Path(__file__).resolve().parents[3]

# temporal_folder_path = project_folder / 'Data Management' / 'Landing Zone' / 'Temporal Zone'
# persistent_folder_path = project_folder / 'Data Management' / 'Landing Zone' / 'Persistent Zone'

# create_delta_tables(temporal_folder_path, persistent_folder_path)
