import json
import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError

def handler(event, context):
    s3 = boto3.client('s3')
    bucket = os.environ.get('BUCKET_NAME')
    
    # Event-driven ETL logic mock
    try:
        filename = f"event_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        
        # Validating data
        for record in event.get('Records', []):
            body = json.loads(record['body'])
            if body.get('lat') is None or body.get('lon') is None:
                raise ValueError("Corrupted Data: Missing geospatial coordinates.")
                
        # S3 PutObject with Metadata for Data Lake Governance
        s3.put_object(
            Bucket=bucket,
            Key=f"raw/noaa/year={datetime.now().year}/month={datetime.now().month:02d}/day={datetime.now().day:02d}/{filename}",
            Body=json.dumps(event),
            Metadata={
                'Project': 'Threshold',
                'DataType': 'ClimateRisk',
                'Validated': 'True'
            }
        )
        return {"statusCode": 200, "body": "ETL Ingest Successful"}
    except Exception as e:
        print(f"Infrastructure Failure: {str(e)}")
        raise e
