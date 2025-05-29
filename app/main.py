from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.db.session import get_db
from app.api import api_router

# Create FastAPI application instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multi-tenant simulation platform API",
    version="0.1.0",
    debug=settings.DEBUG,
)


@app.get("/")
async def root():
    """Root endpoint for health checking"""
    return {
        "message": "Welcome to Quodsi API",
        "status": "running",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
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
            "environment": settings.ENVIRONMENT,
        }
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


# Include API router
app.include_router(api_router)


@app.get("/")
def read_root():
    return {"message": "Quodsi API is running"}


