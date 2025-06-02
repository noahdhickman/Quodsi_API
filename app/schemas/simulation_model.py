# app/schemas/simulation_model.py
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class ModelBase(BaseModel):
    """Base schema with common model fields"""

    name: str = Field(..., max_length=255, description="Model name")
    description: Optional[str] = Field(None, description="Model description")
    source: str = Field(
        ..., description="Source type: lucidchart, miro, manual, import"
    )
    source_document_id: Optional[str] = Field(None, max_length=255)
    source_url: Optional[str] = None

    # Simulation parameters with defaults
    reps: int = Field(1, ge=1, description="Number of simulation repetitions")
    forecast_days: int = Field(30, ge=1, description="Forecast period in days")
    random_seed: Optional[int] = None
    time_type: str = Field("calendar", description="Time type: calendar or clock")
    one_clock_unit: Optional[str] = Field(
        None, description="Clock unit: minutes, hours, days, weeks"
    )
    warmup_clock_period: Optional[int] = None
    run_clock_period: Optional[int] = None

    # Date/time parameters
    warmup_date_time: Optional[datetime] = None
    start_date_time: Optional[datetime] = None
    finish_date_time: Optional[datetime] = None

    # Association fields
    organization_id: Optional[UUID] = None
    team_id: Optional[UUID] = None

    # Flags
    is_public: bool = False
    is_template: bool = False

    @validator("source")
    def validate_source(cls, v):
        allowed_sources = {"lucidchart", "miro", "manual", "import"}
        if v not in allowed_sources:
            raise ValueError(f'Source must be one of: {", ".join(allowed_sources)}')
        return v

    @validator("time_type")
    def validate_time_type(cls, v):
        allowed_types = {"calendar", "clock"}
        if v not in allowed_types:
            raise ValueError(f'Time type must be one of: {", ".join(allowed_types)}')
        return v

    @validator("one_clock_unit")
    def validate_clock_unit(cls, v):
        if v is not None:
            allowed_units = {"minutes", "hours", "days", "weeks"}
            if v not in allowed_units:
                raise ValueError(
                    f'Clock unit must be one of: {", ".join(allowed_units)}'
                )
        return v


class ModelCreate(ModelBase):
    """Schema for creating a new model"""

    # Only name and source are truly required for creation
    # Other fields have defaults or can be set later
    pass


class ModelUpdate(BaseModel):
    """Schema for updating an existing model"""

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None

    # Simulation parameters
    reps: Optional[int] = Field(None, ge=1)
    forecast_days: Optional[int] = Field(None, ge=1)
    random_seed: Optional[int] = None
    time_type: Optional[str] = None
    one_clock_unit: Optional[str] = None
    warmup_clock_period: Optional[int] = None
    run_clock_period: Optional[int] = None

    # Date/time parameters
    warmup_date_time: Optional[datetime] = None
    start_date_time: Optional[datetime] = None
    finish_date_time: Optional[datetime] = None

    # Association fields
    organization_id: Optional[UUID] = None
    team_id: Optional[UUID] = None

    # Flags
    is_public: Optional[bool] = None
    is_template: Optional[bool] = None

    @validator("time_type")
    def validate_time_type(cls, v):
        if v is not None:
            allowed_types = {"calendar", "clock"}
            if v not in allowed_types:
                raise ValueError(
                    f'Time type must be one of: {", ".join(allowed_types)}'
                )
        return v

    @validator("one_clock_unit")
    def validate_clock_unit(cls, v):
        if v is not None:
            allowed_units = {"minutes", "hours", "days", "weeks"}
            if v not in allowed_units:
                raise ValueError(
                    f'Clock unit must be one of: {", ".join(allowed_units)}'
                )
        return v


class UserSummary(BaseModel):
    """Summary of user info for model responses"""

    id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]

    class Config:
        from_attributes = True


class OrganizationSummary(BaseModel):
    """Summary of organization info for model responses"""

    id: UUID
    name: str

    class Config:
        from_attributes = True


class TeamSummary(BaseModel):
    """Summary of team info for model responses"""

    id: UUID
    name: str

    class Config:
        from_attributes = True


class ModelRead(ModelBase):
    """Schema for reading model data"""

    id: UUID
    tenant_id: UUID
    created_by_user_id: UUID
    version: int
    blob_storage_url: Optional[str] = None

    # Timestamps from BaseEntity
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False

    # Related entities (optional - can be populated via joins)
    created_by_user: Optional[UserSummary] = None
    organization: Optional[OrganizationSummary] = None
    team: Optional[TeamSummary] = None

    class Config:
        from_attributes = True


class ModelSummary(BaseModel):
    """Lightweight schema for listing models"""

    id: UUID
    name: str
    description: Optional[str]
    source: str
    is_public: bool
    is_template: bool
    version: int
    created_at: datetime
    created_by_user_id: UUID

    class Config:
        from_attributes = True


class ModelCreateFromTemplate(BaseModel):
    """Schema for creating a model from a template"""

    name: str = Field(..., max_length=255, description="Name for the new model")
    description: Optional[str] = Field(
        None, description="Description for the new model"
    )
    organization_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
