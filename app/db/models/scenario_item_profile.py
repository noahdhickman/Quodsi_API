# app/db/models/scenario_item_profile.py
"""
ScenarioItemProfile database entity for parameter overrides.

This model represents parameter overrides for specific model components within
a scenario, enabling "what-if" analysis by allowing users to modify individual
parameters without changing the base model.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, NVARCHAR
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr

from app.db.models.base_entity import BaseEntity


class ScenarioItemProfile(BaseEntity):
    """
    ScenarioItemProfile entity for parameter overrides in scenarios.
    
    Allows users to override specific parameters of model components
    (activities, resources, etc.) for a particular scenario run,
    enabling "what-if" experimentation without modifying the base model.
    """

    __tablename__ = "scenario_item_profiles"

    # Parent scenario relationship
    scenario_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("scenarios.id", ondelete="CASCADE"),
        nullable=False,
        comment="Parent scenario this profile belongs to"
    )

    # Target object identification
    target_object_id = Column(
        UNIQUEIDENTIFIER,
        nullable=False,
        comment="ID of the model component being overridden"
    )
    
    target_object_type = Column(
        NVARCHAR(50),
        nullable=False,
        comment="Type of model component (activity, resource, etc.)"
    )

    # Override configuration
    property_name = Column(
        NVARCHAR(255),
        nullable=False,
        comment="Name of the property being overridden"
    )
    
    property_value = Column(
        NVARCHAR(None),  # NVARCHAR(MAX)
        nullable=False,
        comment="New value for the property"
    )
    
    original_value = Column(
        NVARCHAR(None),  # NVARCHAR(MAX)
        nullable=True,
        comment="Original value from the base model (for reference)"
    )

    # Metadata
    description = Column(
        NVARCHAR(None),  # NVARCHAR(MAX)
        nullable=True,
        comment="Description of why this override was made"
    )
    
    change_reason = Column(
        NVARCHAR(500),
        nullable=True,
        comment="Reason for the parameter change"
    )

    # Relationships
    scenario = relationship("Scenario", back_populates="item_profiles")

    @declared_attr
    def __table_args__(cls):
        """
        Define scenario_item_profile-specific constraints and indexes.
        Extends BaseEntity's table args with profile-specific requirements.
        """
        # Get base table args from BaseEntity
        base_args = list(super().__table_args__)

        # Add scenario_item_profile-specific constraints and indexes
        profile_args = [
            # Check constraints
            CheckConstraint(
                "target_object_type IN ('activity', 'resource', 'queue', 'connector', 'resource_pool')",
                name="ck_scenario_item_profiles_target_type"
            ),
            
            # Unique constraint: only one override per property per target object per scenario
            UniqueConstraint(
                "tenant_id", "scenario_id", "target_object_id", "property_name",
                name="uq_scenprofiles_tenant_scenario_target_prop"
            ),
            
            # Performance indexes
            Index(
                "ix_scenario_item_profiles_tenant_scenario",
                "tenant_id", "scenario_id"
            ),
            Index(
                "ix_scenario_item_profiles_tenant_target",
                "tenant_id", "target_object_id", "target_object_type"
            ),
        ]

        return tuple(base_args + profile_args)

    def __repr__(self):
        """String representation for debugging"""
        return (
            f"<ScenarioItemProfile("
            f"id={self.id}, "
            f"scenario_id={self.scenario_id}, "
            f"target_object_id={self.target_object_id}, "
            f"target_object_type='{self.target_object_type}', "
            f"property_name='{self.property_name}', "
            f"tenant_id={self.tenant_id}"
            f")>"
        )

    @property
    def display_name(self) -> str:
        """Get display name for the profile"""
        return f"{self.target_object_type}.{self.property_name}"

    def get_override_summary(self) -> dict:
        """
        Get a summary of this override.
        
        Returns:
            Dictionary with override details
        """
        return {
            "id": self.id,
            "scenario_id": self.scenario_id,
            "target_object_id": self.target_object_id,
            "target_object_type": self.target_object_type,
            "property_name": self.property_name,
            "property_value": self.property_value,
            "original_value": self.original_value,
            "description": self.description,
            "change_reason": self.change_reason,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def is_numeric_property(self) -> bool:
        """
        Check if this property is expected to be numeric.
        
        This is a simplified check - in a real system, you'd have
        more sophisticated type checking based on the model schema.
        
        Returns:
            True if property is likely numeric
        """
        numeric_indicators = ['_time', '_cost', '_rate', '_count', '_percentage']
        return any(indicator in self.property_name.lower() for indicator in numeric_indicators)

    def validate_value_type(self) -> bool:
        """
        Basic validation of property value type.
        
        In a production system, this would validate against the actual
        model schema to ensure type compatibility.
        
        Returns:
            True if value appears valid for the property
        """
        # For now, just ensure value is not empty
        return bool(self.property_value and self.property_value.strip())

    def get_value_change_description(self) -> str:
        """
        Get a human-readable description of the value change.
        
        Returns:
            Description of the change
        """
        if self.original_value:
            return f"Changed from '{self.original_value}' to '{self.property_value}'"
        else:
            return f"Set to '{self.property_value}'"

    def applies_to_object(self, object_id: UUID, object_type: str) -> bool:
        """
        Check if this profile applies to a specific object.
        
        Args:
            object_id: ID of the object to check
            object_type: Type of the object to check
            
        Returns:
            True if this profile applies to the specified object
        """
        return (
            self.target_object_id == object_id and
            self.target_object_type == object_type
        )