import os
import pyspark
from delta import *

# Spark Session Configuration
def get_spark_session(app_name="LocalDeltaTable"):
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


# Update load_delta_tables to accept `spark` explicitly:
def load_delta_tables(delta_table_path, spark):
    tables = {}
    for file in os.listdir(delta_table_path):
        df = spark.read.format('delta').load(os.path.join(delta_table_path, file))
        tables[file] = df
    return tables