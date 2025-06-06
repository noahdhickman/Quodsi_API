# app/db/models/simulation_model.py
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    DECIMAL
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, NVARCHAR
from sqlalchemy.orm import relationship

from app.db.models.base_entity import BaseEntity


class Model(BaseEntity):
    """
    Simulation Model entity - stores definitions and metadata
    for all simulation models created on the platform.
    """

    __tablename__ = "models"

    # Basic Information
    name = Column(NVARCHAR(255), nullable=False)
    description = Column(NVARCHAR(None), nullable=True)  # NVARCHAR(MAX)

    # Source Information
    source = Column(
        NVARCHAR(50), nullable=False
    )  # enum: 'lucidchart', 'standalone', 'miro'
    source_document_id = Column(NVARCHAR(255), nullable=True)
    source_url = Column(NVARCHAR(500), nullable=True)

    # Default Simulation Parameters
    reps = Column(Integer, nullable=False, default=1)
    forecast_days = Column(Integer, nullable=False, default=30)
    random_seed = Column(Integer, nullable=True)
    time_type = Column(
        NVARCHAR(20), nullable=False, default="clock"
    )  # enum: 'clock', 'calendar'
    one_clock_unit = Column(
        NVARCHAR(20), nullable=True
    )  # enum: 'seconds', 'minutes', 'hours', 'days'
    warmup_clock_period = Column(DECIMAL(18, 6), nullable=True)
    run_clock_period = Column(DECIMAL(18, 6), nullable=True)

    # Date/Time Parameters
    warmup_date_time = Column(DateTime, nullable=True)
    start_date_time = Column(DateTime, nullable=True)
    finish_date_time = Column(DateTime, nullable=True)

    # Ownership and Association
    created_by_user_id = Column(
        UNIQUEIDENTIFIER, ForeignKey("users.id"), nullable=False
    )
    organization_id = Column(
        UNIQUEIDENTIFIER, ForeignKey("organizations.id"), nullable=True
    )
    team_id = Column(UNIQUEIDENTIFIER, ForeignKey("teams.id"), nullable=True)

    # Flags
    is_public = Column(Boolean, nullable=False, default=False)
    is_template = Column(Boolean, nullable=False, default=False)

    # Versioning
    version = Column(Integer, nullable=False, default=1)

    # Legacy
    blob_storage_url = Column(NVARCHAR(500), nullable=True)

    # Relationships
    created_by_user = relationship("User", back_populates="created_models")
    organization = relationship("Organization", back_populates="models")
    team = relationship("Team", back_populates="models")
    permissions = relationship("ModelPermission", back_populates="model", cascade="all, delete-orphan")
    access_logs = relationship("ModelAccessLog", back_populates="model", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="model", cascade="all, delete-orphan")

    # Table Constraints
    __table_args__ = (
        # Check constraints
        CheckConstraint(
            "source IN ('lucidchart', 'standalone', 'miro')",
            name="ck_models_source",
        ),
        CheckConstraint(
            "time_type IN ('clock', 'calendar')", name="ck_models_time_type"
        ),
        CheckConstraint(
            "one_clock_unit IS NULL OR one_clock_unit IN ('seconds', 'minutes', 'hours', 'days')",
            name="ck_models_one_clock_unit",
        ),
        CheckConstraint("reps >= 1", name="ck_models_reps_positive"),
        CheckConstraint("forecast_days >= 1", name="ck_models_forecast_days_positive"),
        CheckConstraint("version >= 1", name="ck_models_version_positive"),
        # Tenant consistency checks
        CheckConstraint(
            """
            (organization_id IS NULL) OR 
            (SELECT tenant_id FROM organizations WHERE id = organization_id) = tenant_id
            """,
            name="ck_models_tenant_org_consistency",
        ),
        CheckConstraint(
            """
            (team_id IS NULL) OR 
            (SELECT tenant_id FROM teams WHERE id = team_id) = tenant_id
            """,
            name="ck_models_tenant_team_consistency",
        ),
        CheckConstraint(
            """
            (SELECT tenant_id FROM users WHERE id = created_by_user_id) = tenant_id
            """,
            name="ck_models_tenant_user_consistency",
        ),
        # Indexes
        Index("ix_models_tenant_name", "tenant_id", "name"),
        Index("ix_models_tenant_source", "tenant_id", "source"),
        Index("ix_models_tenant_created_by_user", "tenant_id", "created_by_user_id"),
        Index("ix_models_tenant_organization", "tenant_id", "organization_id"),
        Index("ix_models_tenant_team", "tenant_id", "team_id"),
        Index("ix_models_is_template", "is_template"),
        Index("ix_models_is_public", "is_public"),
        # Unique constraint for name within tenant
        UniqueConstraint("tenant_id", "name", name="uq_models_tenant_name"),
    )

    def __repr__(self):
        return f"<Model(id={self.id}, name='{self.name}', source='{self.source}')>"
