# Part 1: Logging Setup and Infrastructure

**Duration:** 15-20 minutes  
**Objective:** Install the logging infrastructure and integrate it into the existing FastAPI application.

---

## Step 1: Install Logging Infrastructure

### 1.1 Create Logging Configuration
Create `app/core/logging_config.py` with the complete implementation from `080_Logging.md`:

```python
"""
Comprehensive logging configuration for Quodsi FastAPI application.
Provides structured JSON logging, request tracing, and exception handling.
"""
import logging
import json
import sys
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from uuid import uuid4
from typing import Optional

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record):
        json_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception information if present
        if record.exc_info:
            json_obj["exception"] = self.formatException(record.exc_info)

        # Add additional fields from extra parameters
        if hasattr(record, "extra_fields"):
            json_obj.update(record.extra_fields)

        return json.dumps(json_obj)

def setup_logging(
    app_name: str = "quodsi-api",
    log_level: str = "INFO",
    json_format: bool = True,
    log_to_file: bool = True,
    log_to_console: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """Configure logging for the FastAPI application"""
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove existing handlers to prevent duplicates
    logger.handlers = []

    # Create formatters
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler with rotation
    if log_to_file:
        log_file = LOGS_DIR / f"{app_name}.log"
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_file_size, backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Error file handler
        error_file = LOGS_DIR / f"{app_name}_error.log"
        error_handler = RotatingFileHandler(
            error_file, maxBytes=max_file_size, backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)
```

### 1.2 Update .gitignore
Add to your `.gitignore`:

```gitignore
# Logs
logs/
*.log
```

---

## Step 2: Create Middleware and Exception Handlers

### 2.1 Add Middleware to logging_config.py
Add this to your `app/core/logging_config.py`:

```python
class LoggingMiddleware:
    """Middleware to log request and response information"""

    def __init__(self, app):
        self.app = app
        self.logger = get_logger("quodsi.request")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope, receive=receive)
        request_id = str(uuid4())

        # Store request ID in state for use in routes
        request.state.request_id = request_id

        # Log request
        start_time = time.time()
        self.logger.info(
            "Request received",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                }
            },
        )

        # Process the request
        response_status = None

        async def send_wrapper(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            response_status = 500
            self.logger.error(
                f"Unhandled exception in middleware: {str(e)}",
                exc_info=True,
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                    }
                },
            )
            raise
        finally:
            # Log response
            end_time = time.time()
            duration = end_time - start_time
            self.logger.info(
                "Request completed",
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response_status,
                        "duration_ms": round(duration * 1000, 2),
                    }
                },
            )
```

### 2.2 Add Exception Handler to logging_config.py
Add this to your `app/core/logging_config.py`:

```python
async def log_exceptions(request: Request, exc: Exception):
    """Global exception handler with logging"""
    logger = get_logger("quodsi.exceptions")
    request_id = getattr(request.state, "request_id", "unknown")

    if isinstance(exc, HTTPException):
        status_code = exc.status_code
        error_type = "HTTPException"
        detail = exc.detail
    elif isinstance(exc, RequestValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        error_type = "ValidationError"
        detail = exc.errors()
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_type = "InternalError"
        detail = str(exc)

    logger.error(
        f"{error_type}: {detail}",
        exc_info=exc,
        extra={
            "extra_fields": {
                "request_id": request_id,
                "error_type": error_type,
                "status_code": status_code,
                "path": request.url.path,
                "method": request.method,
                "detail": detail,
            }
        },
    )

    # Prepare consistent error response
    return {
        "error": {
            "code": status_code,
            "type": error_type,
            "message": detail,
            "request_id": request_id,
        }
    }
```

---

## Step 3: Enhance Existing Main Application

### 3.1 Update app/main.py
**IMPORTANT:** This step enhances your existing `app/main.py` rather than replacing it. Add the following imports and modifications to your current file:

**Add these imports at the top:**
```python
# Add these new imports to your existing imports
from app.core.logging_config import (
    setup_logging,
    LoggingMiddleware,
    log_exceptions,
    get_logger,
)
```

**Add logging setup after imports and before app creation:**
```python
# Configure logging early in application startup (add after imports)
is_production = getattr(settings, 'ENVIRONMENT', 'development') == "production"
setup_logging(
    app_name="quodsi-api",
    log_level="DEBUG" if settings.DEBUG else "INFO",
    json_format=is_production,  # JSON in production, text in development
    log_to_file=True,
    log_to_console=True
)

# Get logger for main application
logger = get_logger(__name__)
```

**Add the new logging middleware to your existing middleware:**
```python
# Add this AFTER your existing middleware (RequestLoggingMiddleware, TenantContextMiddleware, etc.)
app.add_middleware(LoggingMiddleware)
```

**Enhance your existing startup event:**
```python
# Enhance your existing startup_event function
@app.on_event("startup")
async def startup_event():
    # Keep your existing startup logging
    logging.info("Quodsi API starting up...")
    logging.info(f"Project: {settings.PROJECT_NAME}")
    logging.info(f"Database URL: {settings.DATABASE_URL[:50]}...")
    
    # Add enhanced startup logging
    logger.info(f"Starting {settings.PROJECT_NAME}", extra={
        "extra_fields": {
            "environment": getattr(settings, 'ENVIRONMENT', 'development'),
            "debug": settings.DEBUG,
            "version": "1.0.0"
        }
    })
```

**Enhance your existing shutdown event:**
```python
# Enhance your existing shutdown_event function
@app.on_event("shutdown")
async def shutdown_event():
    # Keep your existing shutdown logging
    logging.info("Quodsi API shutting down...")
    
    # Add enhanced shutdown logging
    logger.info(f"Shutting down {settings.PROJECT_NAME}")
```

**Add enhanced database health check endpoint:**
```python
# Add this new endpoint (in addition to your existing /health endpoints)
@app.get("/db-health")
async def database_health_check(request: Request, db: Session = Depends(get_db)):
    """Database health check endpoint with logging"""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.info(
        "Database health check requested",
        extra={"extra_fields": {"request_id": request_id}}
    )
    
    try:
        # Execute a simple query to test database connection
        db.execute("SELECT 1")
        logger.info(
            "Database health check successful",
            extra={"extra_fields": {"request_id": request_id}}
        )
        return {
            "status": "healthy", 
            "database": "connected",
            "environment": getattr(settings, 'ENVIRONMENT', 'development')
        }
    except Exception as e:
        logger.error(
            f"Database health check failed: {str(e)}",
            exc_info=True,
            extra={"extra_fields": {"request_id": request_id}}
        )
        return {
            "status": "unhealthy", 
            "database": "disconnected",
            "error": str(e)
        }
```

**Your final main.py should look similar to this structure:**
```python
# All your existing imports PLUS the new logging imports
from app.core.logging_config import (
    setup_logging,
    LoggingMiddleware,
    log_exceptions,
    get_logger,
)

# Logging setup (NEW)
is_production = getattr(settings, 'ENVIRONMENT', 'development') == "production"
setup_logging(...)
logger = get_logger(__name__)

# Your existing logging configuration
logging.basicConfig(...)

# Your existing FastAPI app creation
app = FastAPI(...)

# Your existing CORS middleware
app.add_middleware(CORSMiddleware, ...)

# Your existing custom middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(TenantContextMiddleware)

# NEW: Add logging middleware
app.add_middleware(LoggingMiddleware)

# Your existing exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
# ... all your other exception handlers

# Your existing API router
app.include_router(api_router)

# Your existing endpoints
@app.get("/")
def read_root():
    # Your existing root endpoint

# Your existing health endpoints
@app.get("/health", tags=["Health"])
def legacy_health_check():
    # Your existing health check

# NEW: Enhanced database health check
@app.get("/db-health")
async def database_health_check(request: Request, db: Session = Depends(get_db)):
    # New enhanced db health check with logging

# Your existing startup/shutdown events (enhanced)
@app.on_event("startup")
async def startup_event():
    # Your existing startup code PLUS new structured logging

@app.on_event("shutdown") 
async def shutdown_event():
    # Your existing shutdown code PLUS new structured logging
```

---

## Step 4: Test Basic Logging

### 4.1 Start the Application
```bash
uvicorn app.main:app --reload
```

### 4.2 Test Endpoints
Open another terminal and test:

```bash
# Test basic endpoint
curl http://localhost:8000/

# Test existing health endpoint
curl http://localhost:8000/health

# Test your existing API endpoints
curl http://localhost:8000/api/v1/

# Test new database health endpoint
curl http://localhost:8000/db-health

# Test error handling
curl http://localhost:8000/nonexistent
```

### 4.3 Check Log Output
You should see:
1. **Console logs** - Both your existing logs AND new structured JSON/text logs
2. **Log files** - Check the `logs/` directory for:
   - `quodsi-api.log` - All logs
   - `quodsi-api_error.log` - Error logs only

### 4.4 Verify Log Structure
Each new structured log entry should include:
- `timestamp` - ISO format timestamp
- `level` - Log level (INFO, ERROR, etc.)
- `message` - Human readable message
- `request_id` - Unique identifier for request correlation
- `module`, `function`, `line` - Code location
- `extra_fields` - Custom context data

---

## Verification Checklist

- [ ] ✅ `app/core/logging_config.py` created
- [ ] ✅ `logs/` directory added to `.gitignore`
- [ ] ✅ `app/main.py` enhanced (not replaced) with logging components
- [ ] ✅ All existing functionality still works (CORS, middleware, exception handlers, API routes)
- [ ] ✅ Application starts without errors
- [ ] ✅ Console shows both existing logs AND new structured logs
- [ ] ✅ Log files are created in `logs/` directory
- [ ] ✅ Each request has a unique `request_id` in the new structured logs
- [ ] ✅ Errors are properly logged with stack traces
- [ ] ✅ Request/response timing is captured
- [ ] ✅ New `/db-health` endpoint works with enhanced logging

---

## What's Next

You now have the foundational logging infrastructure integrated with your existing FastAPI application. The next step is to add logging to your business logic layers.

**Next:** [Part 2: Service and Repository Logging](./080_Logging_Integration_Part2_Services.md)

---

## Troubleshooting

### Issue: Import Errors
**Solution:** Ensure you have the correct imports in `app/core/logging_config.py` and that all imports are properly added to `main.py`

### Issue: Log Files Not Created
**Solution:** Check that the application has write permissions to create the `logs/` directory

### Issue: Duplicate Logs
**Solution:** Make sure you're not calling `setup_logging()` multiple times. You should have both your existing logging AND the new structured logging.

### Issue: No Request ID in New Logs
**Solution:** Verify the `LoggingMiddleware` is properly added to the FastAPI app

### Issue: Existing Functionality Broken
**Solution:** Ensure you enhanced rather than replaced your existing `main.py`. All your existing middleware, exception handlers, and routes should still be present.

### Issue: Multiple Middleware Conflicts
**Solution:** The order of middleware matters. Add `LoggingMiddleware` AFTER your existing middleware (`RequestLoggingMiddleware`, `TenantContextMiddleware`).
