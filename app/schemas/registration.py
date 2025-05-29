# app/schemas/registration.py
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from uuid import UUID

class TenantRegistrationRequest(BaseModel):
    """Request model for tenant registration"""
    name: str
    domain: str
    admin_email: EmailStr
    admin_password: str
    admin_display_name: str
    
    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Tenant name must be at least 2 characters')
        return v.strip()
    
    @validator('domain')
    def validate_domain(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Domain must be at least 3 characters')
        return v.strip().lower()
    
    @validator('admin_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserRegistrationRequest(BaseModel):
    """Request model for user registration within existing tenant"""
    email: EmailStr
    password: str
    display_name: str
    role: Optional[str] = "user"
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v
    
    @validator('display_name')
    def validate_display_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Display name must be at least 2 characters')
        return v.strip()

class RegistrationResponse(BaseModel):
    """Response model for successful registration"""
    user_id: UUID
    tenant_id: UUID
    email: str
    display_name: str
    message: str

class TenantRegistrationResponse(BaseModel):
    """Response model for tenant registration"""
    tenant_id: UUID
    tenant_name: str
    domain: str
    admin_user_id: UUID
    admin_email: str
    message: str