# Module 2: Database & Alembic Configuration

**Duration:** 45-60 minutes  
**Objective:** Configure SQLAlchemy database connection, set up environment variables, and initialize Alembic for database migrations.

**Prerequisites:** Module 1 completed - FastAPI project structure ready

---

## Step 1: Environment Configuration

### 1.1 Create Database Configuration
Create `app/core/config.py`:

```python
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./test.db"  # Fallback to SQLite for development
    )
    
    # API Configuration
    API_V1_STR: str = "/v1"
    PROJECT_NAME: str = "Quodsi API"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Security Configuration (for future use)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()
```

**⚠️ Important:** All environment variables in the `.env` file must be declared in the `Settings` class to avoid Pydantic validation errors.

### 1.2 Create Environment Variables File
Create `.env` file in project root:

```env
# Database Configuration
# SQL Server with Windows Authentication (recommended for local development)
DATABASE_URL=mssql+pyodbc://localhost/QuodsiDb_Dev?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes

# Alternative with SQL Server Authentication:
# DATABASE_URL=mssql+pyodbc://YOUR_USER:YOUR_PASSWORD@YOUR_SERVER/QuodsiDb_Dev?driver=ODBC+Driver+17+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes

# Development Configuration
ENVIRONMENT=development
DEBUG=true

# Security (for future use)
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**⚠️ Important Notes:**
- Replace `QuodsiDb_Dev` with your actual database name
- For Windows Authentication (recommended): Use `Trusted_Connection=yes`
- For SQL Server Authentication: Replace `YOUR_USER`, `YOUR_PASSWORD`, `YOUR_SERVER` with actual values
- Never commit the `.env` file to source control (already in `.gitignore`)

---

## Step 2: Database Session Configuration

### 2.1 Create Database Session Module
Create `app/db/session.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from app.core.config import settings

# Create database engine
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite specific configuration
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG  # Log SQL queries in debug mode
    )
else:
    # SQL Server configuration
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,  # Log SQL queries in debug mode
        pool_pre_ping=True,   # Verify connections before use
        pool_recycle=300      # Recycle connections every 5 minutes
    )

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create declarative base for models
Base = declarative_base()

def get_db():
    """
    Database dependency for FastAPI endpoints.
    Creates a new database session for each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 2.2 Test Database Connection
Create `test_db.py` **in the project root directory** (this avoids Python path issues):

```python
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
```

**Test the connection:**
```bash
# From project root directory
python test_db.py
```

**✅ Checkpoint:** You should see "✅ Database connection successful!" 

If you see an error, verify your `.env` file and database server are running.

---
