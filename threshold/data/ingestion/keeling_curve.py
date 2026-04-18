"""
Databricks Notebook / PySpark Ingestion for Scripps Keeling Curve Dataset
Translates raw CO2 data into Snowflake feature tables.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when

def process_keeling(spark: SparkSession):
    raw_df = spark.read.csv(
        "s3://threshold-data-lake-2025/raw/keeling_daily.csv", 
        header=True, 
        comment="#"
    )
    
    # Handle -99.99 missing values
    cleaned_df = raw_df.withColumn(
        "co2_ppm", 
        when(col("co2_ppm") == -99.99, None).otherwise(col("co2_ppm"))
    ).dropna(subset=["co2_ppm"])
    
    return cleaned_df.count()

if __name__ == "__main__":
    spark = SparkSession.builder.appName("THRESHOLD_Keeling_Ingest").getOrCreate()
    process_keeling(spark)
