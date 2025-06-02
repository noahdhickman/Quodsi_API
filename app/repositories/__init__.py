# app/repositories/__init__.py
"""
Repository layer for data access operations.

This package contains repositories that provide clean interfaces
for database operations with built-in tenant isolation and
consistent CRUD patterns.
"""

from .base import BaseRepository
from .tenant_repository import TenantRepository, tenant_repo
from .user_repository import UserRepository, user_repo
from .user_session_repository import UserSessionRepository
from .organization_repository import OrganizationRepository

# Create singleton instance for dependency injection
organization_repo = OrganizationRepository()

__all__ = [
    "BaseRepository",
    "TenantRepository",
    "tenant_repo",
    "UserRepository",
    "user_repo",
    "UserSessionRepository",
    "OrganizationRepository",
    "organization_repo",
]
