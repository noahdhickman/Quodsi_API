# Module 7.4a: Centralized API Router Structure

## Purpose
Set up the centralized API routing structure and health check endpoints to organize all API endpoints under a unified structure.

## Prerequisites
- Completed Module 7.1 (API Response Standard and Mock Authentication)
- Completed Module 7.2 (Registration Endpoint Implementation)  
- Completed Module 7.3 (User Profile Endpoints)
- All service layers implemented

---

## Overview

In this module, we'll create:
1. **Centralized API Router** - Organized routing structure for all endpoints
2. **Health Check Endpoints** - System monitoring and health verification

## Learning Objectives

By the end of this module, you'll understand:
- How to organize FastAPI applications with multiple routers
- How to implement comprehensive health checking and monitoring

---

## Part 1: Centralized API Router Structure

### 1.1 Complete API Router Setup

Update `app/api/__init__.py` to organize all routers:

```python
# app/api/__init__.py
from fastapi import APIRouter
from app.api.routers.registration import router as registration_router
from app.api.routers.user_profile import router as user_profile_router
from app.api.routers.health import router as health_router

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include all routers with their specific prefixes and tags
api_router.include_router(
    registration_router,
    prefix="/auth",
    tags=["Authentication & Registration"]
)

api_router.include_router(
    user_profile_router,
    tags=["User Management"]
)

api_router.include_router(
    health_router,
    tags=["System Health"]
)

# Version information endpoint
@api_router.get("/", tags=["API Info"])
async def api_info():
    """Get API version and basic information"""
    return {
        "name": "Quodsi API",
        "version": "1.0.0",
        "description": "FastAPI backend for Quodsi SaaS application",
        "endpoints": {
            "registration": "/api/v1/auth/registration/",
            "users": "/api/v1/users/",
            "health": "/api/v1/health/"
        }
    }
```

### 1.2 Health Check Router

Create `app/api/routers/health.py`:

```python
# app/api/routers/health.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from typing import Dict, Any

from app.db.session import get_db
from app.core.config import settings
from app.api.response_helpers import create_success_response, create_error_response

router = APIRouter(prefix="/health")

@router.get("/", response_model=dict)
async def health_check():
    """Basic health check endpoint"""
    return create_success_response({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "quodsi-api",
        "version": "1.0.0"
    })

@router.get("/detailed", response_model=dict)
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check including database connectivity"""
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "quodsi-api",
        "version": "1.0.0",
        "checks": {}
    }
    
    # Database connectivity check
    try:
        db.execute(text("SELECT 1"))
        health_data["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_data["status"] = "unhealthy"
        health_data["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
    
    # Configuration check
    try:
        required_configs = ["DATABASE_URL", "PROJECT_NAME"]
        missing_configs = []
        
        for config in required_configs:
            if not hasattr(settings, config.lower()) or not getattr(settings, config.lower()):
                missing_configs.append(config)
        
        if missing_configs:
            health_data["checks"]["configuration"] = {
                "status": "warning",
                "message": f"Missing configurations: {', '.join(missing_configs)}"
            }
        else:
            health_data["checks"]["configuration"] = {
                "status": "healthy",
                "message": "All required configurations present"
            }
            
    except Exception as e:
        health_data["checks"]["configuration"] = {
            "status": "unhealthy",
            "message": f"Configuration check failed: {str(e)}"
        }
    
    return create_success_response(health_data)

@router.get("/readiness", response_model=dict)
async def readiness_check(db: Session = Depends(get_db)):
    """Kubernetes readiness probe endpoint"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        
        return create_success_response({
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return create_error_response(
            code="NOT_READY",
            message=f"Service not ready: {str(e)}"
        )

@router.get("/liveness", response_model=dict)
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    return create_success_response({
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    })
```

---

## Summary

This module sets up the foundation for centralized API routing:

### ✅ **Implemented Components:**

1. **Centralized Router Structure**: All endpoints organized under `/api/v1/`
2. **Health Check Endpoints**: Basic, detailed, readiness, and liveness checks
3. **API Information Endpoint**: Provides API version and endpoint information

### 🚀 **API Endpoints Summary:**

- **API Info**: `/api/v1/` - Detailed API information
- **Health**: `/api/v1/health/*` - Various health check endpoints

### 🧪 **Testing:**

Start the API server and test the endpoints:

```bash
# Start the API server
uvicorn app.main:app --reload

# Test endpoints
curl http://localhost:8000/api/v1/
curl http://localhost:8000/api/v1/health/
curl http://localhost:8000/api/v1/health/detailed
```

### 📚 **Next Steps:**

Continue to Module 7.4b: Global Middleware and Exception Handling to implement comprehensive error handling and request logging.
