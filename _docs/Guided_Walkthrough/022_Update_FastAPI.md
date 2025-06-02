## Step 4: Update FastAPI Application

### 4.1 Update Main Application
Update `app/main.py` to include database information:

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.db.session import get_db

# Create FastAPI application instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multi-tenant simulation platform API",
    version="0.1.0",
    debug=settings.DEBUG
)

@app.get("/")
async def root():
    """Root endpoint for health checking"""
    return {
        "message": "Welcome to Quodsi API",
        "status": "running",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/db-health")
async def database_health_check(db: Session = Depends(get_db)):
    """Database health check endpoint"""
    try:
        # Execute a simple query to test database connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy", 
            "database": "connected",
            "environment": settings.ENVIRONMENT
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "database": "disconnected",
            "error": str(e)
        }
```

### 4.2 Test Updated Application
```bash
# Run the application
uvicorn app.main:app --reload

# Test endpoints:
# http://127.0.0.1:8000/ 
# http://127.0.0.1:8000/health
# http://127.0.0.1:8000/db-health  <- This should show database connected
```

**✅ Checkpoint:** `/db-health` endpoint should return "database": "connected"

---

## Step 5: Create Database (if needed)

### 5.1 For SQL Server Users
If you need to create the database, connect to SQL Server and run:

```sql
-- Create database (replace with your database name)
CREATE DATABASE QuodsiDb_Dev;

-- Verify database exists
SELECT name FROM sys.databases WHERE name = 'QuodsiDb_Dev';
```

### 5.2 Verify Database Access
Test that your application can connect to the new database:

```bash
python test_db.py
```

---

## Step 6: Clean Up and Commit

### 6.1 Remove Temporary Files
```bash
# The test_db.py file can be kept for future testing or removed
# rm test_db.py
```

### 6.2 Update .gitignore
Ensure `.gitignore` includes:

```gitignore
# Add to existing .gitignore if not already present
.env
*.db
*.sqlite
alembic/versions/*.py
!alembic/versions/.gitkeep
test_db.py  # Optional: if you want to exclude the test file
```

### 6.3 Create .gitkeep for Alembic
```bash
# Create empty .gitkeep file to preserve alembic/versions directory
echo. > alembic/versions/.gitkeep
```

### 6.4 Commit Changes
```bash
git add .
git commit -m "feat: configure database connection and Alembic setup"
```

---

## Step 7: Verification Checklist

Verify your setup by checking:

- [ ] ✅ Database connection works (`python test_db.py`)
- [ ] ✅ FastAPI starts without errors (`uvicorn app.main:app --reload`)
- [ ] ✅ `/db-health` endpoint returns "connected"
- [ ] ✅ Alembic connects to database (`alembic current`)
- [ ] ✅ Environment variables loaded correctly
- [ ] ✅ `.env` file not committed to git

---

## Troubleshooting Common Issues

### Issue: "No module named 'app'" when running test_db.py
**Solution:** 
- Ensure you're running `python test_db.py` from the project root directory
- The `test_db.py` file should be in the project root, not in `app/db/`

### Issue: Pydantic ValidationError "Extra inputs are not permitted"
**Solution:**
- Ensure all environment variables in `.env` are declared in the `Settings` class in `config.py`
- Add missing fields like `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`

### Issue: Database Connection Fails
**Solutions:**
1. Verify SQL Server is running
2. Check connection string in `.env` file (ensure correct database name)
3. Verify database exists (e.g., `QuodsiDb_Dev`)
4. Test Windows Authentication vs SQL Server Authentication
5. Check firewall settings

### Issue: SQLAlchemy "Textual SQL expression should be explicitly declared" Error
**Solution:**
- This occurs with SQLAlchemy 2.x when using raw SQL strings
- Import `text` from SQLAlchemy: `from sqlalchemy import text`
- Wrap raw SQL in `text()`: `db.execute(text("SELECT 1"))` instead of `db.execute("SELECT 1")`
- This ensures proper SQL statement handling and prevents SQL injection vulnerabilities

### Issue: Alembic Import Errors
**Solutions:**
1. Ensure virtual environment is active
2. Check Python path in `alembic/env.py`
3. Verify all `__init__.py` files exist

---

## Module 2 Complete! ✅

You now have:
- [x] Database connection configured with proper error handling
- [x] Environment variables set up with all required fields
- [x] Alembic initialized and configured
- [x] Database health check endpoint
- [x] Working test script for database connectivity
- [x] Proper Python path handling for imports

**Next Module:** [003_BaseEntity_Implementation.md](./003_BaseEntity_Implementation.md)

---

## Quick Reference Commands

```bash
# Test database connection (from project root)
python test_db.py

# Run FastAPI with auto-reload
uvicorn app.main:app --reload

# Alembic commands
alembic current                    # Show current migration
alembic history                    # Show migration history
alembic upgrade head              # Apply all migrations
alembic downgrade -1              # Rollback one migration

# Environment variables
# Edit .env file to change database settings
```
