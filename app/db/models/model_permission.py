# app/db/models/model_permission.py
"""
Model Permission database entity for managing access control to simulation models.

This model handles granular access control for models with role-based permissions,
supporting user, team, and organization-level access grants.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, NVARCHAR
from sqlalchemy.orm import relationship

from app.db.models.base_entity import BaseEntity


class ModelPermission(BaseEntity):
    """
    Model Permission entity for granular access control to simulation models.
    
    Supports permissions granted to users, teams, or organizations with
    different access levels (read, write, execute, admin) and lifecycle management
    including expiration and revocation tracking.
    """

    __tablename__ = "model_permissions"

    # Target model for permission
    model_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=False,
        comment="The model to which this permission applies"
    )

    # Permission targets (exactly one must be set)
    user_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("users.id"),
        nullable=True,
        comment="Target user for this permission (if applicable)"
    )
    
    organization_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("organizations.id"),
        nullable=True,
        comment="Target organization for this permission (if applicable)"
    )
    
    team_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("teams.id"),
        nullable=True,
        comment="Target team for this permission (if applicable)"
    )

    # Permission details
    permission_level = Column(
        NVARCHAR(20),
        nullable=False,
        default="read",
        comment="Access level ('read', 'write', 'execute', 'admin')"
    )

    # Status and lifecycle
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether the permission is currently active"
    )
    
    # Time-based validity (optional)
    valid_from = Column(
        DateTime,
        nullable=True,
        comment="When the permission becomes valid (optional)"
    )
    
    valid_until = Column(
        DateTime,
        nullable=True,
        comment="When the permission expires (optional)"
    )
    
    # Audit trail fields
    granted_by_user_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("users.id"),
        nullable=False,
        comment="User who granted this permission"
    )
    
    granted_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="When the permission was granted"
    )
    
    revoked_by_user_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("users.id"),
        nullable=True,
        comment="User who revoked the permission"
    )
    
    revoked_at = Column(
        DateTime,
        nullable=True,
        comment="When the permission was revoked"
    )
    
    # Notes and documentation
    notes = Column(
        NVARCHAR(500),
        nullable=True,
        comment="Notes about this permission grant/revocation"
    )

    # Relationships
    model = relationship("Model", back_populates="permissions")
    target_user = relationship("User", foreign_keys=[user_id], back_populates="received_permissions")
    target_organization = relationship("Organization", back_populates="received_permissions")
    target_team = relationship("Team", back_populates="received_permissions")
    granted_by = relationship("User", foreign_keys=[granted_by_user_id], back_populates="granted_permissions")
    revoked_by = relationship("User", foreign_keys=[revoked_by_user_id], back_populates="revoked_permissions")

    # Table constraints and indexes
    __table_args__ = (
        # Check constraints
        CheckConstraint(
            """
            (user_id IS NOT NULL AND organization_id IS NULL AND team_id IS NULL) OR
            (user_id IS NULL AND organization_id IS NOT NULL AND team_id IS NULL) OR
            (user_id IS NULL AND organization_id IS NULL AND team_id IS NOT NULL)
            """,
            name="ck_model_permissions_single_target",
        ),
        CheckConstraint(
            "permission_level IN ('read', 'write', 'execute', 'admin')",
            name="ck_model_permissions_level",
        ),
        # Performance indexes
        Index("ix_model_permissions_tenant_active_status", "tenant_id", "index_id"),
        Index("ix_model_permissions_tenant_model", "tenant_id", "model_id", "is_active"),
        Index("ix_model_permissions_tenant_user", "tenant_id", "user_id", "model_id", "is_active"),
        Index("ix_model_permissions_tenant_organization", "tenant_id", "organization_id", "model_id", "is_active"),
        Index("ix_model_permissions_tenant_team", "tenant_id", "team_id", "model_id", "is_active"),
        Index("ix_model_permissions_valid_until", "valid_until"),
    )

    def __repr__(self):
        target = None
        if self.user_id:
            target = f"user:{self.user_id}"
        elif self.organization_id:
            target = f"org:{self.organization_id}"
        elif self.team_id:
            target = f"team:{self.team_id}"
            
        return (
            f"<ModelPermission(id={self.id}, model_id={self.model_id}, "
            f"target={target}, level='{self.permission_level}', active={self.is_active})>"
        )

    def is_expired(self) -> bool:
        """Check if the permission has expired."""
        if self.valid_until is None:
            return False
        return datetime.now(timezone.utc) >= self.valid_until

    def is_valid(self) -> bool:
        """Check if the permission is valid (active and not expired)."""
        return self.is_active and not self.is_expired()

    def get_target_type(self) -> Optional[str]:
        """Get the type of target for this permission."""
        if self.user_id:
            return "user"
        elif self.organization_id:
            return "organization"
        elif self.team_id:
            return "team"
        return None

    def get_target_id(self) -> Optional[UUID]:
        """Get the target ID for this permission."""
        if self.user_id:
            return self.user_id
        elif self.organization_id:
            return self.organization_id
        elif self.team_id:
            return self.team_id
        return None