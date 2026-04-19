import os
try:
    from mangum import Mangum
    from main import app
    
    # AWS Lambda Adapter wraps the FastAPI 'app'
    # This allows THRESHOLD to deploy entirely serverless into AWS infrastructure.
    lambda_handler = Mangum(app)
    
except ImportError:
    print("Mangum not installed. AWS Lambda handler disabled.")
