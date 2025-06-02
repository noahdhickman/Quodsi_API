# app/core/config.py

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

    # Security settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # Environment settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
