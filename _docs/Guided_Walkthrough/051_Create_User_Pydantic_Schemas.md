# Step 2: Create User Pydantic Schemas

## 2.1 Create User Schema File
Create `app/schemas/user.py`:

```python
# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
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


class UserWithTenant(UserResponse):
    """User schema with tenant information included"""
    tenant: Optional[dict] = Field(None, description="Tenant information")
    
    model_config = ConfigDict(from_attributes=True)


class UserRegistration(BaseModel):
    """Schema for user registration (combines user and tenant creation)"""
    # User information
    email: EmailStr
    display_name: str
    identity_provider: str = Field(default="entra_id")
    identity_provider_id: str
    
    # Tenant information
    company_name: str = Field(..., min_length=1, max_length=255)
    tenant_slug: Optional[str] = Field(None, description="Custom tenant slug (auto-generated if not provided)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "admin@newcompany.com",
                "display_name": "Jane Smith",
                "identity_provider": "entra_id",
                "identity_provider_id": "660f9500-f39c-52e5-b827-557766551111",
                "company_name": "New Company Inc",
                "tenant_slug": "new-company"
            }
        }
    )


class LoginStats(BaseModel):
    """Schema for login statistics"""
    user_id: UUID
    login_count: int
    total_usage_minutes: int
    last_login_at: Optional[datetime] = None
    last_session_start: Optional[datetime] = None
    last_active_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
```

## 2.2 Update Schemas __init__.py
Update `app/schemas/__init__.py`:

```python
# app/schemas/__init__.py
from .tenant import (
    TenantCreate, TenantRead, TenantUpdate, TenantSummary
)
from .user import (
    UserBase, UserCreate, UserUpdate, UserInDB, UserResponse, 
    UserWithTenant, UserRegistration, LoginStats
)

__all__ = [
    # Tenant schemas
    "TenantCreate", "TenantRead", "TenantUpdate", "TenantSummary",
    # User schemas
    "UserBase", "UserCreate", "UserUpdate", "UserInDB", "UserResponse", 
    "UserWithTenant", "UserRegistration", "LoginStats"
]
```