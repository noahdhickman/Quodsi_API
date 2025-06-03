# app/schemas/analysis.py
"""
Pydantic schemas for Analysis management.

These schemas define the API contracts for creating, reading, and updating
analyses with proper validation and business rule enforcement.
"""
from pydantic import BaseModel, Field, field_validator, computed_field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum


class TimePeriod(str, Enum):
    """Enumeration of allowed time periods for analyses"""
    HOURLY = "hourly"
    DAILY = "daily"
    MONTHLY = "monthly"


class AnalysisBase(BaseModel):
    """Base analysis schema with common fields"""
    
    name: str = Field(..., min_length=1, max_length=255, description="Analysis name")
    description: Optional[str] = Field(None, description="Analysis description")


class AnalysisCreate(AnalysisBase):
    """Schema for creating a new analysis"""
    
    model_id: UUID = Field(..., description="ID of the parent model")
    
    # Default parameters for child scenarios
    default_reps: int = Field(default=1, ge=1, le=10000, description="Default number of replications for scenarios")
    default_time_period: TimePeriod = Field(default=TimePeriod.DAILY, description="Default time period for scenarios")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate analysis name"""
        if not v.strip():
            raise ValueError("Analysis name cannot be empty or whitespace")
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean description"""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Customer Service Optimization Study",
                "description": "Analysis of various staffing scenarios to optimize customer wait times",
                "model_id": "550e8400-e29b-41d4-a716-446655440000",
                "default_reps": 100,
                "default_time_period": "daily"
            }
        }
    }


class AnalysisUpdate(BaseModel):
    """Schema for updating an analysis"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated analysis name")
    description: Optional[str] = Field(None, description="Updated analysis description")
    default_reps: Optional[int] = Field(None, ge=1, le=10000, description="Updated default replications")
    default_time_period: Optional[TimePeriod] = Field(None, description="Updated default time period")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate analysis name if provided"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Analysis name cannot be empty or whitespace")
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean description if provided"""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Updated Customer Service Study",
                "description": "Enhanced analysis with additional scenarios",
                "default_reps": 150,
                "default_time_period": "hourly"
            }
        }
    }


class AnalysisRead(AnalysisBase):
    """Schema for reading analysis information"""
    
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    model_id: UUID
    created_by_user_id: UUID
    
    # Default parameters
    default_reps: int
    default_time_period: TimePeriod
    
    # Computed fields for convenience
    @computed_field
    @property
    def scenario_count(self) -> int:
        """Number of scenarios in this analysis (placeholder for future)"""
        # TODO: Implement when scenarios are added
        return 0
    
    @computed_field
    @property
    def is_hourly_analysis(self) -> bool:
        """Check if analysis uses hourly time periods"""
        return self.default_time_period == TimePeriod.HOURLY
    
    @computed_field
    @property
    def is_daily_analysis(self) -> bool:
        """Check if analysis uses daily time periods"""
        return self.default_time_period == TimePeriod.DAILY
    
    @computed_field
    @property
    def is_monthly_analysis(self) -> bool:
        """Check if analysis uses monthly time periods"""
        return self.default_time_period == TimePeriod.MONTHLY

    model_config = {"from_attributes": True}


class AnalysisSummary(BaseModel):
    """Lightweight analysis schema for listings"""
    
    id: UUID
    name: str
    description: Optional[str] = None
    model_id: UUID
    created_by_user_id: UUID
    default_reps: int
    default_time_period: TimePeriod
    scenario_count: Optional[int] = 0  # Placeholder for future
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnalysisListResponse(BaseModel):
    """Paginated response for analysis listings"""
    
    analyses: List[AnalysisSummary]
    total: int
    skip: int
    limit: int


# Nested schemas with related entity information

class AnalysisWithModel(AnalysisRead):
    """Analysis schema that includes model information"""
    
    model: Optional[dict] = Field(None, description="Parent model information")
    
    model_config = {"from_attributes": True}


class AnalysisWithUser(AnalysisRead):
    """Analysis schema that includes creator information"""
    
    created_by_user: Optional[dict] = Field(None, description="Creator user information")
    
    model_config = {"from_attributes": True}


class AnalysisDetailed(AnalysisRead):
    """Detailed analysis schema with all related information"""
    
    model: Optional[dict] = Field(None, description="Parent model information")
    created_by_user: Optional[dict] = Field(None, description="Creator user information")
    # scenarios: List[dict] = Field(default_factory=list, description="Child scenarios")  # Future implementation
    
    model_config = {"from_attributes": True}


# Bulk operation schemas

class BulkAnalysisCreate(BaseModel):
    """Schema for creating multiple analyses in bulk"""
    
    model_id: UUID = Field(..., description="Parent model for all analyses")
    analyses: List[AnalysisCreate] = Field(..., min_length=1, max_length=100, description="List of analyses to create")
    
    def model_post_init(self, __context) -> None:
        """Ensure all analyses have the same model_id"""
        for analysis in self.analyses:
            analysis.model_id = self.model_id


class BulkAnalysisResponse(BaseModel):
    """Response schema for bulk analysis operations"""
    
    successful_analyses: List[UUID] = Field(default_factory=list, description="IDs of successfully created analyses")
    failed_analyses: List[dict] = Field(default_factory=list, description="Details of failed analysis creations")
    total_requested: int = Field(..., description="Total number of analyses requested")
    total_successful: int = Field(..., description="Total number of successfully created analyses")
    total_failed: int = Field(..., description="Total number of failed analysis creations")


# Query and filter schemas

class AnalysisQuery(BaseModel):
    """Schema for querying analyses with filters"""
    
    model_id: Optional[UUID] = Field(None, description="Filter by model ID")
    created_by_user_id: Optional[UUID] = Field(None, description="Filter by creator user ID")
    time_period: Optional[TimePeriod] = Field(None, description="Filter by default time period")
    name_contains: Optional[str] = Field(None, min_length=1, description="Filter by name containing text")
    
    # Date range filters
    created_after: Optional[datetime] = Field(None, description="Filter analyses created after this date")
    created_before: Optional[datetime] = Field(None, description="Filter analyses created before this date")
    
    # Pagination
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of records to return")
    
    def model_post_init(self, __context) -> None:
        """Validate date range"""
        if self.created_after and self.created_before and self.created_after >= self.created_before:
            raise ValueError("created_after must be before created_before")


class AnalysisStatistics(BaseModel):
    """Schema for analysis statistics and analytics"""
    
    total_analyses: int
    analyses_by_time_period: dict[str, int] = Field(default_factory=dict)
    analyses_by_model: List[dict] = Field(default_factory=list)
    recent_analyses: List[AnalysisSummary] = Field(default_factory=list)
    
    # Average metrics
    average_default_reps: float
    most_common_time_period: Optional[str] = None
    
    # Date range for statistics
    period_start: datetime
    period_end: datetime


# Copy/Clone operation schemas

class AnalysisCopyRequest(BaseModel):
    """Schema for copying an analysis"""
    
    source_analysis_id: UUID = Field(..., description="ID of analysis to copy")
    new_name: str = Field(..., min_length=1, max_length=255, description="Name for the new analysis")
    new_description: Optional[str] = Field(None, description="Description for the new analysis")
    target_model_id: Optional[UUID] = Field(None, description="Target model (if different from source)")
    copy_scenarios: bool = Field(default=False, description="Whether to copy child scenarios (future feature)")
    
    @field_validator('new_name')
    @classmethod
    def validate_new_name(cls, v: str) -> str:
        """Validate new analysis name"""
        if not v.strip():
            raise ValueError("New analysis name cannot be empty or whitespace")
        return v.strip()


class AnalysisValidationResponse(BaseModel):
    """Schema for analysis validation results"""
    
    is_valid: bool
    validation_errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Validation details
    name_available: bool
    model_exists: bool
    user_has_permission: bool
    tenant_consistent: bool