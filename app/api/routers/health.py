# app/api/routers/health.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from typing import Dict, Any

from app.db.session import get_db
from app.core.config import settings
from app.api.response_helpers import create_success_response, create_error_response

from app.core.logging_config import get_logger

logger = get_logger(__name__)

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