# app/main.py
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from fastapi import FastAPI, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.db.session import get_db
from app.api import api_router

# ADD THIS IMPORT FOR SESSIONS
# from app.api.endpoints import sessions

from app.core.logging_config import (
    setup_logging,
    LoggingMiddleware,
    log_exceptions,
    get_logger,
)

from app.api import api_router
from app.core.config import settings
from app.api.exception_handlers import (
    validation_exception_handler,
    pydantic_validation_exception_handler,
    integrity_error_handler,
    operational_error_handler,
    http_exception_handler,
    starlette_http_exception_handler,
    general_exception_handler,
)
from app.api.middleware import RequestLoggingMiddleware, TenantContextMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Configure logging early in application startup (add after imports)
is_production = getattr(settings, "ENVIRONMENT", "development") == "production"
setup_logging(
    app_name="quodsi-api",
    log_level="DEBUG" if settings.DEBUG else "INFO",
    json_format=is_production,  # JSON in production, text in development
    log_to_file=True,
    log_to_console=True,
)

# Get logger for main application
logger = get_logger(__name__)


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="FastAPI backend for Quodsi SaaS application with tenant-based user management",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        settings.ALLOWED_HOSTS if hasattr(settings, "ALLOWED_HOSTS") else ["*"]
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add custom middleware
# Add this AFTER your existing middleware (RequestLoggingMiddleware, TenantContextMiddleware, etc.)
app.add_middleware(LoggingMiddleware)
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

# ADD THIS LINE - Include sessions router
# app.include_router(sessions.router, prefix="/api/v1")


# Root endpoint
@app.get("/", tags=["Root"])
def read_root():
    """Root endpoint with basic API information"""
    return {
        "message": "Quodsi API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "api": "/api/v1/",
    }


# Legacy health endpoint for backward compatibility
@app.get("/health", tags=["Health"])
def legacy_health_check():
    """Legacy health check endpoint"""
    return {"status": "healthy"}


# Enhance your existing startup_event function
@app.on_event("startup")
async def startup_event():
    # Keep your existing startup logging
    logging.info("Quodsi API starting up...")
    logging.info(f"Project: {settings.PROJECT_NAME}")
    logging.info(f"Database URL: {settings.DATABASE_URL[:50]}...")

    # Add enhanced startup logging
    logger.info(
        f"Starting {settings.PROJECT_NAME}",
        extra={
            "extra_fields": {
                "environment": getattr(settings, "ENVIRONMENT", "development"),
                "debug": settings.DEBUG,
                "version": "1.0.0",
            }
        },
    )


# Enhance your existing shutdown_event function
@app.on_event("shutdown")
async def shutdown_event():
    # Keep your existing shutdown logging
    logging.info("Quodsi API shutting down...")

    # Add enhanced shutdown logging
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


# Add this new endpoint (in addition to your existing /health endpoints)
@app.get("/db-health")
async def database_health_check(request: Request, db: Session = Depends(get_db)):
    """Database health check endpoint with logging"""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.info(
        "Database health check requested",
        extra={"extra_fields": {"request_id": request_id}},
    )

    try:
        # Execute a simple query to test database connection
        db.execute(text("SELECT 1"))
        logger.info(
            "Database health check successful",
            extra={"extra_fields": {"request_id": request_id}},
        )
        return {
            "status": "healthy",
            "database": "connected",
            "environment": getattr(settings, "ENVIRONMENT", "development"),
        }
    except Exception as e:
        logger.error(
            f"Database health check failed: {str(e)}",
            exc_info=True,
            extra={"extra_fields": {"request_id": request_id}},
        )
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
