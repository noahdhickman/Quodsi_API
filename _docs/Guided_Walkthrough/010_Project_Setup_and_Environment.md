# Module 1: Project Setup & Environment Configuration

**Duration:** 30-45 minutes  
**Objective:** Set up the foundational project structure, Python environment, and basic FastAPI application stub.

---

## Prerequisites Checklist

Before starting, ensure you have:
- [ ] Python 3.8+ installed (`python --version`)
- [ ] Git installed (`git --version`)
- [ ] Code editor (VS Code recommended)
- [ ] Access to MS SQL Server instance (local or remote)

---

## Step 1: Initialize Project Structure

### 1.1 Create Main Project Directory
```bash
# Navigate to your development folder
cd C:\_source\Greenshoes\Summer2025Internship\Sprint 2

# Create project directory
mkdir quodsi_api
cd quodsi_api
```

### 1.2 Set Up Python Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate

# Verify activation (should show (venv) in prompt)
```

**✅ Checkpoint:** Your terminal prompt should now show `(venv)` indicating the virtual environment is active.

---

## Step 2: Install Core Dependencies

### 2.1 Install FastAPI and Core Packages
```bash
pip install fastapi "uvicorn[standard]" sqlalchemy python-dotenv pyodbc alembic pydantic[email] pydantic-settings
```

**Package Breakdown:**
- `fastapi` - Modern web framework for APIs
- `uvicorn` - ASGI server for running FastAPI
- `sqlalchemy` - Python ORM for database operations
- `python-dotenv` - Environment variable management
- `pyodbc` - MS SQL Server database driver
- `alembic` - Database migration tool
- `pydantic[email]` - Data validation with email support
- `pydantic-settings` - Pydantic settings management for configuration

### 2.2 Create Requirements File
```bash
pip freeze > requirements.txt
```

**✅ Checkpoint:** Check that `requirements.txt` contains all installed packages.

---

## Step 3: Create Basic Project Structure

### 3.1 Create Directory Structure
```bash
# Create app directory and subdirectories
mkdir app
mkdir app\core
mkdir app\db
mkdir app\api
mkdir app\schemas
mkdir app\repositories
mkdir app\services

# Create __init__.py files for Python packages
echo. > app\__init__.py
echo. > app\core\__init__.py
echo. > app\db\__init__.py
echo. > app\api\__init__.py
echo. > app\schemas\__init__.py
echo. > app\repositories\__init__.py
echo. > app\services\__init__.py
```

### 3.2 Expected Project Structure
```
quodsi_api/
├── venv/                    # Virtual environment
├── app/                     # Main application code
│   ├── __init__.py
│   ├── main.py             # FastAPI application entry point
│   ├── core/               # Core configuration
│   │   └── __init__.py
│   ├── db/                 # Database related code
│   │   └── __init__.py
│   ├── api/                # API endpoints
│   │   └── __init__.py
│   ├── schemas/            # Pydantic schemas
│   │   └── __init__.py
│   ├── repositories/       # Data access layer
│   │   └── __init__.py
│   └── services/           # Business logic layer
│       └── __init__.py
├── requirements.txt
└── .env                    # Environment variables (to be created)
```

---

## Step 4: Create FastAPI Application Stub

### 4.1 Create Main Application File
Create `app/main.py`:

```python
from fastapi import FastAPI

# Create FastAPI application instance
app = FastAPI(
    title="Quodsi API",
    description="Multi-tenant simulation platform API",
    version="0.1.0"
)

@app.get("/")
async def root():
    """Root endpoint for health checking"""
    return {
        "message": "Welcome to Quodsi API",
        "status": "running",
        "version": "0.1.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
```

### 4.2 Test Basic FastAPI Setup
```bash
# Run the application
uvicorn app.main:app --reload --port 8000

# You should see output like:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete.
```

**✅ Checkpoint:** 
- Open browser to `http://127.0.0.1:8000` - should see welcome message
- Visit `http://127.0.0.1:8000/docs` - should see Swagger UI
- Visit `http://127.0.0.1:8000/health` - should see health status

Stop the server with `Ctrl+C` before continuing.

---

## Step 5: Git Setup

### 5.1 Create .gitignore File
Create `.gitignore` in project root:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Environment variables
.env
.env.local
.env.*.local

# Database
*.db
*.sqlite

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Alembic - Migration files MUST be version controlled
# Only ignore temporary/local migration files if you have them
# DO NOT ignore alembic/versions/*.py files - they are critical for deployments
# alembic/versions/*
# !alembic/versions/.gitkeep

# Testing
.pytest_cache/
.coverage
htmlcov/

# Build
build/
dist/
*.egg-info/
```

### 5.2 Initialize Git Repository
```bash
# Initialize git repository
git init

# Add all files
git add .

# Initial commit
git commit -m "feat: initial project setup with FastAPI stub"
```

**✅ Checkpoint:** Run `git status` - should show "working tree clean"

---

## Step 6: Verification & Next Steps

### 6.1 Verify Environment
Run these commands to verify everything is set up correctly:

```bash
# Check Python environment
python --version

# Check virtual environment is active
where python
# Should show path to your venv directory

# Check installed packages
pip list

# Check git repository
git log --oneline
```

### 6.2 Expected Output
- Python version 3.8+
- Virtual environment active
- All required packages installed
- Git repository initialized with initial commit

---

## Troubleshooting Common Issues

### Issue: Virtual Environment Not Activating
**Solution:** 
- Windows: Use `.\venv\Scripts\activate.bat` instead
- Check PowerShell execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### Issue: pip install fails
**Solution:**
- Update pip: `python -m pip install --upgrade pip`
- Check Python version compatibility

### Issue: FastAPI won't start
**Solution:**
- Ensure virtual environment is active
- Check for typos in `app/main.py`
- Verify port 8000 is not in use

### Issue: Migration files not appearing in git
**Symptoms:** Alembic migration files created but not showing up in `git status`
**Cause:** The .gitignore above has commented out the migration exclusion lines
**Important:** Migration files (.py files in alembic/versions/) MUST be version controlled
**Why:** 
- Team members need same migrations to set up their databases
- Production deployments require these files
- They are the historical record of your database schema changes
- Rollback functionality depends on these files
**Never ignore:** `alembic/versions/*.py` files in a real project

---

## Module 1 Complete! ✅

You now have:
- [x] Python virtual environment set up
- [x] All required dependencies installed
- [x] Basic project structure created
- [x] Working FastAPI application
- [x] Git repository initialized

**Next Module:** [002_Database_and_Alembic_Setup.md](./020_Database_and_Alembic_Setup.md)

---

## Quick Reference Commands

```bash
# Activate virtual environment
.\venv\Scripts\activate

# Run FastAPI application
uvicorn app.main:app --reload

# Install new package
pip install package_name
pip freeze > requirements.txt

# Git commands
git add .
git commit -m "commit message"
git status
```
