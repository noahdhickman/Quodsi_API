import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Load environment variables
load_dotenv()

# Get the DATABASE_URL
database_url = os.getenv('DATABASE_URL')
print(f"DATABASE_URL: {database_url}")

# Try to create an engine and connect
try:
    engine = create_engine(database_url)
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        print("✅ Connection successful!")
        print(f"Result: {result.scalar()}")
except Exception as e:
    print(f"❌ Connection failed: {type(e).__name__}: {e}")