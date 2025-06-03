# app/db/models/analysis.py
"""
Analysis database entity for organizing simulation studies.

This model represents a container for grouping related scenarios under a common
study or experimental setup, linked to a parent simulation model. Analyses provide
default parameters for child scenarios and enable hierarchical organization.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, NVARCHAR
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr

from app.db.models.base_entity import BaseEntity


class Analysis(BaseEntity):
    """
    Analysis entity for organizing simulation studies and experiments.
    
    Serves as a container for grouping related scenarios under a common study,
    providing default parameters and hierarchical organization of simulation work.
    Each analysis belongs to a parent model and can contain multiple scenarios.
    """

    __tablename__ = "analyses"

    # Core analysis information
    name = Column(
        NVARCHAR(255),
        nullable=False,
        comment="Name of the analysis study"
    )
    
    description = Column(
        NVARCHAR(None),  # NVARCHAR(MAX)
        nullable=True,
        comment="Description of the analysis study"
    )

    # Parent model relationship
    model_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=False,
        comment="Parent model this analysis belongs to"
    )

    # Default parameters for child scenarios
    default_reps = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Default number of replications for child scenarios"
    )
    
    default_time_period = Column(
        NVARCHAR(50),
        nullable=False,
        default="daily",
        comment="Default time period for child scenarios"
    )

    # Ownership tracking
    created_by_user_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("users.id"),
        nullable=False,
        comment="User who created the analysis"
    )

    # Relationships
    model = relationship("Model", back_populates="analyses")
    created_by_user = relationship("User", back_populates="analyses")
    scenarios = relationship("Scenario", back_populates="analysis", cascade="all, delete-orphan")

    @declared_attr
    def __table_args__(cls):
        """
        Define analysis-specific constraints and indexes.
        Extends BaseEntity's table args with analysis-specific requirements.
        """
        # Get base table args from BaseEntity
        base_args = list(super().__table_args__)

        # Add analysis-specific constraints and indexes
        analysis_args = [
            # Check constraints
            CheckConstraint(
                "default_time_period IN ('hourly', 'daily', 'monthly')",
                name="ck_analyses_default_time_period"
            ),
            
            # Foreign key constraints
            # Note: BaseEntity FK to tenants is handled in BaseEntity
            # model_id and created_by_user_id FKs are defined in Column declarations above
            
            # Unique constraint: analysis name must be unique within model
            UniqueConstraint(
                "tenant_id", "model_id", "name",
                name="uq_analyses_tenant_model_name"
            ),
            
            # Performance indexes beyond BaseEntity
            Index(
                "ix_analyses_tenant_model",
                "tenant_id", "model_id"
            ),
            Index(
                "ix_analyses_tenant_created_by",
                "tenant_id", "created_by_user_id"
            ),
        ]

        return tuple(base_args + analysis_args)

    def __repr__(self):
        """String representation for debugging"""
        return (
            f"<Analysis("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"model_id={self.model_id}, "
            f"tenant_id={self.tenant_id}"
            f")>"
        )

    @property
    def display_name(self) -> str:
        """Get display name for the analysis"""
        return self.name

    def get_default_scenario_config(self) -> dict:
        """
        Get default configuration for scenarios created under this analysis.
        
        Returns:
            Dictionary with default parameters for new scenarios
        """
        return {
            "default_reps": self.default_reps,
            "default_time_period": self.default_time_period
        }

    def is_editable_by_user(self, user_id: UUID) -> bool:
        """
        Check if the analysis can be edited by the specified user.
        
        Currently checks if user is the creator. This will be enhanced
        with the permission system in the future.
        
        Args:
            user_id: User ID to check permissions for
            
        Returns:
            True if user can edit this analysis
        """
        return self.created_by_user_id == user_id

    def validate_time_period(self) -> bool:
        """
        Validate that the default_time_period is one of the allowed values.
        
        Returns:
            True if time period is valid
        """
        allowed_periods = {"hourly", "daily", "monthly"}
        return self.default_time_period in allowed_periods

    def get_scenario_count(self) -> int:
        """
        Get the number of scenarios in this analysis.
        
        Note: This will be implemented when scenarios table is added.
        For now, returns 0 as placeholder.
        
        Returns:
            Number of scenarios in this analysis
        """
        # TODO: Implement when scenarios relationship is available
        # return len([s for s in self.scenarios if not s.is_deleted])
        return 0

    def get_summary_info(self) -> dict:
        """
        Get summary information about this analysis.
        
        Returns:
            Dictionary with analysis summary data
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "model_id": self.model_id,
            "created_by_user_id": self.created_by_user_id,
            "scenario_count": self.get_scenario_count(),
            "default_reps": self.default_reps,
            "default_time_period": self.default_time_period,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }