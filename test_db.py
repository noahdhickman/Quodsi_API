"""
Test database connection from project root.
Run: python test_db.py
"""
from sqlalchemy import text
from app.db.session import engine

def test_connection():
    """Test database connection"""
    try:
        print("Testing database connection...")
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("✅ Database connection successful!")
                print(f"Connected to: {engine.url.database}")
                return True
            else:
                print("❌ Database connection failed - unexpected result")
                return False
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print("\nPossible solutions:")
        print("1. Ensure SQL Server is running")
        print("2. Verify the database exists (e.g., 'QuodsiDb_Dev')")
        print("3. Check Windows Authentication permissions")
        print("4. Verify ODBC Driver 17 for SQL Server is installed")
        return False

if __name__ == "__main__":
    test_connection()