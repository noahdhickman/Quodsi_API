# app/schemas/scenario_item_profile.py
"""
Pydantic schemas for scenario item profile management.

Defines data transfer objects for scenario parameter override CRUD operations
and API validation. Includes specialized schemas for different use cases.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


# Enums for controlled values
class TargetObjectType(str, Enum):
    """Allowed target object types for parameter overrides"""
    ACTIVITY = "activity"
    RESOURCE = "resource"
    QUEUE = "queue"
    CONNECTOR = "connector"
    RESOURCE_POOL = "resource_pool"


# Base schemas
class ScenarioItemProfileBase(BaseModel):
    """Base schema with common profile fields"""
    target_object_id: UUID = Field(..., description="ID of the model component being overridden")
    target_object_type: TargetObjectType = Field(..., description="Type of model component")
    property_name: str = Field(..., min_length=1, max_length=255, description="Name of the property being overridden")
    property_value: str = Field(..., min_length=1, description="New value for the property")
    description: Optional[str] = Field(None, max_length=4000, description="Description of why this override was made")
    change_reason: Optional[str] = Field(None, max_length=500, description="Reason for the parameter change")

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


# CRUD schemas
class ScenarioItemProfileCreate(ScenarioItemProfileBase):
    """Schema for creating a new scenario item profile"""
    original_value: Optional[str] = Field(None, description="Original value from the base model (for reference)")

    @field_validator('property_name')
    @classmethod
    def validate_property_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Property name cannot be empty or whitespace only')
        return v.strip()

    @field_validator('property_value')
    @classmethod
    def validate_property_value(cls, v):
        if not v or not v.strip():
            raise ValueError('Property value cannot be empty or whitespace only')
        return v.strip()


class ScenarioItemProfileUpdate(BaseModel):
    """Schema for updating scenario item profile"""
    property_value: Optional[str] = Field(None, min_length=1, description="Updated value for the property")
    description: Optional[str] = Field(None, max_length=4000, description="Updated description")
    change_reason: Optional[str] = Field(None, max_length=500, description="Updated reason for change")

    @field_validator('property_value')
    @classmethod
    def validate_property_value(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Property value cannot be empty or whitespace only')
        return v.strip() if v else v


# Read schemas
class ScenarioItemProfileRead(ScenarioItemProfileBase):
    """Complete schema for scenario item profile details"""
    id: UUID
    scenario_id: UUID
    original_value: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class ScenarioItemProfileSummary(BaseModel):
    """Lightweight schema for profile lists"""
    id: UUID
    scenario_id: UUID
    target_object_id: UUID
    target_object_type: TargetObjectType
    property_name: str
    property_value: str
    has_description: bool = Field(description="Whether a description is provided")

    class Config:
        from_attributes = True
        use_enum_values = True

    @model_validator(mode='before')
    @classmethod
    def set_has_description(cls, data):
        if isinstance(data, dict):
            data['has_description'] = bool(data.get('description'))
        else:
            # For ORM objects
            data.has_description = bool(getattr(data, 'description', None))
        return data


# Specialized operation schemas
class ScenarioItemProfileBulkCreate(BaseModel):
    """Schema for bulk profile creation"""
    scenario_id: UUID = Field(..., description="Target scenario for all profiles")
    profiles: List[ScenarioItemProfileBase] = Field(..., min_items=1, max_items=100, description="Profiles to create")
    
    @field_validator('profiles')
    @classmethod
    def validate_unique_profiles(cls, v):
        # Check for duplicate property overrides
        seen = set()
        for profile in v:
            key = (profile.target_object_id, profile.property_name)
            if key in seen:
                raise ValueError(f'Duplicate override for object {profile.target_object_id}, property {profile.property_name}')
            seen.add(key)
        return v


class ScenarioItemProfileBulkResponse(BaseModel):
    """Response schema for bulk operations"""
    successful_profiles: List[UUID] = Field(description="IDs of successfully created profiles")
    failed_profiles: List[Dict[str, Any]] = Field(description="Failed creations with error details")
    total_requested: int = Field(ge=0)
    total_successful: int = Field(ge=0)
    total_failed: int = Field(ge=0)


class ScenarioItemProfileQuery(BaseModel):
    """Schema for advanced profile searching"""
    scenario_id: Optional[UUID] = Field(None, description="Filter by scenario")
    target_object_id: Optional[UUID] = Field(None, description="Filter by target object")
    target_object_type: Optional[TargetObjectType] = Field(None, description="Filter by object type")
    property_name_contains: Optional[str] = Field(None, min_length=1, max_length=100, description="Search in property names")
    skip: int = Field(default=0, ge=0, description="Pagination offset")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum results")

    class Config:
        use_enum_values = True


class ProfilesByTargetResponse(BaseModel):
    """Response schema for profiles grouped by target object"""
    target_object_id: UUID
    target_object_type: TargetObjectType
    profiles: List[ScenarioItemProfileRead]
    profile_count: int = Field(ge=0)

    class Config:
        use_enum_values = True


class ProfileValidationResponse(BaseModel):
    """Schema for profile validation results"""
    is_valid: bool
    validation_errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    target_object_exists: bool
    property_exists: bool
    value_type_compatible: bool
    conflicts_with_existing: bool


class ProfileComparisonResponse(BaseModel):
    """Schema for comparing profile values with original"""
    profile_id: UUID
    target_object_id: UUID
    target_object_type: TargetObjectType
    property_name: str
    original_value: Optional[str]
    override_value: str
    value_changed: bool
    change_percentage: Optional[float] = Field(None, description="Percentage change if numeric values")
    change_description: str

    class Config:
        use_enum_values = True


class ScenarioProfileApplicationResult(BaseModel):
    """Schema for the result of applying profiles to model data"""
    scenario_id: UUID
    base_model_id: UUID
    applied_profiles_count: int = Field(ge=0)
    modified_objects: List[Dict[str, Any]] = Field(description="Objects that were modified")
    validation_errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    result_configuration: Dict[str, Any] = Field(description="Final configuration with overrides applied")


# List and pagination schemas
class ScenarioItemProfileListResponse(BaseModel):
    """Response schema for paginated profile lists"""
    profiles: List[ScenarioItemProfileRead]
    total: int = Field(ge=0)
    skip: int = Field(ge=0)
    limit: int = Field(ge=1)
    has_more: bool

    @model_validator(mode='before')
    @classmethod
    def calculate_has_more(cls, values):
        total = values.get('total', 0)
        skip = values.get('skip', 0)
        limit = values.get('limit', 0)
        values['has_more'] = (skip + limit) < total
        return values


# Import/Export schemas
class ScenarioItemProfileExport(BaseModel):
    """Schema for exporting profiles"""
    scenario_name: str
    scenario_id: UUID
    export_timestamp: datetime
    profiles: List[ScenarioItemProfileRead]
    total_profiles: int = Field(ge=0)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class ScenarioItemProfileImport(BaseModel):
    """Schema for importing profiles to a scenario"""
    target_scenario_id: UUID = Field(..., description="Scenario to import profiles into")
    profiles: List[ScenarioItemProfileBase] = Field(..., min_items=1, description="Profiles to import")
    overwrite_existing: bool = Field(default=False, description="Whether to overwrite existing profiles")
    validate_targets: bool = Field(default=True, description="Whether to validate target objects exist")