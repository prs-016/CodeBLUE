import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "THRESHOLD API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # DB (Local SQLite Mocking Snowflake for Dev)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///../threshold.db")
    
    # Snowflake Real Data
    SNOWFLAKE_USER: str = os.getenv("SNOWFLAKE_USER", "")
    SNOWFLAKE_PASSWORD: str = os.getenv("SNOWFLAKE_PASSWORD", "")
    SNOWFLAKE_ACCOUNT: str = os.getenv("SNOWFLAKE_ACCOUNT", "")
    
    # Environment
    USE_MOCK_SNOWFLAKE: bool = True  # True for Hackathon demo if real credentials fail

settings = Settings()
