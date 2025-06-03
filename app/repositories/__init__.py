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
from .organization_membership_repository import OrganizationMembershipRepository
from .model_repository import ModelRepository
from .model_permission_repository import ModelPermissionRepository
from .model_access_log_repository import ModelAccessLogRepository
from .analysis_repository import AnalysisRepository
from .scenario_repository import ScenarioRepository

# Create singleton instances for dependency injection
organization_repo = OrganizationRepository()
organization_membership_repo = OrganizationMembershipRepository()
model_repo = ModelRepository()
model_permission_repo = ModelPermissionRepository()
model_access_log_repo = ModelAccessLogRepository()
analysis_repo = AnalysisRepository()
scenario_repo = ScenarioRepository()

__all__ = [
    "BaseRepository",
    "TenantRepository",
    "tenant_repo",
    "UserRepository",
    "user_repo",
    "UserSessionRepository",
    "OrganizationRepository",
    "organization_repo",
    "OrganizationMembershipRepository",
    "organization_membership_repo",
    "ModelRepository",
    "model_repo",
    "ModelPermissionRepository",
    "model_permission_repo",
    "ModelAccessLogRepository",
    "model_access_log_repo",
    "AnalysisRepository",
    "analysis_repo",
    "ScenarioRepository",
    "scenario_repo",
]
