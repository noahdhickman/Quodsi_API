# app/db/models/scenario.py
"""
Scenario database entity for individual simulation runs.

This model represents individual simulation runs with specific parameter
configurations, execution state tracking, and results storage. Scenarios
belong to an analysis and enable "what-if" experimentation.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    DateTime,
    BigInteger,
    DECIMAL,
    UniqueConstraint,
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, NVARCHAR
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr

from app.db.models.base_entity import BaseEntity


class Scenario(BaseEntity):
    """
    Scenario entity for individual simulation runs with parameter configurations.
    
    Represents a single simulation run belonging to an analysis, with specific
    parameter configurations, execution state tracking, error handling, and
    results storage capabilities.
    """

    __tablename__ = "scenarios"

    # Core scenario information
    name = Column(
        NVARCHAR(255),
        nullable=False,
        comment="Name of the scenario"
    )
    
    description = Column(
        NVARCHAR(None),  # NVARCHAR(MAX)
        nullable=True,
        comment="Description of the scenario"
    )

    # Parent analysis relationship
    analysis_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        comment="Parent analysis this scenario belongs to"
    )

    # Simulation configuration
    reps = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Number of simulation replications for this scenario"
    )
    
    time_period = Column(
        NVARCHAR(50),
        nullable=False,
        default="daily",
        comment="Time period for this scenario"
    )

    # Execution state tracking
    state = Column(
        NVARCHAR(50),
        nullable=False,
        default="not_ready_to_run",
        comment="Execution state of the scenario"
    )
    
    current_rep = Column(
        Integer,
        nullable=True,
        comment="Current replication number during execution"
    )
    
    total_reps = Column(
        Integer,
        nullable=True,
        comment="Total replications to run (matches reps)"
    )
    
    progress_percentage = Column(
        DECIMAL(5, 2),
        nullable=True,
        comment="Execution progress (0.00 to 100.00)"
    )
    
    started_at = Column(
        DateTime,
        nullable=True,
        comment="Timestamp when execution started"
    )
    
    completed_at = Column(
        DateTime,
        nullable=True,
        comment="Timestamp when execution completed"
    )
    
    execution_time_ms = Column(
        BigInteger,
        nullable=True,
        comment="Total execution time in milliseconds"
    )

    # Error handling
    error_message = Column(
        NVARCHAR(None),  # NVARCHAR(MAX)
        nullable=True,
        comment="User-friendly error message if execution failed"
    )
    
    error_details = Column(
        NVARCHAR(None),  # NVARCHAR(MAX)
        nullable=True,
        comment="Technical error details if execution failed"
    )
    
    error_stack_trace = Column(
        NVARCHAR(None),  # NVARCHAR(MAX)
        nullable=True,
        comment="Full stack trace for debugging if execution failed"
    )

    # Results storage
    blob_storage_path = Column(
        NVARCHAR(500),
        nullable=True,
        comment="Path to detailed results in Azure Blob Storage"
    )

    # Ownership tracking
    created_by_user_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("users.id"),
        nullable=False,
        comment="User who created the scenario"
    )

    # Relationships
    analysis = relationship("Analysis", back_populates="scenarios")
    created_by_user = relationship("User", back_populates="scenarios")
    item_profiles = relationship("ScenarioItemProfile", back_populates="scenario", cascade="all, delete-orphan")

    @declared_attr
    def __table_args__(cls):
        """
        Define scenario-specific constraints and indexes.
        Extends BaseEntity's table args with scenario-specific requirements.
        """
        # Get base table args from BaseEntity
        base_args = list(super().__table_args__)

        # Add scenario-specific constraints and indexes
        scenario_args = [
            # Check constraints
            CheckConstraint(
                "time_period IN ('hourly', 'daily', 'monthly')",
                name="ck_scenarios_time_period"
            ),
            CheckConstraint(
                "state IN ('not_ready_to_run', 'ready_to_run', 'is_running', 'cancelling', 'ran_success', 'ran_with_errors')",
                name="ck_scenarios_state"
            ),
            
            # Foreign key constraints
            # Note: BaseEntity FK to tenants is handled in BaseEntity
            # analysis_id and created_by_user_id FKs are defined in Column declarations above
            
            # Unique constraint: scenario name must be unique within analysis
            UniqueConstraint(
                "tenant_id", "analysis_id", "name",
                name="uq_scenarios_tenant_analysis_name"
            ),
            
            # Performance indexes beyond BaseEntity
            Index(
                "ix_scenarios_tenant_analysis",
                "tenant_id", "analysis_id"
            ),
            Index(
                "ix_scenarios_tenant_state",
                "tenant_id", "state"
            ),
            Index(
                "ix_scenarios_tenant_created_by",
                "tenant_id", "created_by_user_id"
            ),
        ]

        return tuple(base_args + scenario_args)

    def __repr__(self):
        """String representation for debugging"""
        return (
            f"<Scenario("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"analysis_id={self.analysis_id}, "
            f"state='{self.state}', "
            f"tenant_id={self.tenant_id}"
            f")>"
        )

    @property
    def display_name(self) -> str:
        """Get display name for the scenario"""
        return self.name

    def is_editable_by_user(self, user_id: UUID) -> bool:
        """
        Check if the scenario can be edited by the specified user.
        
        Currently checks if user is the creator. This will be enhanced
        with the permission system in the future.
        
        Args:
            user_id: User ID to check permissions for
            
        Returns:
            True if user can edit this scenario
        """
        return self.created_by_user_id == user_id

    def can_be_executed(self) -> bool:
        """
        Check if the scenario is in a state where it can be executed.
        
        Returns:
            True if scenario can be started for execution
        """
        executable_states = {"ready_to_run", "not_ready_to_run"}
        return self.state in executable_states

    def is_running(self) -> bool:
        """
        Check if the scenario is currently running.
        
        Returns:
            True if scenario is currently executing
        """
        return self.state == "is_running"

    def is_completed(self) -> bool:
        """
        Check if the scenario has completed execution (successfully or with errors).
        
        Returns:
            True if scenario has finished executing
        """
        completed_states = {"ran_success", "ran_with_errors"}
        return self.state in completed_states

    def has_errors(self) -> bool:
        """
        Check if the scenario completed with errors.
        
        Returns:
            True if scenario failed during execution
        """
        return self.state == "ran_with_errors"

    def get_execution_duration_seconds(self) -> Optional[float]:
        """
        Get the execution duration in seconds.
        
        Returns:
            Execution duration in seconds, or None if not available
        """
        if self.execution_time_ms is not None:
            return self.execution_time_ms / 1000.0
        return None

    def get_progress_info(self) -> dict:
        """
        Get comprehensive progress information for the scenario.
        
        Returns:
            Dictionary with progress details
        """
        return {
            "state": self.state,
            "current_rep": self.current_rep,
            "total_reps": self.total_reps or self.reps,
            "progress_percentage": float(self.progress_percentage) if self.progress_percentage else None,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "execution_time_ms": self.execution_time_ms,
            "has_errors": self.has_errors(),
            "is_running": self.is_running(),
            "is_completed": self.is_completed()
        }

    def get_configuration_summary(self) -> dict:
        """
        Get scenario configuration summary.
        
        Returns:
            Dictionary with configuration details
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "analysis_id": self.analysis_id,
            "reps": self.reps,
            "time_period": self.time_period,
            "created_by_user_id": self.created_by_user_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def can_be_modified(self) -> bool:
        """
        Check if the scenario configuration can be modified.
        
        Scenarios can only be modified when they're not running or completed.
        
        Returns:
            True if scenario can be modified
        """
        modifiable_states = {"not_ready_to_run", "ready_to_run"}
        return self.state in modifiable_states

    def reset_execution_state(self) -> None:
        """
        Reset execution-related fields to prepare for a new run.
        
        This clears progress tracking, timestamps, and error information.
        """
        self.current_rep = None
        self.total_reps = None
        self.progress_percentage = None
        self.started_at = None
        self.completed_at = None
        self.execution_time_ms = None
        self.error_message = None
        self.error_details = None
        self.error_stack_trace = None
        self.blob_storage_path = None
        self.state = "not_ready_to_run"