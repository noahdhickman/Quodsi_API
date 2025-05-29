# app/api/__init__.py
from fastapi import APIRouter
from app.api.routers.registration import router as registration_router
from app.api.routers.user_profile import router as user_profile_router

api_router = APIRouter(prefix="/api")
api_router.include_router(registration_router)
api_router.include_router(user_profile_router)