# app/api/__init__.py
from fastapi import APIRouter
from app.api.routers.registration import router as registration_router
from app.api.routers.user_profile import router as user_profile_router
from app.api.routers.health import router as health_router
from app.api.routers.organization import router as organization_router
from app.api.routers.organization_membership import router as membership_router

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include all routers with their specific prefixes and tags
api_router.include_router(
    registration_router, prefix="/auth", tags=["Authentication & Registration"]
)

api_router.include_router(user_profile_router, tags=["User Management"])

api_router.include_router(organization_router, tags=["Organization Management"])

api_router.include_router(membership_router, tags=["Organization Memberships"])

api_router.include_router(health_router, tags=["System Health"])


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
            "organizations": "/api/v1/organizations/",
            "memberships": "/api/v1/memberships/",
            "health": "/api/v1/health/",
        },
    }
