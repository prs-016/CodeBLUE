import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import urllib.parse
load_dotenv()
user = os.environ.get("SNOWFLAKE_USER")
pw = os.environ.get("SNOWFLAKE_PASSWORD")
account = os.environ.get("SNOWFLAKE_ACCOUNT")
safe_password = urllib.parse.quote_plus(pw)
url = f"snowflake://{user}:{safe_password}@{account}/CALCOFI/PUBLIC"
eng = create_engine(url)
with eng.connect() as conn:
    tables = conn.execute(text("SHOW TABLES IN SCHEMA CALCOFI.PUBLIC")).fetchall()
    for t in tables:
        print(t[1])
