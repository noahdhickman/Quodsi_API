# app/db/models/user.py
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from app.db.models.base_entity import BaseEntity
from datetime import datetime


class User(BaseEntity):
    """
    User model representing individual users within tenants.
    
    Each user belongs to exactly one tenant, establishing the foundation
    for multi-tenant data isolation. Users authenticate through various
    identity providers and maintain session and usage statistics.
    """
    __tablename__ = "users"

    # Identity and authentication fields
    identity_provider = Column(String(50), nullable=False, comment="Provider type ('entra_id', 'google', etc.)")
    identity_provider_id = Column(String(255), nullable=False, comment="Unique identifier from the provider")
    email = Column(String(255), nullable=False, comment="User's email address")
    display_name = Column(String(255), nullable=False, comment="User's display name")

    # Session and activity tracking
    last_login_at = Column(DateTime, nullable=True, comment="Most recent login timestamp")
    login_count = Column(Integer, nullable=False, default=0, comment="Count of user logins")
    total_usage_minutes = Column(Integer, nullable=False, default=0, comment="Cumulative time spent using Quodsi")
    last_session_start = Column(DateTime, nullable=True, comment="When current/last session started")
    last_active_at = Column(DateTime, nullable=True, comment="Last user activity timestamp")

    # Account status and metadata
    status = Column(String(20), nullable=False, default='active', comment="User status (active, invited, suspended)")
    user_metadata = Column(String(4000), nullable=True, comment="Additional profile information (JSON data)")

    # Relationships

    tenant_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("tenants.id", name="fk_users_tenant_id"),
        nullable=False,
        index=True,
        comment="Multi-tenant isolation key"
    )

    tenant = relationship("Tenant", back_populates="users")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    created_models = relationship("Model", back_populates="created_by_user")
    analyses = relationship("Analysis", back_populates="created_by_user")
    scenarios = relationship("Scenario", back_populates="created_by_user")
    organization_memberships = relationship("OrganizationMembership", foreign_keys="OrganizationMembership.user_id", back_populates="user")
    
    # Permission relationships
    received_permissions = relationship("ModelPermission", foreign_keys="ModelPermission.user_id", back_populates="target_user")
    granted_permissions = relationship("ModelPermission", foreign_keys="ModelPermission.granted_by_user_id", back_populates="granted_by")
    revoked_permissions = relationship("ModelPermission", foreign_keys="ModelPermission.revoked_by_user_id", back_populates="revoked_by")
    access_logs = relationship("ModelAccessLog", back_populates="user")

    # Additional indexes for user-specific queries
    @declared_attr
    def __table_args__(cls):
        """Define indexes and constraints specific to users table"""
        base_args = super().__table_args__
        user_args = (
            # Unique email per tenant
            UniqueConstraint('tenant_id', 'email', name='uq_users_tenant_email'),
            
            # Identity provider lookup (global uniqueness across tenants)
            UniqueConstraint('identity_provider', 'identity_provider_id', name='uq_users_identity_provider'),
        )
        return base_args + user_args

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, tenant_id={self.tenant_id})>"

    def update_login_stats(self):
        """Update login statistics when user signs in"""
        self.login_count += 1
        self.last_login_at = datetime.utcnow()
        self.last_active_at = datetime.utcnow()

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_active_at = datetime.utcnow()
    
    def get_organizations(self):
        """Get list of organizations user belongs to"""
        return [m.organization for m in self.organization_memberships if m.is_active()]
    
    def get_organization_role(self, organization_id) -> str:
        """Get user's role in a specific organization"""
        for membership in self.organization_memberships:
            if membership.organization_id == organization_id and membership.is_active():
                return membership.role
        return None
    
    def is_organization_member(self, organization_id) -> bool:
        """Check if user is a member of organization"""
        return self.get_organization_role(organization_id) is not None
    
    def is_organization_owner(self, organization_id) -> bool:
        """Check if user is an owner of organization"""
        return self.get_organization_role(organization_id) == "owner"
    
    def is_organization_admin_or_owner(self, organization_id) -> bool:
        """Check if user has admin privileges in organization"""
        role = self.get_organization_role(organization_id)
        return role in ("owner", "admin") if role else False
