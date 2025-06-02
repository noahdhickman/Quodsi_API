## Step 3: Alembic Setup for Database Migrations

### 3.1 Initialize Alembic
```bash
# From project root directory
alembic init alembic
```

This creates:
- `alembic/` directory with migration files
- `alembic.ini` configuration file

### 3.2 Configure Alembic Settings
Edit `alembic.ini` file:

Find this line:
```ini
sqlalchemy.url = driver://user:pass@localhost/dbname
```

Comment it out and replace with:
```ini
# sqlalchemy.url = driver://user:pass@localhost/dbname
# URL will be configured in env.py instead
```

### 3.3 Configure Alembic Environment
Edit `alembic/env.py`:

Replace the entire file content with:

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys
from dotenv import load_dotenv

# Load environment variables - be explicit about path and override system vars
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
print(f"Loading .env from: {env_path}")
load_dotenv(env_path, override=True)

# Verify DATABASE_URL is loaded correctly
database_url = os.getenv('DATABASE_URL')
print(f"DATABASE_URL loaded: {database_url}")

# Add your project directory to Python path
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

# Import your models and configuration
from app.core.config import settings
from app.db.session import Base

# Import all models so they are registered with SQLAlchemy metadata
# This automatically imports all models defined in the models package
import app.db.models

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    from sqlalchemy import create_engine
    
    # Use the database URL from settings
    connectable = create_engine(settings.DATABASE_URL)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 3.4 Test Alembic Configuration
```bash
# Test that Alembic can connect to the database
alembic current

# You should see output like:
# Loading .env from: C:\_source\...\quodsi_api\.env
# DATABASE_URL loaded: mssql+pyodbc://localhost/QuodsiDb_Dev?...
# INFO  [alembic.runtime.migration] Context impl MSSQLImpl.
# INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
```

**✅ Checkpoint:** Alembic should connect without errors (even though no migrations exist yet).

### 3.5 Initialize Migration Tracking (if needed)
If `alembic current` shows no output or errors, you may need to initialize the migration tracking:

```bash
# Create the alembic_version table and mark database as up-to-date
alembic stamp head

# Now check current version (should work)
alembic current

# Check migration history
alembic history
```

---

## Troubleshooting Common Issues

### Issue: "Cannot open database QuodsiDb" (Wrong Database Name)
**Cause:** System environment variable is overriding your `.env` file
**Solution:**
```bash
# Check if system environment variable exists
echo $env:DATABASE_URL  # PowerShell
echo %DATABASE_URL%     # Command Prompt

# Remove system environment variable
Remove-Item Env:DATABASE_URL  # PowerShell
set DATABASE_URL=             # Command Prompt

# Or ensure your config.py uses override=True
load_dotenv(override=True)
```

### Issue: "No module named 'app'" in Alembic
**Cause:** Python path issues in alembic/env.py
**Solution:** The updated env.py above includes proper path handling

### Issue: Debug vs Normal Execution Differences
**Cause:** Different environment loading between debug and normal execution
**Solution:** The explicit env_path loading in env.py fixes this

### Issue: Environment Variables Not Loading
**Symptoms:**
- `.env` file contains correct DATABASE_URL
- `os.getenv('DATABASE_URL')` returns different value
- Debug mode works but normal execution fails

**Diagnosis:**
```bash
# Create debug script to check what's loaded
python -c "
import os
from dotenv import load_dotenv
print('Before load_dotenv:', os.getenv('DATABASE_URL'))
load_dotenv()
print('After load_dotenv:', os.getenv('DATABASE_URL'))
load_dotenv(override=True)  
print('After override=True:', os.getenv('DATABASE_URL'))
"
```

**Solution:** Use `load_dotenv(override=True)` in both `config.py` and `alembic/env.py`

### Issue: "Mapper could not assemble any primary key columns" 
**Symptoms:**
- `alembic revision --autogenerate` fails with primary key error
- Models appear to have primary keys defined

**Cause:** Models are not being imported in `env.py`, so Alembic can't detect them

**Solution:** Ensure `import app.db.models` is included in `env.py` (see updated configuration above)

### Issue: New models not detected by Alembic
**Symptoms:**
- Created new model files but `alembic revision --autogenerate` doesn't detect them

**Cause:** New models not imported in the models package `__init__.py`

**Solution:** 
1. Add new model imports to `app/db/models/__init__.py`
2. Update the `__all__` list in the same file
3. The `import app.db.models` in `env.py` will automatically pick up the new models

---

## Updated Configuration Files

Based on the troubleshooting above, ensure your configuration files use the robust loading approach.

**Update `app/core/config.py`:**
```python
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# Load environment variables from .env file - force override system variables
load_dotenv(override=True)

class Settings(BaseSettings):
    # ... rest of your settings class
```

This ensures your `.env` file values always take precedence over system environment variables.

---

## Module Complete! ✅

You now have:
- [x] Alembic properly configured with robust environment loading
- [x] Protection against system environment variable conflicts  
- [x] Proper debugging and error handling
- [x] Working database connection testing

**Next Steps:** You can now create your first database models and migrations.
