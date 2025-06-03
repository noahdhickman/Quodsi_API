# app/schemas/scenario.py
"""
Pydantic schemas for scenario management.

Defines data transfer objects for scenario CRUD operations, execution state management,
and API validation. Includes specialized schemas for different use cases and lifecycle stages.
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Any, Dict
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


# Enums for controlled values
class TimePeriod(str, Enum):
    """Allowed time periods for scenarios"""
    HOURLY = "hourly"
    DAILY = "daily"
    MONTHLY = "monthly"


class ScenarioState(str, Enum):
    """Scenario execution states"""
    NOT_READY_TO_RUN = "not_ready_to_run"
    READY_TO_RUN = "ready_to_run"
    IS_RUNNING = "is_running"
    CANCELLING = "cancelling"
    RAN_SUCCESS = "ran_success"
    RAN_WITH_ERRORS = "ran_with_errors"


# Base schemas
class ScenarioBase(BaseModel):
    """Base schema with common scenario fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the scenario")
    description: Optional[str] = Field(None, max_length=4000, description="Description of the scenario")
    reps: int = Field(default=1, ge=1, le=10000, description="Number of simulation replications")
    time_period: TimePeriod = Field(default=TimePeriod.DAILY, description="Time period for the scenario")

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


# CRUD schemas
class ScenarioCreate(ScenarioBase):
    """Schema for creating a new scenario"""
    analysis_id: UUID = Field(..., description="ID of the parent analysis")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty or whitespace only')
        return v.strip()


class ScenarioUpdate(BaseModel):
    """Schema for updating scenario metadata"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated name")
    description: Optional[str] = Field(None, max_length=4000, description="Updated description")
    reps: Optional[int] = Field(None, ge=1, le=10000, description="Updated replication count")
    time_period: Optional[TimePeriod] = Field(None, description="Updated time period")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Name cannot be empty or whitespace only')
        return v.strip() if v else v

    class Config:
        use_enum_values = True


# Execution state management schemas
class ScenarioStateUpdate(BaseModel):
    """Schema for updating scenario execution state"""
    state: ScenarioState = Field(..., description="New execution state")
    current_rep: Optional[int] = Field(None, ge=0, description="Current replication number")
    total_reps: Optional[int] = Field(None, ge=1, description="Total replications to run")
    progress_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Progress percentage")
    started_at: Optional[datetime] = Field(None, description="Execution start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Execution completion timestamp")
    execution_time_ms: Optional[int] = Field(None, ge=0, description="Total execution time in milliseconds")
    error_message: Optional[str] = Field(None, max_length=4000, description="User-friendly error message")
    error_details: Optional[str] = Field(None, max_length=8000, description="Technical error details")
    error_stack_trace: Optional[str] = Field(None, max_length=8000, description="Error stack trace")
    blob_storage_path: Optional[str] = Field(None, max_length=500, description="Results storage path")

    @model_validator(mode='before')
    @classmethod
    def validate_execution_fields(cls, values):
        state = values.get('state')
        
        # Validate state-specific requirements
        if state == ScenarioState.IS_RUNNING:
            if values.get('started_at') is None:
                raise ValueError('started_at is required when state is running')
        
        if state in [ScenarioState.RAN_SUCCESS, ScenarioState.RAN_WITH_ERRORS]:
            if values.get('completed_at') is None:
                raise ValueError('completed_at is required when scenario is completed')
        
        if state == ScenarioState.RAN_WITH_ERRORS:
            if not values.get('error_message'):
                raise ValueError('error_message is required when scenario ran with errors')
        
        # Validate progress consistency
        current_rep = values.get('current_rep')
        total_reps = values.get('total_reps')
        progress = values.get('progress_percentage')
        
        if current_rep is not None and total_reps is not None:
            if current_rep > total_reps:
                raise ValueError('current_rep cannot exceed total_reps')
            
            # Calculate expected progress
            if total_reps > 0:
                expected_progress = (current_rep / total_reps) * 100
                if progress is not None and abs(float(progress) - expected_progress) > 1.0:
                    raise ValueError('progress_percentage is inconsistent with current_rep/total_reps')
        
        return values

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            Decimal: lambda d: float(d)
        }


# Read schemas
class ScenarioSummary(ScenarioBase):
    """Lightweight schema for scenario lists"""
    id: UUID
    analysis_id: UUID
    state: ScenarioState
    progress_percentage: Optional[Decimal] = None
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            Decimal: lambda d: float(d) if d else None
        }


class ScenarioRead(ScenarioBase):
    """Complete schema for scenario details"""
    id: UUID
    analysis_id: UUID
    state: ScenarioState
    current_rep: Optional[int] = None
    total_reps: Optional[int] = None
    progress_percentage: Optional[Decimal] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    error_details: Optional[str] = None
    error_stack_trace: Optional[str] = None
    blob_storage_path: Optional[str] = None
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    # Optional nested objects (can be included based on query parameters)
    # analysis: Optional["AnalysisRead"] = None
    # created_by_user: Optional["UserRead"] = None
    # item_profiles: Optional[List["ScenarioItemProfileRead"]] = None

    class Config:
        from_attributes = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            Decimal: lambda d: float(d) if d else None
        }


# Specialized operation schemas
class ScenarioExecutionRequest(BaseModel):
    """Schema for requesting scenario execution"""
    override_reps: Optional[int] = Field(None, ge=1, le=10000, description="Override replication count for this run")
    priority: Optional[str] = Field(default="normal", description="Execution priority (low, normal, high)")
    execution_notes: Optional[str] = Field(None, max_length=1000, description="Notes for this execution")

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        allowed_priorities = {"low", "normal", "high"}
        if v not in allowed_priorities:
            raise ValueError(f'Priority must be one of: {allowed_priorities}')
        return v


class ScenarioExecutionProgress(BaseModel):
    """Schema for scenario execution progress updates"""
    scenario_id: UUID
    state: ScenarioState
    current_rep: int = Field(ge=0)
    total_reps: int = Field(ge=1)
    progress_percentage: Decimal = Field(ge=0, le=100)
    elapsed_time_ms: int = Field(ge=0)
    estimated_remaining_ms: Optional[int] = Field(None, ge=0)
    last_update: datetime

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            Decimal: lambda d: float(d)
        }


class ScenarioCopyRequest(BaseModel):
    """Schema for copying a scenario"""
    new_name: str = Field(..., min_length=1, max_length=255, description="Name for the copied scenario")
    new_description: Optional[str] = Field(None, max_length=4000, description="Description for the copied scenario")
    target_analysis_id: Optional[UUID] = Field(None, description="Target analysis (defaults to same analysis)")
    copy_item_profiles: bool = Field(default=True, description="Whether to copy parameter overrides")

    @field_validator('new_name')
    @classmethod
    def validate_new_name(cls, v):
        if not v or not v.strip():
            raise ValueError('New name cannot be empty or whitespace only')
        return v.strip()


# List and pagination schemas
class ScenarioListResponse(BaseModel):
    """Response schema for paginated scenario lists"""
    scenarios: List[ScenarioSummary]
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


class ScenarioQuery(BaseModel):
    """Schema for advanced scenario searching"""
    analysis_id: Optional[UUID] = Field(None, description="Filter by analysis")
    created_by_user_id: Optional[UUID] = Field(None, description="Filter by creator")
    state: Optional[ScenarioState] = Field(None, description="Filter by execution state")
    time_period: Optional[TimePeriod] = Field(None, description="Filter by time period")
    name_contains: Optional[str] = Field(None, min_length=1, max_length=100, description="Search in names")
    has_errors: Optional[bool] = Field(None, description="Filter scenarios with/without errors")
    completed_after: Optional[datetime] = Field(None, description="Filter by completion date")
    completed_before: Optional[datetime] = Field(None, description="Filter by completion date")
    skip: int = Field(default=0, ge=0, description="Pagination offset")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum results")
    sort_by: Optional[str] = Field(default="created_at", description="Sort field")
    sort_order: Optional[str] = Field(default="desc", description="Sort order (asc/desc)")

    @field_validator('sort_by')
    @classmethod
    def validate_sort_by(cls, v):
        allowed_fields = {
            "name", "created_at", "updated_at", "state", 
            "progress_percentage", "execution_time_ms", "completed_at"
        }
        if v not in allowed_fields:
            raise ValueError(f'sort_by must be one of: {allowed_fields}')
        return v

    @field_validator('sort_order')
    @classmethod
    def validate_sort_order(cls, v):
        if v.lower() not in {"asc", "desc"}:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v.lower()

    @model_validator(mode='before')
    @classmethod
    def validate_date_range(cls, values):
        after = values.get('completed_after')
        before = values.get('completed_before')
        if after and before and after >= before:
            raise ValueError('completed_after must be before completed_before')
        return values

    class Config:
        use_enum_values = True


# Bulk operations
class BulkScenarioCreate(BaseModel):
    """Schema for bulk scenario creation"""
    analysis_id: UUID = Field(..., description="Target analysis for all scenarios")
    scenarios: List[ScenarioBase] = Field(..., min_items=1, max_items=50, description="Scenarios to create")
    
    @field_validator('scenarios')
    @classmethod
    def validate_unique_names(cls, v):
        names = [scenario.name for scenario in v]
        if len(names) != len(set(names)):
            raise ValueError('All scenario names must be unique within the batch')
        return v


class BulkScenarioResponse(BaseModel):
    """Response schema for bulk operations"""
    successful_scenarios: List[UUID] = Field(description="IDs of successfully created scenarios")
    failed_scenarios: List[Dict[str, Any]] = Field(description="Failed creations with error details")
    total_requested: int = Field(ge=0)
    total_successful: int = Field(ge=0)
    total_failed: int = Field(ge=0)


# Statistics and analytics
class ScenarioStatistics(BaseModel):
    """Schema for scenario analytics and statistics"""
    total_scenarios: int = Field(ge=0)
    scenarios_by_state: Dict[str, int] = Field(description="Count of scenarios by state")
    scenarios_by_analysis: Dict[str, int] = Field(description="Count of scenarios by analysis")
    scenarios_by_time_period: Dict[str, int] = Field(description="Count of scenarios by time period")
    average_execution_time_ms: Optional[float] = Field(None, ge=0)
    success_rate_percentage: Optional[float] = Field(None, ge=0, le=100)
    most_common_errors: List[Dict[str, Any]] = Field(description="Most frequent error messages")
    recent_scenarios: List[ScenarioSummary] = Field(description="Recently created scenarios")
    period_start: datetime
    period_end: datetime

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


# Validation schemas
class ScenarioValidationResponse(BaseModel):
    """Schema for scenario validation results"""
    is_valid: bool
    validation_errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    name_available: bool
    analysis_exists: bool
    user_has_permission: bool
    analysis_allows_scenarios: bool = Field(default=True, description="Whether parent analysis allows new scenarios")


# Error and status schemas
class ScenarioExecutionError(BaseModel):
    """Schema for detailed execution error information"""
    scenario_id: UUID
    error_type: str = Field(description="Classification of the error")
    error_message: str = Field(description="User-friendly error message")
    error_details: Optional[str] = Field(None, description="Technical error details")
    error_stack_trace: Optional[str] = Field(None, description="Full stack trace")
    occurred_at: datetime
    recovery_suggestions: List[str] = Field(default_factory=list, description="Possible solutions")

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


# Forward references for nested relationships (will be resolved when needed)
# from app.schemas.analysis import AnalysisRead
# from app.schemas.user import UserRead
# from app.schemas.scenario_item_profile import ScenarioItemProfileRead

# ScenarioRead.model_rebuild()  # Rebuild after importing related schemas