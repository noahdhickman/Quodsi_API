from sqlalchemy import (
    Column, String, DateTime, Index, CheckConstraint, 
    ForeignKey, UniqueConstraint, text as sa_text
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime, timezone
from app.db.models.base_entity import BaseEntity


class OrganizationMembership(BaseEntity):
    """
    Organization membership model linking users to organizations with roles.
    
    Represents user membership within organizations, including their role,
    status (active/invited/suspended), and audit information.
    """
    
    __tablename__ = "organization_memberships"
    
    # Foreign key to organizations table
    organization_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("organizations.id", name="fk_organization_memberships_organization"),
        nullable=False,
        index=True,
        comment="Organization this membership belongs to"
    )
    
    # Foreign key to users table
    user_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("users.id", name="fk_organization_memberships_user"),
        nullable=False,
        index=True,
        comment="User who is a member of the organization"
    )
    
    # User role within the organization
    role = Column(
        String(50),
        nullable=False,
        default="member",
        comment="User role: owner, admin, member, viewer"
    )
    
    # Who invited this user (nullable for owners/initial members)
    invited_by_user_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("users.id", name="fk_organization_memberships_invited_by"),
        nullable=True,
        comment="User who invited this member"
    )
    
    # Membership status
    status = Column(
        String(20),
        nullable=False,
        default="active",
        comment="Membership status: active, invited, suspended, left"
    )
    
    # Last activity timestamp for analytics
    last_active_at = Column(
        DateTime,
        nullable=True,
        comment="When the user was last active in this organization"
    )
    
    # Relationships
    organization = relationship("Organization", back_populates="memberships")
    user = relationship("User", foreign_keys=[user_id], back_populates="organization_memberships")
    invited_by = relationship("User", foreign_keys=[invited_by_user_id])
    
    @declared_attr
    def __table_args__(cls):
        """
        Define organization membership-specific indexes and constraints.
        Extends BaseEntity's table args with membership-specific requirements.
        """
        # Get base table args from BaseEntity
        base_args = list(super().__table_args__)
        
        # Add membership-specific constraints and indexes
        membership_args = [
            # Unique constraint: one active membership per user per organization per tenant
            UniqueConstraint(
                "tenant_id", "organization_id", "user_id",
                name="uq_organization_memberships_tenant_org_user"
            ),
            
            # Check constraint for valid roles
            CheckConstraint(
                "role IN ('owner', 'admin', 'member', 'viewer')",
                name="ck_organization_memberships_role"
            ),
            
            # Check constraint for valid statuses
            CheckConstraint(
                "status IN ('active', 'invited', 'suspended', 'left')",
                name="ck_organization_memberships_status"
            ),
            
            # Note: Tenant consistency enforced by application logic rather than DB constraint
            # SQL Server doesn't support subqueries in CHECK constraints
            
            # Index for finding members of an organization
            Index(
                "ix_organization_memberships_org_active",
                "tenant_id", "organization_id", "status",
                mssql_where=sa_text("is_deleted = 0 AND status = 'active'")
            ),
            
            # Index for finding user's organizations
            Index(
                "ix_organization_memberships_user_active", 
                "tenant_id", "user_id", "status",
                mssql_where=sa_text("is_deleted = 0 AND status = 'active'")
            ),
            
            # Index for role-based queries
            Index(
                "ix_organization_memberships_role_lookup",
                "tenant_id", "organization_id", "role",
                mssql_where=sa_text("is_deleted = 0 AND status = 'active'")
            ),
            
            # Index for invitation management
            Index(
                "ix_organization_memberships_invitations",
                "tenant_id", "status", "created_at",
                mssql_where=sa_text("is_deleted = 0 AND status = 'invited'")
            ),
        ]
        
        return tuple(base_args + membership_args)
    
    def __repr__(self):
        """String representation for debugging"""
        return (
            f"<OrganizationMembership("
            f"id={self.id}, "
            f"tenant_id={self.tenant_id}, "
            f"user_id={self.user_id}, "
            f"organization_id={self.organization_id}, "
            f"role='{self.role}', "
            f"status='{self.status}'"
            f")>"
        )
    
    def is_active(self) -> bool:
        """Check if membership is active"""
        return self.status == "active" and not self.is_deleted
    
    def is_owner(self) -> bool:
        """Check if user is an owner of the organization"""
        return self.role == "owner" and self.is_active()
    
    def is_admin_or_owner(self) -> bool:
        """Check if user has admin privileges in the organization"""
        return self.role in ("owner", "admin") and self.is_active()
    
    def can_manage_members(self) -> bool:
        """Check if user can invite/remove members"""
        return self.role in ("owner", "admin") and self.is_active()
    
    def can_edit_organization(self) -> bool:
        """Check if user can edit organization details"""
        return self.role in ("owner", "admin") and self.is_active()
    
    def update_last_active(self):
        """Update the last active timestamp"""
        self.last_active_at = datetime.now(timezone.utc)
    
    def accept_invitation(self):
        """Accept membership invitation"""
        if self.status == "invited":
            self.status = "active"
            self.update_last_active()
    
    def suspend_membership(self):
        """Suspend membership (admin action)"""
        if self.status == "active":
            self.status = "suspended"
    
    def leave_organization(self):
        """User leaves organization voluntarily"""
        if self.status in ("active", "suspended"):
            self.status = "left"