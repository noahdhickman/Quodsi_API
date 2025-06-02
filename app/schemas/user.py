# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr = Field(..., description="User's email address")
    display_name: str = Field(..., min_length=1, max_length=255, description="User's display name")


class UserCreate(UserBase):
    """Schema for creating a new user"""
    identity_provider: str = Field(..., description="Identity provider (entra_id, google, etc.)")
    identity_provider_id: str = Field(..., description="Provider-specific user ID")
    tenant_id: UUID = Field(..., description="Tenant ID for the user")
    status: str = Field(default="active", description="Initial user status")
    user_metadata: Optional[str] = Field(None, description="Additional user metadata (JSON)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john.doe@acme.com",
                "display_name": "John Doe",
                "identity_provider": "entra_id",
                "identity_provider_id": "550e8400-e29b-41d4-a716-446655440000",
                "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "active"
            }
        }
    )


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[str] = Field(None, description="User status")
    user_metadata: Optional[str] = Field(None, description="User metadata (JSON)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "display_name": "John D. Smith",
                "user_metadata": '{"timezone": "America/New_York", "theme": "dark"}'
            }
        }
    )


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile information."""
    display_name: Optional[str] = None
    user_metadata: Optional[str] = None  # JSON string for flexible metadata
    
    @field_validator('display_name')
    @classmethod
    def validate_display_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.strip()) < 2:
            raise ValueError("Display name must be at least 2 characters long")
        return v.strip() if v else None


class UserInDB(UserBase):
    """User schema as stored in database"""
    id: UUID
    tenant_id: UUID
    identity_provider: str
    identity_provider_id: str
    last_login_at: Optional[datetime] = None
    login_count: int
    total_usage_minutes: int
    last_session_start: Optional[datetime] = None
    last_active_at: Optional[datetime] = None
    status: str
    user_metadata: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    
    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """User schema for API responses (excludes sensitive data)"""
    id: UUID
    email: EmailStr
    display_name: str
    status: str
    login_count: int
    total_usage_minutes: int
    last_login_at: Optional[datetime] = None
    last_active_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Tenant information
    tenant_id: UUID
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "john.doe@acme.com",
                "display_name": "John Doe",
                "status": "active",
                "login_count": 42,
                "total_usage_minutes": 1440,
                "last_login_at": "2025-01-20T10:30:00Z",
                "last_active_at": "2025-01-20T15:45:00Z",
                "created_at": "2024-12-01T09:00:00Z",
                "updated_at": "2025-01-20T15:45:00Z",
                "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
    )


class UserSummary(BaseModel):
    """Lightweight user schema for listings and references"""
    id: UUID = Field(..., description="User unique identifier")
    email: EmailStr = Field(..., description="User's email address")
    display_name: str = Field(..., description="User's display name")
    status: str = Field(..., description="User status")
    
    model_config = ConfigDict(from_attributes=True)


class UserWithTenant(UserResponse):
    """User schema with tenant information included"""
    tenant: Optional[dict] = Field(None, description="Tenant information")
    
    model_config = ConfigDict(from_attributes=True)


class UserRegistration(BaseModel):
    """
    Schema for user registration that includes both user and tenant information.
    
    This schema is used when a user signs up and creates a new organization.
    """
    email: EmailStr
    display_name: str
    identity_provider: str = "local_dev_registration"
    identity_provider_id: Optional[str] = None
    
    # Tenant/Organization information
    company_name: str
    tenant_slug: Optional[str] = None  # Auto-generated if not provided
    
    @field_validator('company_name')
    @classmethod
    def validate_company_name(cls, v: str) -> str:
        if not v or len(v.strip()) < 2:
            raise ValueError("Company name must be at least 2 characters long")
        return v.strip()
    
    @field_validator('tenant_slug', mode='before')
    @classmethod
    def validate_tenant_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Basic slug validation
        import re
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Tenant slug may only contain lowercase letters, numbers, and hyphens")
        return v


class AuthenticationResult(BaseModel):
    """Result of user authentication process."""
    success: bool
    user: Optional[UserResponse] = None
    tenant: Optional[Dict[str, Any]] = None
    message: str
    requires_setup: bool = False


class UserActivitySummary(BaseModel):
    """Summary of user activity and engagement."""
    user_id: str
    total_logins: int
    total_usage_minutes: int
    last_login_at: Optional[datetime] = None
    days_since_registration: int
    is_recently_active: bool
    engagement_level: str  # "high", "medium", "low", "inactive"


class LoginStats(BaseModel):
    """Schema for login statistics"""
    user_id: UUID
    login_count: int
    total_usage_minutes: int
    last_login_at: Optional[datetime] = None
    last_session_start: Optional[datetime] = None
    last_active_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)