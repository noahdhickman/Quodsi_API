# app/schemas/simulation_model.py
"""
Pydantic schemas for Model (Simulation Model) management.

These schemas define the API contracts for creating, reading, and updating
simulation models with proper validation and defaults.
"""
from pydantic import BaseModel, Field, field_validator, computed_field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class ModelBase(BaseModel):
    """Base model schema with common fields"""
    
    name: str = Field(..., min_length=1, max_length=255, description="Model name")
    description: Optional[str] = Field(None, description="Model description")


class ModelCreate(ModelBase):
    """Schema for creating a new simulation model"""
    
    # Source information
    source: str = Field(..., description="Source of the model")
    source_document_id: Optional[str] = Field(None, max_length=255, description="Source document ID (LucidChart, Miro, etc.)")
    source_url: Optional[str] = Field(None, max_length=500, description="URL to source document")
    
    # Default simulation parameters (with defaults from schema)
    reps: int = Field(default=1, ge=1, description="Default number of simulation replications")
    forecast_days: int = Field(default=30, ge=1, description="Default forecast period in days")
    random_seed: Optional[int] = Field(None, description="Default random seed for simulations")
    
    # Time configuration
    time_type: str = Field(default="clock", description="Time mode (clock or calendar)")
    one_clock_unit: Optional[str] = Field(None, description="Clock unit for clock mode")
    warmup_clock_period: Optional[Decimal] = Field(None, description="Warmup duration for clock mode")
    run_clock_period: Optional[Decimal] = Field(None, description="Run duration for clock mode")
    
    # Calendar mode parameters
    warmup_date_time: Optional[datetime] = Field(None, description="Warmup start date/time for calendar mode")
    start_date_time: Optional[datetime] = Field(None, description="Run start date/time for calendar mode")
    finish_date_time: Optional[datetime] = Field(None, description="Run finish date/time for calendar mode")
    
    # Association (optional - can be set later)
    organization_id: Optional[UUID] = Field(None, description="Associated organization ID")
    team_id: Optional[UUID] = Field(None, description="Associated team ID")
    
    # Model characteristics
    is_public: bool = Field(default=False, description="Whether model is publicly accessible")
    is_template: bool = Field(default=False, description="Whether model can be used as template")
    
    @field_validator('source')
    @classmethod
    def validate_source(cls, v: str) -> str:
        """Validate source is one of allowed values"""
        allowed_sources = ['lucidchart', 'standalone', 'miro']
        if v not in allowed_sources:
            raise ValueError(f"Source must be one of: {', '.join(allowed_sources)}")
        return v
    
    @field_validator('time_type')
    @classmethod
    def validate_time_type(cls, v: str) -> str:
        """Validate time_type is one of allowed values"""
        allowed_types = ['clock', 'calendar']
        if v not in allowed_types:
            raise ValueError(f"Time type must be one of: {', '.join(allowed_types)}")
        return v
    
    @field_validator('one_clock_unit')
    @classmethod
    def validate_clock_unit(cls, v: Optional[str]) -> Optional[str]:
        """Validate one_clock_unit is one of allowed values"""
        if v is None:
            return v
        allowed_units = ['seconds', 'minutes', 'hours', 'days']
        if v not in allowed_units:
            raise ValueError(f"Clock unit must be one of: {', '.join(allowed_units)}")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Customer Service Process",
                "description": "Simulation model for customer service workflow",
                "source": "lucidchart",
                "source_document_id": "1234-5678-9012",
                "reps": 100,
                "forecast_days": 90,
                "time_type": "clock",
                "one_clock_unit": "minutes",
                "is_template": False
            }
        }
    }


class ModelUpdate(BaseModel):
    """Schema for updating a simulation model"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    
    # Simulation parameters
    reps: Optional[int] = Field(None, ge=1)
    forecast_days: Optional[int] = Field(None, ge=1)
    random_seed: Optional[int] = Field(None)
    
    # Time configuration
    time_type: Optional[str] = Field(None)
    one_clock_unit: Optional[str] = Field(None)
    warmup_clock_period: Optional[Decimal] = Field(None)
    run_clock_period: Optional[Decimal] = Field(None)
    
    # Calendar mode parameters
    warmup_date_time: Optional[datetime] = Field(None)
    start_date_time: Optional[datetime] = Field(None)
    finish_date_time: Optional[datetime] = Field(None)
    
    # Association
    organization_id: Optional[UUID] = Field(None)
    team_id: Optional[UUID] = Field(None)
    
    # Model characteristics
    is_public: Optional[bool] = Field(None)
    is_template: Optional[bool] = Field(None)
    
    @field_validator('time_type')
    @classmethod
    def validate_time_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed_types = ['clock', 'calendar']
        if v not in allowed_types:
            raise ValueError(f"Time type must be one of: {', '.join(allowed_types)}")
        return v
    
    @field_validator('one_clock_unit')
    @classmethod
    def validate_clock_unit(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed_units = ['seconds', 'minutes', 'hours', 'days']
        if v not in allowed_units:
            raise ValueError(f"Clock unit must be one of: {', '.join(allowed_units)}")
        return v


class ModelRead(ModelBase):
    """Schema for reading model information"""
    
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    
    # Source information
    source: str
    source_document_id: Optional[str] = None
    source_url: Optional[str] = None
    
    # Simulation parameters
    reps: int
    forecast_days: int
    random_seed: Optional[int] = None
    
    # Time configuration
    time_type: str
    one_clock_unit: Optional[str] = None
    warmup_clock_period: Optional[Decimal] = None
    run_clock_period: Optional[Decimal] = None
    
    # Calendar mode parameters
    warmup_date_time: Optional[datetime] = None
    start_date_time: Optional[datetime] = None
    finish_date_time: Optional[datetime] = None
    
    # Ownership and association
    created_by_user_id: UUID
    organization_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    
    # Model characteristics
    is_public: bool
    is_template: bool
    version: int
    
    # Legacy
    blob_storage_url: Optional[str] = None
    
    # Computed fields for convenience
    @computed_field
    @property
    def is_clock_mode(self) -> bool:
        """Check if model uses clock-based time"""
        return self.time_type == "clock"
    
    @computed_field
    @property
    def is_calendar_mode(self) -> bool:
        """Check if model uses calendar-based time"""
        return self.time_type == "calendar"

    model_config = {"from_attributes": True}


class ModelSummary(BaseModel):
    """Lightweight model schema for listings"""
    
    id: UUID
    name: str
    description: Optional[str] = None
    source: str
    created_by_user_id: UUID
    organization_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    is_public: bool
    is_template: bool
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ModelListResponse(BaseModel):
    """Paginated response for model listings"""
    
    models: List[ModelSummary]
    total: int
    skip: int
    limit: int


class ModelTemplateCreate(BaseModel):
    """Schema for creating a model from template"""
    
    template_model_id: UUID = Field(..., description="ID of template model to copy")
    new_model_name: str = Field(..., min_length=1, max_length=255, description="Name for new model")
    description: Optional[str] = Field(None, description="Description for new model")
    
    # Optional overrides
    organization_id: Optional[UUID] = Field(None, description="Associate with different organization")
    team_id: Optional[UUID] = Field(None, description="Associate with different team")


class ModelPermissionContext(BaseModel):
    """Schema for permission context (future integration)"""
    
    model_id: UUID
    user_id: UUID
    can_read: bool = False
    can_write: bool = False
    can_execute: bool = False
    can_admin: bool = False
    permission_source: Optional[str] = None  # 'direct', 'team', 'organization'


class ModelAccessInfo(BaseModel):
    """Schema for model access information (future integration)"""
    
    model: ModelRead
    permissions: ModelPermissionContext
    last_accessed_at: Optional[datetime] = None
    access_count: Optional[int] = None