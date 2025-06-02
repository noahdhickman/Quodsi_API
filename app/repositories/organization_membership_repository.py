from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone, timedelta

from app.repositories.base import BaseRepository
from app.db.models.organization_membership import OrganizationMembership
from app.db.models.organization import Organization
from app.db.models.user import User


class OrganizationMembershipRepository(BaseRepository[OrganizationMembership]):
    """
    Repository for organization membership operations.
    
    Handles user-organization relationships including invitations,
    role management, and membership lifecycle operations.
    """
    
    def __init__(self):
        super().__init__(OrganizationMembership)
    
    # === Core Membership Operations ===
    
    def add_member(
        self, 
        db: Session, 
        tenant_id: UUID, 
        organization_id: UUID, 
        user_id: UUID, 
        role: str, 
        invited_by_user_id: Optional[UUID] = None,
        status: str = "active"
    ) -> OrganizationMembership:
        """
        Add a user to an organization with specified role.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            organization_id: Organization UUID
            user_id: User UUID to add
            role: Role to assign (owner, admin, member, viewer)
            invited_by_user_id: User who sent invitation (optional)
            status: Membership status (default: active)
            
        Returns:
            Created membership record
            
        Raises:
            ValueError: If membership already exists
        """
        # Check if membership already exists
        existing = self.get_membership(db, tenant_id, organization_id, user_id)
        if existing and not existing.is_deleted:
            raise ValueError("User is already a member of this organization")
        
        # Prepare membership data
        membership_data = {
            "organization_id": organization_id,
            "user_id": user_id,
            "role": role,
            "status": status,
            "invited_by_user_id": invited_by_user_id,
            "last_active_at": datetime.now(timezone.utc) if status == "active" else None
        }
        
        return self.create(db=db, obj_in=membership_data, tenant_id=tenant_id)
    
    def get_membership(
        self, 
        db: Session, 
        tenant_id: UUID, 
        organization_id: UUID, 
        user_id: UUID
    ) -> Optional[OrganizationMembership]:
        """
        Get membership record for specific user and organization.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            organization_id: Organization UUID
            user_id: User UUID
            
        Returns:
            Membership record or None if not found
        """
        return db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.organization_id == organization_id,
                self.model.user_id == user_id,
                self.model.is_deleted == False
            )
        ).first()
    
    def get_membership_by_id(
        self, 
        db: Session, 
        tenant_id: UUID, 
        membership_id: UUID
    ) -> Optional[OrganizationMembership]:
        """
        Get membership by ID with tenant isolation.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            membership_id: Membership UUID
            
        Returns:
            Membership record or None if not found
        """
        return self.get_by_id(db, tenant_id, membership_id)
    
    def update_member_role_or_status(
        self, 
        db: Session, 
        membership_id: UUID, 
        tenant_id: UUID, 
        new_role: Optional[str] = None,
        new_status: Optional[str] = None
    ) -> Optional[OrganizationMembership]:
        """
        Update member role or status.
        
        Args:
            db: Database session
            membership_id: Membership UUID to update
            tenant_id: Tenant UUID for isolation
            new_role: New role to assign (optional)
            new_status: New status to assign (optional)
            
        Returns:
            Updated membership record or None if not found
        """
        membership = self.get_by_id(db, tenant_id, membership_id)
        if not membership:
            return None
        
        update_data = {}
        if new_role:
            update_data["role"] = new_role
        if new_status:
            update_data["status"] = new_status
        
        # Update last active if becoming active
        if new_status == "active":
            update_data["last_active_at"] = datetime.now(timezone.utc)
        
        return self.update(db=db, db_obj=membership, obj_in=update_data)
    
    def remove_member(
        self, 
        db: Session, 
        membership_id: UUID, 
        tenant_id: UUID
    ) -> bool:
        """
        Remove member from organization (soft delete).
        
        Args:
            db: Database session
            membership_id: Membership UUID to remove
            tenant_id: Tenant UUID for isolation
            
        Returns:
            True if removed successfully, False if not found
        """
        membership = self.get_by_id(db, tenant_id, membership_id)
        if membership:
            # Update status to 'left' before soft deleting
            self.update(db=db, db_obj=membership, obj_in={"status": "left"})
            return self.soft_delete(db, tenant_id, membership_id)
        return False
    
    # === Organization-focused queries ===
    
    def get_members_of_organization(
        self, 
        db: Session, 
        tenant_id: UUID, 
        organization_id: UUID, 
        skip: int = 0, 
        limit: int = 100,
        status_filter: Optional[str] = None,
        role_filter: Optional[str] = None,
        include_user_details: bool = True
    ) -> List[OrganizationMembership]:
        """
        Get members of a specific organization.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            organization_id: Organization UUID
            skip: Pagination offset
            limit: Maximum results
            status_filter: Filter by status (optional)
            role_filter: Filter by role (optional)
            include_user_details: Whether to include user details
            
        Returns:
            List of membership records
        """
        query = db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.organization_id == organization_id,
                self.model.is_deleted == False
            )
        )
        
        # Apply filters
        if status_filter:
            query = query.filter(self.model.status == status_filter)
        if role_filter:
            query = query.filter(self.model.role == role_filter)
        
        # Include user details if requested
        if include_user_details:
            query = query.options(joinedload(self.model.user))
        
        return query.order_by(self.model.created_at).offset(skip).limit(limit).all()
    
    def get_organization_owners(
        self, 
        db: Session, 
        tenant_id: UUID, 
        organization_id: UUID
    ) -> List[OrganizationMembership]:
        """
        Get all owners of an organization.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            organization_id: Organization UUID
            
        Returns:
            List of owner memberships
        """
        return db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.organization_id == organization_id,
                self.model.role == "owner",
                self.model.status == "active",
                self.model.is_deleted == False
            )
        ).all()
    
    def count_organization_members(
        self, 
        db: Session, 
        tenant_id: UUID, 
        organization_id: UUID,
        status_filter: Optional[str] = "active"
    ) -> int:
        """
        Count members in an organization.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            organization_id: Organization UUID
            status_filter: Status filter (default: active)
            
        Returns:
            Number of members
        """
        query = db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.organization_id == organization_id,
                self.model.is_deleted == False
            )
        )
        
        if status_filter:
            query = query.filter(self.model.status == status_filter)
        
        return query.count()
    
    def get_organization_member_counts_by_role(
        self, 
        db: Session, 
        tenant_id: UUID, 
        organization_id: UUID
    ) -> Dict[str, int]:
        """
        Get member counts grouped by role.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            organization_id: Organization UUID
            
        Returns:
            Dictionary with role counts
        """
        result = db.query(
            self.model.role,
            func.count(self.model.id).label('count')
        ).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.organization_id == organization_id,
                self.model.status == "active",
                self.model.is_deleted == False
            )
        ).group_by(self.model.role).all()
        
        # Convert to dictionary with default values
        role_counts = {"owner": 0, "admin": 0, "member": 0, "viewer": 0}
        for role, count in result:
            role_counts[role] = count
        
        return role_counts
    
    # === User-focused queries ===
    
    def get_organizations_for_user(
        self, 
        db: Session, 
        tenant_id: UUID, 
        user_id: UUID, 
        skip: int = 0, 
        limit: int = 100,
        status_filter: Optional[str] = "active",
        include_organization_details: bool = True
    ) -> List[OrganizationMembership]:
        """
        Get organizations that a user belongs to.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            user_id: User UUID
            skip: Pagination offset
            limit: Maximum results
            status_filter: Filter by membership status
            include_organization_details: Whether to include organization details
            
        Returns:
            List of membership records with organization details
        """
        query = db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.user_id == user_id,
                self.model.is_deleted == False
            )
        )
        
        if status_filter:
            query = query.filter(self.model.status == status_filter)
        
        if include_organization_details:
            query = query.options(joinedload(self.model.organization))
        
        return query.order_by(self.model.created_at).offset(skip).limit(limit).all()
    
    def get_user_role_in_organization(
        self, 
        db: Session, 
        tenant_id: UUID, 
        user_id: UUID, 
        organization_id: UUID
    ) -> Optional[str]:
        """
        Get user's role in a specific organization.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            user_id: User UUID
            organization_id: Organization UUID
            
        Returns:
            User's role or None if not a member
        """
        membership = self.get_membership(db, tenant_id, organization_id, user_id)
        return membership.role if membership and membership.is_active() else None
    
    def user_has_permission(
        self, 
        db: Session, 
        tenant_id: UUID, 
        user_id: UUID, 
        organization_id: UUID,
        required_roles: List[str]
    ) -> bool:
        """
        Check if user has required role in organization.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            user_id: User UUID
            organization_id: Organization UUID
            required_roles: List of acceptable roles
            
        Returns:
            True if user has required permission
        """
        user_role = self.get_user_role_in_organization(
            db, tenant_id, user_id, organization_id
        )
        return user_role in required_roles if user_role else False
    
    # === Invitation management ===
    
    def get_pending_invitations(
        self, 
        db: Session, 
        tenant_id: UUID, 
        user_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[OrganizationMembership]:
        """
        Get pending invitations.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            user_id: Filter by user (optional)
            organization_id: Filter by organization (optional)
            skip: Pagination offset
            limit: Maximum results
            
        Returns:
            List of pending invitation memberships
        """
        query = db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.status == "invited",
                self.model.is_deleted == False
            )
        )
        
        if user_id:
            query = query.filter(self.model.user_id == user_id)
        if organization_id:
            query = query.filter(self.model.organization_id == organization_id)
        
        query = query.options(
            joinedload(self.model.organization),
            joinedload(self.model.user),
            joinedload(self.model.invited_by)
        )
        
        return query.order_by(desc(self.model.created_at)).offset(skip).limit(limit).all()
    
    def accept_invitation(
        self, 
        db: Session, 
        tenant_id: UUID, 
        membership_id: UUID
    ) -> Optional[OrganizationMembership]:
        """
        Accept a pending invitation.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            membership_id: Membership UUID
            
        Returns:
            Updated membership or None if not found/invalid
        """
        membership = self.get_by_id(db, tenant_id, membership_id)
        if membership and membership.status == "invited":
            update_data = {
                "status": "active",
                "last_active_at": datetime.now(timezone.utc)
            }
            return self.update(db=db, db_obj=membership, obj_in=update_data)
        return None
    
    def decline_invitation(
        self, 
        db: Session, 
        tenant_id: UUID, 
        membership_id: UUID
    ) -> bool:
        """
        Decline a pending invitation (soft delete).
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            membership_id: Membership UUID
            
        Returns:
            True if declined successfully
        """
        membership = self.get_by_id(db, tenant_id, membership_id)
        if membership and membership.status == "invited":
            # Mark as left before soft deleting
            self.update(db=db, db_obj=membership, obj_in={"status": "left"})
            return self.soft_delete(db, tenant_id, membership_id)
        return False
    
    # === Analytics and reporting ===
    
    def get_recent_members(
        self, 
        db: Session, 
        tenant_id: UUID, 
        organization_id: Optional[UUID] = None,
        days: int = 30, 
        limit: int = 100
    ) -> List[OrganizationMembership]:
        """
        Get recently added members.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            organization_id: Filter by organization (optional)
            days: Number of days back to search
            limit: Maximum results
            
        Returns:
            List of recent memberships
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        query = db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.created_at >= cutoff_date,
                self.model.is_deleted == False
            )
        )
        
        if organization_id:
            query = query.filter(self.model.organization_id == organization_id)
        
        return query.options(
            joinedload(self.model.user),
            joinedload(self.model.organization)
        ).order_by(desc(self.model.created_at)).limit(limit).all()
    
    def get_membership_statistics(
        self, 
        db: Session, 
        tenant_id: UUID, 
        organization_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get membership statistics.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            organization_id: Filter by organization (optional)
            
        Returns:
            Dictionary with membership statistics
        """
        base_filter = and_(
            self.model.tenant_id == tenant_id,
            self.model.is_deleted == False
        )
        
        if organization_id:
            base_filter = and_(base_filter, self.model.organization_id == organization_id)
        
        # Total memberships
        total = db.query(self.model).filter(base_filter).count()
        
        # Active memberships
        active = db.query(self.model).filter(
            and_(base_filter, self.model.status == "active")
        ).count()
        
        # Pending invitations
        pending = db.query(self.model).filter(
            and_(base_filter, self.model.status == "invited")
        ).count()
        
        return {
            "total_memberships": total,
            "active_memberships": active,
            "pending_invitations": pending,
            "suspended_memberships": total - active - pending
        }