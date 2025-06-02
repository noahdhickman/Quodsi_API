# Step 2: Create Tenant Pydantic Schemas

## 2.1 Implement Tenant Schemas
Create `app/schemas/tenant.py`:

```python
"""
Pydantic schemas for Tenant model.

These schemas define the data structures for API requests and responses,
providing validation, serialization, and documentation.
"""
from pydantic import BaseModel, EmailStr, field_validator, computed_field
from typing import Optional
from uuid import UUID
from datetime import datetime
import re

class TenantBase(BaseModel):
    """Base tenant schema with common fields"""
    
    name: str
    subdomain: Optional[str] = None
    slug: Optional[str] = None
    plan_type: str = 'trial'
    status: str = 'trial'

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate tenant name"""
        if not v or len(v.strip()) < 2:
            raise ValueError('Tenant name must be at least 2 characters long')
        if len(v) > 255:
            raise ValueError('Tenant name must be less than 255 characters')
        return v.strip()

    @field_validator('subdomain', 'slug')
    @classmethod
    def validate_url_friendly(cls, v: Optional[str]) -> Optional[str]:
        """Validate subdomain and slug are URL-friendly"""
        if v is None:
            return v
        
        # Convert to lowercase and strip
        v = v.lower().strip()
        
        # Check format: only lowercase letters, numbers, and hyphens
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Must contain only lowercase letters, numbers, and hyphens")
        
        # Check length
        if len(v) < 2 or len(v) > 50:
            raise ValueError("Must be between 2 and 50 characters")
        
        # Can't start or end with hyphen
        if v.startswith('-') or v.endswith('-'):
            raise ValueError("Cannot start or end with a hyphen")
        
        # Reserved subdomains
        reserved = ['www', 'api', 'admin', 'app', 'mail', 'ftp', 'blog', 'help', 'support']
        if v in reserved:
            raise ValueError(f"'{v}' is a reserved subdomain")
        
        return v

    @field_validator('plan_type')
    @classmethod
    def validate_plan_type(cls, v: str) -> str:
        """Validate plan type"""
        allowed_plans = ['trial', 'starter', 'professional', 'enterprise']
        if v not in allowed_plans:
            raise ValueError(f"Plan type must be one of: {', '.join(allowed_plans)}")
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate tenant status"""
        allowed_statuses = ['trial', 'active', 'suspended', 'cancelled', 'deleted']
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v

class TenantCreate(TenantBase):
    """Schema for creating a new tenant"""
    
    # Required fields for creation
    name: str
    
    # Optional billing information
    billing_email: Optional[EmailStr] = None

    @computed_field
    @property
    def computed_slug(self) -> str:
        """Auto-generate slug from name if not provided"""
        if self.slug:
            return self.slug
        
        # Convert name to URL-friendly slug
        slug = self.name.lower()
        # Replace spaces and special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_-]+', '-', slug)
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        
        return slug[:50]  # Limit length

    @computed_field
    @property
    def computed_subdomain(self) -> str:
        """Auto-generate subdomain from slug if not provided"""
        if self.subdomain:
            return self.subdomain
        
        return self.computed_slug

class TenantRead(TenantBase):
    """Schema for reading tenant information"""
    
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    # Usage limits
    max_users: int
    max_models: int
    max_scenarios_per_month: int
    max_storage_gb: float
    
    # Lifecycle
    trial_expires_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    
    # Billing
    stripe_customer_id: Optional[str] = None
    billing_email: Optional[EmailStr] = None

    @computed_field
    @property
    def full_domain(self) -> str:
        """Computed full domain"""
        return f"{self.subdomain}.quodsi.com"

    @computed_field
    @property
    def is_trial(self) -> bool:
        """Computed trial status"""
        return self.plan_type == 'trial' or self.status == 'trial'

    @computed_field
    @property
    def is_active(self) -> bool:
        """Computed active status"""
        return self.status == 'active'

    class Config:
        from_attributes = True

class TenantUpdate(BaseModel):
    """Schema for updating tenant information"""
    
    name: Optional[str] = None
    plan_type: Optional[str] = None
    status: Optional[str] = None
    max_users: Optional[int] = None
    max_models: Optional[int] = None
    max_scenarios_per_month: Optional[int] = None
    max_storage_gb: Optional[float] = None
    billing_email: Optional[EmailStr] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate tenant name if provided"""
        if v is None:
            return v
        if len(v.strip()) < 2:
            raise ValueError('Tenant name must be at least 2 characters long')
        if len(v) > 255:
            raise ValueError('Tenant name must be less than 255 characters')
        return v.strip()

class TenantSummary(BaseModel):
    """Lightweight tenant schema for lists and references"""
    
    id: UUID
    name: str
    subdomain: str
    status: str
    plan_type: str
    is_trial: bool
    
    class Config:
        from_attributes = True
```

## 2.2 Update Schemas Package
Update `app/schemas/__init__.py`:

```python
"""
Pydantic schemas package.

Contains all request/response schemas for API validation and serialization.
"""

from .tenant import TenantCreate, TenantRead, TenantUpdate, TenantSummary

__all__ = [
    "TenantCreate", 
    "TenantRead", 
    "TenantUpdate", 
    "TenantSummary"
]
```
