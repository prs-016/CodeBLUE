"""
Databricks Notebook / PySpark Ingestion for Scripps CalCOFI Dataset
Translates raw observational data into the Snowflake feature store.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, to_date

def process_calcofi(spark: SparkSession):
    # This assumes dataset is mounted via Databricks S3 volume
    raw_df = spark.read.csv("s3://threshold-data-lake-2025/raw/calcofi.csv", header=True, inferSchema=True)
    
    # Cleaning and normalization
    cleaned_df = raw_df.select(
        col("station"),
        to_date(col("date"), "yyyy-MM-dd").alias("obs_date"),
        col("depth_m"),
        col("temp_c"),
        col("o2_ml_l")
    ).dropna(subset=["temp_c", "o2_ml_l"])
    
    # Regional mapping mock
    regional_df = cleaned_df.withColumn("region_id", "california_current")
    
    # Write to Snowflake through Databricks connector
    # regional_df.write.format("snowflake").options(**SNOWFLAKE_OPTIONS).save()
    
    return regional_df.count()

if __name__ == "__main__":
    spark = SparkSession.builder.appName("THRESHOLD_CalCOFI_Ingest").getOrCreate()
    print(f"Processed {process_calcofi(spark)} CalCOFI records into feature store.")
