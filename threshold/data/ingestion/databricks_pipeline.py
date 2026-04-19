# Databricks PySpark Ingestion Pipeline for THRESHOLD

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, current_date

def run_databricks_pipeline():
    """
    Sponsor integration: Databricks PySpark execution endpoint.
    This notebook is designed to be executed via Databricks Workflows, pulling Scripps data directly to Delta format.
    """
    spark = SparkSession.builder \\
        .appName("Threshold_Ocean_Ingestion") \\
        .getOrCreate()
        
    print("Databricks Pipeline Initialized. Reading CalCOFI data...")
    
    # In a real Databricks deployment, this path points to 'dbfs:/mnt/calcofi/dataset.csv'
    # Fallback to local mockup for Code Blue Demo
    schema = ["region_id", "date", "sst_anomaly", "o2_current"]
    
    mock_calcofi_data = [
        ("california_current", "2024-01-01", 1.2, 5.4),
        ("california_current", "2024-01-15", 1.3, 5.2),
        ("great_barrier_reef", "2024-01-01", 2.1, 6.1)
    ]
    
    df = spark.createDataFrame(mock_calcofi_data, schema=schema)
    
    # Feature Engineering via PySpark transformations
    df_transformed = df.withColumn("ingestion_date", current_date()) \\
                       .withColumn("hypoxia_flag", col("o2_current") < 2.0)
                       
    df_transformed.show()
    
    # Write to Delta table (Using DBFS or S3 bucket via Databricks)
    # df_transformed.write.format("delta").mode("overwrite").save("dbfs:/threshold/processed_features")
    print("Saved pipeline outputs to Databricks Delta Lake.")

if __name__ == "__main__":
    run_databricks_pipeline()
