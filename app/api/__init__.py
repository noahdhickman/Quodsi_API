# app/api/__init__.py
from fastapi import APIRouter
from app.api.routers.registration import router as registration_router

api_router = APIRouter(prefix="/api")
api_router.include_router(registration_router)