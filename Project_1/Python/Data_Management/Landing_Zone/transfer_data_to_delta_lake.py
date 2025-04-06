import pyspark
from delta import *
import os

def clean_column_names(df):
    for col_name in df.columns:
        new_name = col_name.replace(" ", "_").replace("%", "percent").replace("±", "plus_minus")  # Modify as needed
        df = df.withColumnRenamed(col_name, new_name)
    return df

def start_spark():
    builder = pyspark.sql.SparkSession.builder.appName("LocalDeltaTable") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")

    spark = configure_spark_with_delta_pip(builder).getOrCreate()

    return spark

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

            file_path = os.path.join(temporal_folder_path, filename)

            try:
                if filename.endswith('.csv'):

                    df = spark.read.format('csv').option('header', True).load(file_path)
                    # df.show()
                    df.write.format('delta').mode('overwrite').save(str(datasource_folder_path / filename.removesuffix('.csv')))
                    

                elif filename.endswith('.tsv'):
                    df = spark.read.format('csv').option('header', True).option('delimiter', '\t').load(file_path)
                    # # df.show()
                    df.write.format('delta').mode('overwrite').save(str(datasource_folder_path / filename.removesuffix('.tsv')))

                else:
                    df = spark.read.format("json").option("multiline", "true").load(file_path)
                    # df.show()
                    df = clean_column_names(df)
                    df.write.format('delta').mode('overwrite').option('mergeSchema', True).save(str(datasource_folder_path / filename.removesuffix('.json')))
                        


            except Exception as e:
                print(f"Error reading {filename}: {e}")

def create_delta_tables(temporal_folder_path, persistent_folder_path):
    spark = start_spark()
    transfer_data_to_delta_lake(spark, temporal_folder_path, persistent_folder_path)

# from pathlib import Path
# project_folder = Path(__file__).resolve().parents[3]

# temporal_folder_path = project_folder / 'Data Management' / 'Landing Zone' / 'Temporal Zone'
# persistent_folder_path = project_folder / 'Data Management' / 'Landing Zone' / 'Persistent Zone'


# create_delta_tables(temporal_folder_path, persistent_folder_path)