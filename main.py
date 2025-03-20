from pyspark.sql import SparkSession

# Create a Spark session with Delta support
spark = SparkSession.builder \
    .appName("LocalDeltaLake") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Define a local path to store the Delta table
delta_table_path = "file:///C:/Users/bruna/delta_table"  # Change this path as needed

# Create a sample DataFrame
data = [("Alice", 1), ("Bob", 2), ("Charlie", 3)]
columns = ["name", "value"]
df = spark.createDataFrame(data, columns)

# Write the DataFrame as a Delta table
df.write.format("delta").mode("overwrite").save(delta_table_path)

