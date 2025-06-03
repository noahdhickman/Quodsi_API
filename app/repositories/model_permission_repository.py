# app/repositories/model_permission_repository.py
"""
Repository for managing model permissions with comprehensive query methods.

This repository provides specialized methods for permission management,
including permission checks, hierarchy resolution, and audit operations.
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, text
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from datetime import datetime, timezone

from app.repositories.base import BaseRepository
from app.db.models.model_permission import ModelPermission
from app.db.models.user import User
from app.db.models.organization import Organization
from app.db.models.team import Team
from app.schemas.model_permission import PermissionLevel


class ModelPermissionRepository(BaseRepository[ModelPermission]):
    """Repository for ModelPermission entities with permission-specific operations"""
    
    def __init__(self):
        super().__init__(ModelPermission)
    
    def get_user_permissions_for_model(
        self, 
        db: Session, 
        tenant_id: UUID, 
        user_id: UUID, 
        model_id: UUID
    ) -> List[ModelPermission]:
        """
        Get all effective permissions for a user on a specific model.
        
        Includes direct user permissions, organization permissions, and team permissions.
        """
        # For now, let's get user's organization IDs directly
        # TODO: This should be optimized with proper joins when organization membership is fully implemented
        from app.db.models.organization_membership import OrganizationMembership
        
        user_org_ids = db.query(OrganizationMembership.organization_id).filter(
            and_(
                OrganizationMembership.user_id == user_id,
                OrganizationMembership.status == "active",
                OrganizationMembership.is_deleted == False
            )
        ).all()
        
        # Extract the IDs from the result tuples
        org_ids = [org_id[0] for org_id in user_org_ids] if user_org_ids else []
        
        # Build the query conditions
        permission_conditions = [
            # Direct user permission
            ModelPermission.user_id == user_id
        ]
        
        # Add organization permissions if user belongs to any organizations
        if org_ids:
            permission_conditions.append(
                ModelPermission.organization_id.in_(org_ids)
            )
        
        # TODO: Add team permissions when team membership is implemented
        # For now, we'll skip team permissions
        
        return db.query(ModelPermission).filter(
            and_(
                ModelPermission.tenant_id == tenant_id,
                ModelPermission.model_id == model_id,
                ModelPermission.is_active == True,
                ModelPermission.is_deleted == False,
                # Date validity check
                or_(
                    ModelPermission.valid_from.is_(None),
                    ModelPermission.valid_from <= datetime.now(timezone.utc)
                ),
                or_(
                    ModelPermission.valid_until.is_(None),
                    ModelPermission.valid_until > datetime.now(timezone.utc)
                ),
                # Permission target conditions
                or_(*permission_conditions)
            )
        ).options(
            joinedload(ModelPermission.target_user),
            joinedload(ModelPermission.target_organization),
            joinedload(ModelPermission.target_team),
            joinedload(ModelPermission.granted_by),
            joinedload(ModelPermission.revoked_by)
        ).all()
    
    def check_user_permission(
        self, 
        db: Session, 
        tenant_id: UUID, 
        user_id: UUID, 
        model_id: UUID, 
        required_level: PermissionLevel
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user has required permission level for a model.
        
        Returns:
            tuple: (has_permission, permission_source)
        """
        permissions = self.get_user_permissions_for_model(db, tenant_id, user_id, model_id)
        
        # Define permission hierarchy
        permission_hierarchy = {
            PermissionLevel.READ: 1,
            PermissionLevel.WRITE: 2,
            PermissionLevel.EXECUTE: 3,
            PermissionLevel.ADMIN: 4
        }
        
        required_rank = permission_hierarchy.get(required_level, 0)
        highest_rank = 0
        permission_source = None
        
        for permission in permissions:
            perm_rank = permission_hierarchy.get(permission.permission_level, 0)
            if perm_rank >= required_rank and perm_rank > highest_rank:
                highest_rank = perm_rank
                if permission.user_id:
                    permission_source = "direct"
                elif permission.organization_id:
                    permission_source = "organization"
                elif permission.team_id:
                    permission_source = "team"
        
        return highest_rank >= required_rank, permission_source
    
    def get_permissions_by_model(
        self, 
        db: Session, 
        tenant_id: UUID, 
        model_id: UUID, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[ModelPermission]:
        """Get all permissions for a specific model"""
        query = db.query(ModelPermission).filter(
            and_(
                ModelPermission.tenant_id == tenant_id,
                ModelPermission.model_id == model_id,
                ModelPermission.is_deleted == False
            )
        )
        
        if not include_inactive:
            query = query.filter(ModelPermission.is_active == True)
        
        return query.options(
            joinedload(ModelPermission.target_user),
            joinedload(ModelPermission.target_organization),
            joinedload(ModelPermission.target_team),
            joinedload(ModelPermission.granted_by)
        ).order_by(
            ModelPermission.granted_at.desc()
        ).offset(skip).limit(limit).all()
    
    def get_permissions_by_user(
        self, 
        db: Session, 
        tenant_id: UUID, 
        user_id: UUID, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ModelPermission]:
        """Get all direct permissions granted to a specific user"""
        return db.query(ModelPermission).filter(
            and_(
                ModelPermission.tenant_id == tenant_id,
                ModelPermission.user_id == user_id,
                ModelPermission.is_active == True,
                ModelPermission.is_deleted == False
            )
        ).options(
            joinedload(ModelPermission.model),
            joinedload(ModelPermission.granted_by)
        ).order_by(
            ModelPermission.granted_at.desc()
        ).offset(skip).limit(limit).all()
    
    def get_permissions_by_organization(
        self, 
        db: Session, 
        tenant_id: UUID, 
        organization_id: UUID, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ModelPermission]:
        """Get all permissions granted to a specific organization"""
        return db.query(ModelPermission).filter(
            and_(
                ModelPermission.tenant_id == tenant_id,
                ModelPermission.organization_id == organization_id,
                ModelPermission.is_active == True,
                ModelPermission.is_deleted == False
            )
        ).options(
            joinedload(ModelPermission.model),
            joinedload(ModelPermission.granted_by)
        ).order_by(
            ModelPermission.granted_at.desc()
        ).offset(skip).limit(limit).all()
    
    def get_permissions_by_team(
        self, 
        db: Session, 
        tenant_id: UUID, 
        team_id: UUID, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ModelPermission]:
        """Get all permissions granted to a specific team"""
        return db.query(ModelPermission).filter(
            and_(
                ModelPermission.tenant_id == tenant_id,
                ModelPermission.team_id == team_id,
                ModelPermission.is_active == True,
                ModelPermission.is_deleted == False
            )
        ).options(
            joinedload(ModelPermission.model),
            joinedload(ModelPermission.granted_by)
        ).order_by(
            ModelPermission.granted_at.desc()
        ).offset(skip).limit(limit).all()
    
    def grant_permission(
        self, 
        db: Session, 
        *, 
        tenant_id: UUID,
        model_id: UUID,
        permission_level: PermissionLevel,
        granted_by_user_id: UUID,
        user_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        team_id: Optional[UUID] = None,
        valid_from: Optional[datetime] = None,
        valid_until: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> ModelPermission:
        """
        Grant a permission with proper validation.
        
        Ensures exactly one target is specified and handles the audit trail.
        """
        # Validate exactly one target
        targets = [user_id, organization_id, team_id]
        non_none_targets = [t for t in targets if t is not None]
        
        if len(non_none_targets) != 1:
            raise ValueError("Exactly one of user_id, organization_id, or team_id must be specified")
        
        # Create permission data
        permission_data = {
            "model_id": model_id,
            "permission_level": permission_level.value,
            "granted_by_user_id": granted_by_user_id,
            "granted_at": datetime.now(timezone.utc),
            "is_active": True,
            "user_id": user_id,
            "organization_id": organization_id,
            "team_id": team_id,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "notes": notes
        }
        
        return self.create(db, obj_in=permission_data, tenant_id=tenant_id)
    
    def revoke_permission(
        self, 
        db: Session, 
        tenant_id: UUID, 
        permission_id: UUID, 
        revoked_by_user_id: UUID,
        revocation_reason: Optional[str] = None
    ) -> Optional[ModelPermission]:
        """
        Revoke a permission by setting is_active=False and recording revocation info.
        """
        permission = self.get_by_id(db, tenant_id, permission_id)
        if not permission:
            return None
        
        # Update permission with revocation info
        revocation_data = {
            "is_active": False,
            "revoked_by_user_id": revoked_by_user_id,
            "revoked_at": datetime.now(timezone.utc),
            "notes": f"{permission.notes or ''}\nRevoked: {revocation_reason or 'No reason provided'}"
        }
        
        return self.update(db, db_obj=permission, obj_in=revocation_data)
    
    def bulk_revoke_permissions(
        self, 
        db: Session, 
        tenant_id: UUID, 
        permission_ids: List[UUID], 
        revoked_by_user_id: UUID,
        revocation_reason: Optional[str] = None
    ) -> tuple[List[UUID], List[Dict[str, Any]]]:
        """
        Revoke multiple permissions in bulk.
        
        Returns:
            tuple: (successful_ids, failed_operations)
        """
        successful_ids = []
        failed_operations = []
        
        for permission_id in permission_ids:
            try:
                permission = self.revoke_permission(
                    db, tenant_id, permission_id, revoked_by_user_id, revocation_reason
                )
                if permission:
                    successful_ids.append(permission_id)
                else:
                    failed_operations.append({
                        "id": permission_id,
                        "error": "Permission not found"
                    })
            except Exception as e:
                failed_operations.append({
                    "id": permission_id,
                    "error": str(e)
                })
        
        return successful_ids, failed_operations
    
    def get_expiring_permissions(
        self, 
        db: Session, 
        tenant_id: UUID, 
        days_ahead: int = 7
    ) -> List[ModelPermission]:
        """Get permissions that will expire within the specified number of days"""
        from datetime import timedelta
        
        expiry_threshold = datetime.now(timezone.utc) + timedelta(days=days_ahead)
        
        return db.query(ModelPermission).filter(
            and_(
                ModelPermission.tenant_id == tenant_id,
                ModelPermission.is_active == True,
                ModelPermission.is_deleted == False,
                ModelPermission.valid_until.isnot(None),
                ModelPermission.valid_until <= expiry_threshold,
                ModelPermission.valid_until > datetime.now(timezone.utc)
            )
        ).options(
            joinedload(ModelPermission.model),
            joinedload(ModelPermission.target_user),
            joinedload(ModelPermission.target_organization),
            joinedload(ModelPermission.target_team)
        ).order_by(ModelPermission.valid_until).all()
    
    def get_permission_statistics(
        self, 
        db: Session, 
        tenant_id: UUID, 
        model_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get statistics about permissions for a model or tenant"""
        base_query = db.query(ModelPermission).filter(
            and_(
                ModelPermission.tenant_id == tenant_id,
                ModelPermission.is_deleted == False
            )
        )
        
        if model_id:
            base_query = base_query.filter(ModelPermission.model_id == model_id)
        
        # Get various statistics
        total_permissions = base_query.count()
        active_permissions = base_query.filter(ModelPermission.is_active == True).count()
        revoked_permissions = base_query.filter(ModelPermission.is_active == False).count()
        
        # Permission level distribution
        level_distribution = {}
        for level in PermissionLevel:
            count = base_query.filter(
                and_(
                    ModelPermission.permission_level == level.value,
                    ModelPermission.is_active == True
                )
            ).count()
            level_distribution[level.value] = count
        
        # Target type distribution
        user_permissions = base_query.filter(
            and_(
                ModelPermission.user_id.isnot(None),
                ModelPermission.is_active == True
            )
        ).count()
        
        org_permissions = base_query.filter(
            and_(
                ModelPermission.organization_id.isnot(None),
                ModelPermission.is_active == True
            )
        ).count()
        
        team_permissions = base_query.filter(
            and_(
                ModelPermission.team_id.isnot(None),
                ModelPermission.is_active == True
            )
        ).count()
        
        return {
            "total_permissions": total_permissions,
            "active_permissions": active_permissions,
            "revoked_permissions": revoked_permissions,
            "permission_level_distribution": level_distribution,
            "target_type_distribution": {
                "user": user_permissions,
                "organization": org_permissions,
                "team": team_permissions
            }
        }
    
    def cleanup_expired_permissions(
        self, 
        db: Session, 
        tenant_id: UUID
    ) -> int:
        """
        Deactivate permissions that have passed their valid_until date.
        
        Returns:
            Number of permissions deactivated
        """
        expired_permissions = db.query(ModelPermission).filter(
            and_(
                ModelPermission.tenant_id == tenant_id,
                ModelPermission.is_active == True,
                ModelPermission.is_deleted == False,
                ModelPermission.valid_until.isnot(None),
                ModelPermission.valid_until <= datetime.now(timezone.utc)
            )
        ).all()
        
        count = 0
        for permission in expired_permissions:
            permission.is_active = False
            permission.updated_at = datetime.now(timezone.utc)
            db.add(permission)
            count += 1
        
        if count > 0:
            db.flush()
        
        return count