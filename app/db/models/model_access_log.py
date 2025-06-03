# app/db/models/model_access_log.py
"""
Model Access Log database entity for audit trail of model-related operations.

This model serves as a comprehensive audit trail, recording who accessed or
performed operations on models, when, and what the outcome was.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, NVARCHAR
from sqlalchemy.orm import relationship

from app.db.models.base_entity import BaseEntity


class ModelAccessLog(BaseEntity):
    """
    Model Access Log entity for audit trail of model-related operations.
    
    Records all access and operations performed on models including the user,
    action type, result, and contextual information for comprehensive auditing.
    """

    __tablename__ = "model_access_logs"

    # Target model for the access log
    model_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=False,
        comment="The model that was accessed"
    )

    # User who performed the action
    user_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("users.id"),
        nullable=False,
        comment="User who performed the access/operation"
    )

    # Access details
    access_type = Column(
        NVARCHAR(50),
        nullable=False,
        comment="Type of access ('read', 'write', 'execute', 'delete', 'permission_change', 'share', 'download', 'copy', 'template_create')"
    )

    access_result = Column(
        NVARCHAR(20),
        nullable=False,
        comment="Result of the access attempt ('success', 'denied', 'error', 'partial')"
    )

    # Permission context (optional)
    permission_source = Column(
        NVARCHAR(50),
        nullable=True,
        comment="Source of permission ('direct', 'team', 'organization', 'admin')"
    )

    # Session and context information
    session_id = Column(
        NVARCHAR(255),
        nullable=True,
        comment="User session identifier"
    )

    ip_address = Column(
        NVARCHAR(45),  # IPv6 max length
        nullable=True,
        comment="IP address of the request"
    )

    user_agent = Column(
        NVARCHAR(500),
        nullable=True,
        comment="User agent string from the request"
    )

    # Request context
    endpoint = Column(
        NVARCHAR(100),
        nullable=True,
        comment="API endpoint that was accessed"
    )

    request_method = Column(
        NVARCHAR(10),
        nullable=True,
        comment="HTTP method used for the request"
    )

    # Additional details (JSON)
    details = Column(
        NVARCHAR(None),  # NVARCHAR(MAX) for JSON data
        nullable=True,
        comment="Additional context information (JSON format)"
    )

    # Relationships
    model = relationship("Model", back_populates="access_logs")
    user = relationship("User", back_populates="access_logs")

    # Table constraints and indexes
    __table_args__ = (
        # Check constraints
        CheckConstraint(
            "access_type IN ('read', 'write', 'execute', 'delete', 'permission_change', 'share', 'download', 'copy', 'template_create')",
            name="ck_model_access_logs_access_type",
        ),
        CheckConstraint(
            "access_result IN ('success', 'denied', 'error', 'partial')",
            name="ck_model_access_logs_access_result",
        ),
        CheckConstraint(
            "permission_source IS NULL OR permission_source IN ('direct', 'team', 'organization', 'admin')",
            name="ck_model_access_logs_permission_source",
        ),
        # Performance indexes
        Index("ix_model_access_logs_tenant_model_user", "tenant_id", "model_id", "user_id"),
        Index("ix_model_access_logs_tenant_user_time", "tenant_id", "user_id", "created_at"),
        Index("ix_model_access_logs_tenant_model_time", "tenant_id", "model_id", "created_at"),
        Index("ix_model_access_logs_access_type", "access_type"),
        Index("ix_model_access_logs_access_result", "access_result"),
        Index("ix_model_access_logs_session", "session_id"),
    )

    def __repr__(self):
        return (
            f"<ModelAccessLog(id={self.id}, model_id={self.model_id}, "
            f"user_id={self.user_id}, access_type='{self.access_type}', "
            f"result='{self.access_result}', at={self.created_at})>"
        )

    def was_successful(self) -> bool:
        """Check if the access was successful."""
        return self.access_result == 'success'

    def was_denied(self) -> bool:
        """Check if the access was denied."""
        return self.access_result == 'denied'

    def had_error(self) -> bool:
        """Check if there was an error during access."""
        return self.access_result == 'error'

    def was_partial(self) -> bool:
        """Check if the access was partially successful."""
        return self.access_result == 'partial'