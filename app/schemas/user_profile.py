# app/schemas/user_profile.py
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class UserProfileResponse(BaseModel):
    """Response model for user profile information"""
    id: UUID
    tenant_id: UUID
    email: str
    display_name: str
    status: str
    identity_provider: str
    identity_provider_id: str
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    login_count: int = 0
    
    # Computed field for compatibility
    @property
    def is_active(self) -> bool:
        """Computed property for active status"""
        return self.status == 'active'
    
    class Config:
        from_attributes = True

class UserProfileUpdateRequest(BaseModel):
    """Request model for updating user profile"""
    display_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    
    @validator('display_name')
    def validate_display_name(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError('Display name must be at least 2 characters')
        return v.strip() if v else v
    
    @validator('role')
    def validate_role(cls, v):
        if v is not None:
            allowed_roles = ['admin', 'user', 'viewer']
            if v not in allowed_roles:
                raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v

class PasswordUpdateRequest(BaseModel):
    """Request model for updating user password"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters')
        return v

class UserSearchRequest(BaseModel):
    """Request model for user search"""
    search_term: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    limit: Optional[int] = 50
    offset: Optional[int] = 0
    
    @validator('limit')
    def validate_limit(cls, v):
        if v is not None and (v < 1 or v > 100):
            raise ValueError('Limit must be between 1 and 100')
        return v
    
    @validator('offset')
    def validate_offset(cls, v):
        if v is not None and v < 0:
            raise ValueError('Offset must be non-negative')
        return v

class UserListResponse(BaseModel):
    """Response model for user listing"""
    users: List[UserProfileResponse]
    total_count: int
    limit: int
    offset: int
