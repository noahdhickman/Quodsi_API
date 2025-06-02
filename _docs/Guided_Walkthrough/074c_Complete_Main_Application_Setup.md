# Module 7.4c: Complete Main Application Setup

## Purpose
Set up the complete main application with all middleware, exception handlers, and routing integration.

## Prerequisites
- Completed Module 7.4a (Centralized API Router Structure)
- Completed Module 7.4b (Global Middleware and Exception Handling)

---

## Part 3: Complete Main Application Setup

### 3.1 Updated Main Application

Update `app/main.py` with complete setup:

```python
# app/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from app.api import api_router
from app.core.config import settings
from app.api.exception_handlers import (
    validation_exception_handler,
    pydantic_validation_exception_handler,
    integrity_error_handler,
    operational_error_handler,
    http_exception_handler,
    starlette_http_exception_handler,
    general_exception_handler
)
from app.api.middleware import RequestLoggingMiddleware, TenantContextMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="FastAPI backend for Quodsi SaaS application with tenant-based user management",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS if hasattr(settings, 'ALLOWED_HOSTS') else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(TenantContextMiddleware)

# Add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(OperationalError, operational_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API router
app.include_router(api_router)

# Root endpoint
@app.get("/", tags=["Root"])
def read_root():
    """Root endpoint with basic API information"""
    return {
        "message": "Quodsi API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "api": "/api/v1/"
    }

# Legacy health endpoint for backward compatibility
@app.get("/health", tags=["Health"])
def legacy_health_check():
    """Legacy health check endpoint"""
    return {"status": "healthy"}

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logging.info("Quodsi API starting up...")
    logging.info(f"Project: {settings.PROJECT_NAME}")
    logging.info(f"Database URL: {settings.DATABASE_URL[:50]}...")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logging.info("Quodsi API shutting down...")
```

### 3.2 Enhanced Configuration

Update `app/core/config.py` if needed:

```python
# app/core/config.py (additions if not already present)
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Quodsi API"
    VERSION: str = "1.0.0"
    DATABASE_URL: str
    
    # CORS settings
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # API settings
    API_V1_STR: str = "/api/v1"
    
    # Security settings (for future use)
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

---

## Summary

This module integrates all components into the main FastAPI application:

### ✅ **Implemented Components:**

1. **Complete FastAPI Application**: Fully configured with all middleware and handlers
2. **CORS Configuration**: Cross-origin resource sharing setup
3. **Logging Configuration**: Structured logging for the entire application
4. **Startup/Shutdown Events**: Application lifecycle management
5. **Enhanced Settings**: Complete configuration management

### 🧪 **Testing:**

Start the application and verify all components are working:

```bash
uvicorn app.main:app --reload
```

Visit the following URLs to test:
- http://localhost:8000/ - Root endpoint
- http://localhost:8000/docs - Swagger documentation
- http://localhost:8000/api/v1/ - API info
- http://localhost:8000/api/v1/health/ - Health check

### 📚 **Next Steps:**

Continue to Module 7.4d: Complete Testing Suite to implement comprehensive API testing.
