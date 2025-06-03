# app/services/model_permission_service.py
"""
Service layer for model permission management with comprehensive business logic.

This service handles permission granting, revocation, checking, and audit operations
with proper validation, security controls, and business rule enforcement.
"""
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timezone

from app.repositories.model_permission_repository import ModelPermissionRepository
from app.repositories.model_access_log_repository import ModelAccessLogRepository
from app.repositories.model_repository import ModelRepository
from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository
from app.db.models.model_permission import ModelPermission
from app.db.models.model_access_log import ModelAccessLog
from app.schemas.model_permission import (
    PermissionLevel, PermissionTargetType, ModelPermissionCreate, 
    ModelPermissionUpdate, ModelPermissionRead, ModelPermissionResult,
    PermissionGrantRequest, PermissionRevokeRequest, BulkPermissionResponse
)
from app.schemas.model_access_log import AccessType, AccessResult, ModelAccessLogCreate
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ModelPermissionService:
    """Service for managing model permissions with comprehensive business logic"""
    
    def __init__(self):
        self.permission_repo = ModelPermissionRepository()
        self.access_log_repo = ModelAccessLogRepository()
        self.model_repo = ModelRepository()
        self.user_repo = UserRepository()
        self.org_repo = OrganizationRepository()
    
    async def check_user_permission(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        model_id: UUID,
        required_level: PermissionLevel,
        log_access: bool = True,
        session_context: Optional[Dict[str, Any]] = None
    ) -> ModelPermissionResult:
        """
        Check if user has required permission level for a model with comprehensive result.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            user_id: User requesting access
            model_id: Model being accessed
            required_level: Required permission level
            log_access: Whether to log this permission check
            session_context: Additional context for logging (IP, user agent, etc.)
        
        Returns:
            ModelPermissionResult with detailed permission information
        """
        try:
            # Get all effective permissions for the user
            permissions = self.permission_repo.get_user_permissions_for_model(
                db, tenant_id, user_id, model_id
            )
            
            # Check permission using repository method
            has_permission, permission_source = self.permission_repo.check_user_permission(
                db, tenant_id, user_id, model_id, required_level
            )
            
            # Build permission result
            permission_sources = {}
            highest_level = None
            can_read = can_write = can_execute = can_admin = False
            
            # Analyze all permissions to build comprehensive result
            permission_hierarchy = {
                PermissionLevel.READ: 1,
                PermissionLevel.WRITE: 2,
                PermissionLevel.EXECUTE: 3,
                PermissionLevel.ADMIN: 4
            }
            
            highest_rank = 0
            for permission in permissions:
                perm_rank = permission_hierarchy.get(permission.permission_level, 0)
                if perm_rank > highest_rank:
                    highest_rank = perm_rank
                    highest_level = permission.permission_level
                
                # Determine source for each permission level
                source = "direct" if permission.user_id else ("organization" if permission.organization_id else "team")
                
                # Set capabilities based on permission level
                if permission.permission_level == PermissionLevel.READ and perm_rank >= 1:
                    can_read = True
                    permission_sources["read"] = source
                if permission.permission_level in [PermissionLevel.WRITE, PermissionLevel.EXECUTE, PermissionLevel.ADMIN] and perm_rank >= 2:
                    can_read = can_write = True
                    permission_sources["read"] = permission_sources["write"] = source
                if permission.permission_level in [PermissionLevel.EXECUTE, PermissionLevel.ADMIN] and perm_rank >= 3:
                    can_read = can_write = can_execute = True
                    permission_sources["read"] = permission_sources["write"] = permission_sources["execute"] = source
                if permission.permission_level == PermissionLevel.ADMIN and perm_rank >= 4:
                    can_read = can_write = can_execute = can_admin = True
                    permission_sources["read"] = permission_sources["write"] = permission_sources["execute"] = permission_sources["admin"] = source
            
            result = ModelPermissionResult(
                model_id=model_id,
                user_id=user_id,
                can_read=can_read,
                can_write=can_write,
                can_execute=can_execute,
                can_admin=can_admin,
                permission_sources=permission_sources,
                effective_permissions=[ModelPermissionRead.model_validate(p) for p in permissions],
                has_any_permission=len(permissions) > 0,
                highest_permission_level=highest_level
            )
            
            # Log the access attempt if requested
            if log_access:
                access_result = AccessResult.SUCCESS if has_permission else AccessResult.DENIED
                await self._log_permission_check(
                    db, tenant_id, user_id, model_id, required_level,
                    access_result, permission_source, session_context
                )
            
            logger.info(
                f"Permission check: user={user_id}, model={model_id}, "
                f"required={required_level.value}, granted={has_permission}, source={permission_source}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking user permission: {e}")
            
            # Log the error
            if log_access:
                await self._log_permission_check(
                    db, tenant_id, user_id, model_id, required_level,
                    AccessResult.ERROR, None, session_context, str(e)
                )
            
            # Return denied result on error
            return ModelPermissionResult(
                model_id=model_id,
                user_id=user_id,
                can_read=False,
                can_write=False,
                can_execute=False,
                can_admin=False,
                permission_sources={},
                effective_permissions=[],
                has_any_permission=False,
                highest_permission_level=None
            )
    
    async def grant_permission(
        self,
        db: Session,
        tenant_id: UUID,
        permission_data: ModelPermissionCreate,
        granted_by_user_id: UUID,
        session_context: Optional[Dict[str, Any]] = None
    ) -> ModelPermissionRead:
        """
        Grant a permission with validation and audit logging.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            permission_data: Permission creation data
            granted_by_user_id: User granting the permission
            session_context: Additional context for logging
        
        Returns:
            Created permission
        """
        try:
            # Validate the model exists and user has admin permission
            model = self.model_repo.get_by_id(db, tenant_id, permission_data.model_id)
            if not model:
                raise ValueError(f"Model {permission_data.model_id} not found")
            
            # Check if granting user has admin permission on the model
            granter_permission = await self.check_user_permission(
                db, tenant_id, granted_by_user_id, permission_data.model_id,
                PermissionLevel.ADMIN, log_access=False
            )
            
            if not granter_permission.can_admin:
                raise PermissionError("User does not have admin permission to grant access")
            
            # Validate target exists
            await self._validate_permission_target(db, tenant_id, permission_data)
            
            # Check for existing permission to avoid duplicates
            existing_permissions = self.permission_repo.get_user_permissions_for_model(
                db, tenant_id, permission_data.user_id or UUID('00000000-0000-0000-0000-000000000000'), 
                permission_data.model_id
            )
            
            # Filter for same target type and ID
            for existing in existing_permissions:
                if (
                    (permission_data.user_id and existing.user_id == permission_data.user_id) or
                    (permission_data.organization_id and existing.organization_id == permission_data.organization_id) or
                    (permission_data.team_id and existing.team_id == permission_data.team_id)
                ):
                    if existing.is_active and existing.permission_level == permission_data.permission_level:
                        logger.warning(f"Permission already exists: {existing.id}")
                        return ModelPermissionRead.model_validate(existing)
            
            # Create the permission
            permission = self.permission_repo.grant_permission(
                db,
                tenant_id=tenant_id,
                model_id=permission_data.model_id,
                permission_level=permission_data.permission_level,
                granted_by_user_id=granted_by_user_id,
                user_id=permission_data.user_id,
                organization_id=permission_data.organization_id,
                team_id=permission_data.team_id,
                valid_from=permission_data.valid_from,
                valid_until=permission_data.valid_until,
                notes=permission_data.notes
            )
            
            # Log the permission grant
            await self._log_access(
                db, tenant_id, granted_by_user_id, permission_data.model_id,
                AccessType.PERMISSION_CHANGE, AccessResult.SUCCESS,
                "admin", session_context,
                {"action": "grant_permission", "permission_id": str(permission.id), "target_type": self._get_target_type(permission_data)}
            )
            
            logger.info(f"Permission granted: {permission.id} by user {granted_by_user_id}")
            
            return ModelPermissionRead.model_validate(permission)
            
        except Exception as e:
            logger.error(f"Error granting permission: {e}")
            
            # Log the failed attempt
            await self._log_access(
                db, tenant_id, granted_by_user_id, permission_data.model_id,
                AccessType.PERMISSION_CHANGE, AccessResult.ERROR,
                None, session_context,
                {"action": "grant_permission_failed", "error": str(e)}
            )
            
            raise
    
    async def revoke_permission(
        self,
        db: Session,
        tenant_id: UUID,
        permission_id: UUID,
        revoked_by_user_id: UUID,
        revocation_reason: Optional[str] = None,
        session_context: Optional[Dict[str, Any]] = None
    ) -> Optional[ModelPermissionRead]:
        """
        Revoke a permission with validation and audit logging.
        """
        try:
            # Get the permission to revoke
            permission = self.permission_repo.get_by_id(db, tenant_id, permission_id)
            if not permission:
                raise ValueError(f"Permission {permission_id} not found")
            
            # Check if revoking user has admin permission on the model
            revoker_permission = await self.check_user_permission(
                db, tenant_id, revoked_by_user_id, permission.model_id,
                PermissionLevel.ADMIN, log_access=False
            )
            
            if not revoker_permission.can_admin:
                raise PermissionError("User does not have admin permission to revoke access")
            
            # Revoke the permission
            revoked_permission = self.permission_repo.revoke_permission(
                db, tenant_id, permission_id, revoked_by_user_id, revocation_reason
            )
            
            if revoked_permission:
                # Log the permission revocation
                await self._log_access(
                    db, tenant_id, revoked_by_user_id, permission.model_id,
                    AccessType.PERMISSION_CHANGE, AccessResult.SUCCESS,
                    "admin", session_context,
                    {"action": "revoke_permission", "permission_id": str(permission_id), "reason": revocation_reason}
                )
                
                logger.info(f"Permission revoked: {permission_id} by user {revoked_by_user_id}")
                
                return ModelPermissionRead.model_validate(revoked_permission)
            
            return None
            
        except Exception as e:
            logger.error(f"Error revoking permission: {e}")
            
            # Log the failed attempt
            if permission:
                await self._log_access(
                    db, tenant_id, revoked_by_user_id, permission.model_id,
                    AccessType.PERMISSION_CHANGE, AccessResult.ERROR,
                    None, session_context,
                    {"action": "revoke_permission_failed", "permission_id": str(permission_id), "error": str(e)}
                )
            
            raise
    
    async def bulk_grant_permissions(
        self,
        db: Session,
        tenant_id: UUID,
        grant_request: PermissionGrantRequest,
        granted_by_user_id: UUID,
        session_context: Optional[Dict[str, Any]] = None
    ) -> BulkPermissionResponse:
        """
        Grant permissions to multiple targets in bulk.
        """
        successful_operations = []
        failed_operations = []
        
        # Collect all target IDs and types
        targets = []
        if grant_request.user_ids:
            targets.extend([("user", user_id) for user_id in grant_request.user_ids])
        if grant_request.organization_ids:
            targets.extend([("organization", org_id) for org_id in grant_request.organization_ids])
        if grant_request.team_ids:
            targets.extend([("team", team_id) for team_id in grant_request.team_ids])
        
        total_requested = len(targets)
        
        for target_type, target_id in targets:
            try:
                # Create permission data for this target
                permission_data = ModelPermissionCreate(
                    model_id=grant_request.model_id,
                    permission_level=grant_request.permission_level,
                    user_id=target_id if target_type == "user" else None,
                    organization_id=target_id if target_type == "organization" else None,
                    team_id=target_id if target_type == "team" else None,
                    valid_from=grant_request.valid_from,
                    valid_until=grant_request.valid_until,
                    notes=grant_request.notes
                )
                
                # Grant the permission
                permission = await self.grant_permission(
                    db, tenant_id, permission_data, granted_by_user_id, session_context
                )
                
                successful_operations.append(permission.id)
                
            except Exception as e:
                failed_operations.append({
                    "target_type": target_type,
                    "target_id": str(target_id),
                    "error": str(e)
                })
        
        return BulkPermissionResponse(
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            total_requested=total_requested,
            total_successful=len(successful_operations),
            total_failed=len(failed_operations)
        )
    
    async def bulk_revoke_permissions(
        self,
        db: Session,
        tenant_id: UUID,
        revoke_request: PermissionRevokeRequest,
        revoked_by_user_id: UUID,
        session_context: Optional[Dict[str, Any]] = None
    ) -> BulkPermissionResponse:
        """
        Revoke multiple permissions in bulk.
        """
        successful_operations = []
        failed_operations = []
        
        for permission_id in revoke_request.permission_ids:
            try:
                revoked_permission = await self.revoke_permission(
                    db, tenant_id, permission_id, revoked_by_user_id,
                    revoke_request.revocation_reason, session_context
                )
                
                if revoked_permission:
                    successful_operations.append(permission_id)
                else:
                    failed_operations.append({
                        "permission_id": str(permission_id),
                        "error": "Permission not found or already revoked"
                    })
                    
            except Exception as e:
                failed_operations.append({
                    "permission_id": str(permission_id),
                    "error": str(e)
                })
        
        return BulkPermissionResponse(
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            total_requested=len(revoke_request.permission_ids),
            total_successful=len(successful_operations),
            total_failed=len(failed_operations)
        )
    
    def get_model_permissions(
        self,
        db: Session,
        tenant_id: UUID,
        model_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[ModelPermissionRead]:
        """Get all permissions for a specific model."""
        permissions = self.permission_repo.get_permissions_by_model(
            db, tenant_id, model_id, skip=skip, limit=limit, include_inactive=include_inactive
        )
        return [ModelPermissionRead.model_validate(p) for p in permissions]
    
    def get_user_permissions(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelPermissionRead]:
        """Get all permissions granted to a specific user."""
        permissions = self.permission_repo.get_permissions_by_user(
            db, tenant_id, user_id, skip=skip, limit=limit
        )
        return [ModelPermissionRead.model_validate(p) for p in permissions]
    
    def get_permission_statistics(
        self,
        db: Session,
        tenant_id: UUID,
        model_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get permission statistics for a model or tenant."""
        return self.permission_repo.get_permission_statistics(db, tenant_id, model_id)
    
    def get_expiring_permissions(
        self,
        db: Session,
        tenant_id: UUID,
        days_ahead: int = 7
    ) -> List[ModelPermissionRead]:
        """Get permissions that will expire soon."""
        permissions = self.permission_repo.get_expiring_permissions(db, tenant_id, days_ahead)
        return [ModelPermissionRead.model_validate(p) for p in permissions]
    
    async def cleanup_expired_permissions(
        self,
        db: Session,
        tenant_id: UUID
    ) -> int:
        """Clean up expired permissions and return count of deactivated permissions."""
        count = self.permission_repo.cleanup_expired_permissions(db, tenant_id)
        
        if count > 0:
            logger.info(f"Cleaned up {count} expired permissions for tenant {tenant_id}")
        
        return count
    
    # Private helper methods
    
    async def _validate_permission_target(
        self,
        db: Session,
        tenant_id: UUID,
        permission_data: ModelPermissionCreate
    ) -> None:
        """Validate that the permission target exists."""
        if permission_data.user_id:
            user = self.user_repo.get_by_id(db, tenant_id, permission_data.user_id)
            if not user:
                raise ValueError(f"User {permission_data.user_id} not found")
        
        elif permission_data.organization_id:
            org = self.org_repo.get_by_id(db, tenant_id, permission_data.organization_id)
            if not org:
                raise ValueError(f"Organization {permission_data.organization_id} not found")
        
        elif permission_data.team_id:
            # Note: Assuming team repository would be available
            # For now, we'll skip team validation
            pass
    
    def _get_target_type(self, permission_data: ModelPermissionCreate) -> str:
        """Get the target type from permission data."""
        if permission_data.user_id:
            return "user"
        elif permission_data.organization_id:
            return "organization"
        elif permission_data.team_id:
            return "team"
        return "unknown"
    
    async def _log_permission_check(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        model_id: UUID,
        required_level: PermissionLevel,
        access_result: AccessResult,
        permission_source: Optional[str],
        session_context: Optional[Dict[str, Any]],
        error_details: Optional[str] = None
    ) -> None:
        """Log a permission check operation."""
        details = {
            "required_permission_level": required_level.value,
            "permission_source": permission_source
        }
        
        if error_details:
            details["error"] = error_details
        
        await self._log_access(
            db, tenant_id, user_id, model_id,
            AccessType.READ, access_result, permission_source,
            session_context, details
        )
    
    async def _log_access(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        model_id: UUID,
        access_type: AccessType,
        access_result: AccessResult,
        permission_source: Optional[str],
        session_context: Optional[Dict[str, Any]],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an access event."""
        try:
            details = additional_details or {}
            
            # Extract session context
            session_id = session_context.get("session_id") if session_context else None
            ip_address = session_context.get("ip_address") if session_context else None
            user_agent = session_context.get("user_agent") if session_context else None
            endpoint = session_context.get("endpoint") if session_context else None
            request_method = session_context.get("request_method") if session_context else None
            
            self.access_log_repo.log_access(
                db,
                tenant_id=tenant_id,
                model_id=model_id,
                user_id=user_id,
                access_type=access_type,
                access_result=access_result,
                permission_source=permission_source,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                endpoint=endpoint,
                request_method=request_method,
                details=details
            )
            
        except Exception as e:
            # Don't let logging errors break the main flow
            logger.error(f"Failed to log access event: {e}")


# Dependency injection function
def get_model_permission_service() -> ModelPermissionService:
    """Get ModelPermissionService instance for dependency injection."""
    return ModelPermissionService()