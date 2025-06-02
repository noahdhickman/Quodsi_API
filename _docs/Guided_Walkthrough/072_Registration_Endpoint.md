# Module 7.2: Registration Endpoint Implementation

## Purpose
Implement user and tenant registration endpoints using the mock authentication system and standardized API responses.

## Prerequisites
- Completed Module 7.1 (API Response Standard and Mock Authentication)
- Registration service layer implemented
- Response helpers and mock authentication dependencies available

---

## Overview

In this module, we'll create:
1. **Registration Request/Response Models** - Pydantic models for API contracts
2. **Registration Endpoints** - FastAPI endpoints for user/tenant registration
3. **Error Handling** - Comprehensive error handling for registration scenarios
4. **Endpoint Testing** - Manual testing procedures for registration endpoints

## Learning Objectives

By the end of this module, you'll understand:
- How to create FastAPI endpoints with proper request/response models
- How to integrate service layers with API endpoints
- How to handle various error scenarios in registration
- How to use the standardized response format consistently

---

## Part 1: Registration Request/Response Models

### 1.1 Registration Request Models

Create registration-specific schemas in `app/schemas/registration.py`:

```python
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
```

---

## Part 2: Registration Endpoints

### 2.1 Create Registration Router

Create `app/api/routers/registration.py`:

```python
# app/api/routers/registration.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.services.registration_service import RegistrationService
from app.schemas.registration import (
    TenantRegistrationRequest, 
    UserRegistrationRequest,
    RegistrationResponse,
    TenantRegistrationResponse
)
from app.api.response_helpers import (
    create_success_response, 
    create_error_response,
    create_validation_error_response
)
from app.api.deps import get_current_user_mock, MockCurrentUser
from pydantic import ValidationError

router = APIRouter(prefix="/registration", tags=["registration"])

@router.post("/tenant", response_model=dict)
async def register_tenant(
    request: TenantRegistrationRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new tenant with admin user.
    
    This endpoint creates both a tenant and its first admin user.
    """
    try:
        registration_service = RegistrationService(db)
        
        # Register tenant and admin user
        result = registration_service.register_tenant_with_admin(
            tenant_name=request.name,
            domain=request.domain,
            admin_email=request.admin_email,
            admin_password=request.admin_password,
            admin_display_name=request.admin_display_name
        )
        
        # Create response data
        response_data = TenantRegistrationResponse(
            tenant_id=result.tenant.id,
            tenant_name=result.tenant.name,
            domain=result.tenant.domain,
            admin_user_id=result.admin_user.id,
            admin_email=result.admin_user.email,
            message="Tenant and admin user registered successfully"
        )
        
        return create_success_response(
            data=response_data.dict(),
            tenant_id=result.tenant.id
        )
        
    except ValueError as e:
        return create_error_response(
            code="REGISTRATION_ERROR",
            message=str(e)
        )
    except IntegrityError as e:
        return create_error_response(
            code="DUPLICATE_ERROR",
            message="Tenant domain or admin email already exists"
        )
    except Exception as e:
        return create_error_response(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred during registration"
        )

@router.post("/user", response_model=dict)
async def register_user(
    request: UserRegistrationRequest,
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Register a new user within the current tenant.
    
    This endpoint creates a new user within the authenticated user's tenant.
    """
    try:
        registration_service = RegistrationService(db)
        
        # Register user in current tenant
        user = registration_service.register_user_in_tenant(
            tenant_id=current_user.tenant_id,
            email=request.email,
            password=request.password,
            display_name=request.display_name,
            role=request.role
        )
        
        # Create response data
        response_data = RegistrationResponse(
            user_id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            display_name=user.display_name,
            message="User registered successfully"
        )
        
        return create_success_response(
            data=response_data.dict(),
            tenant_id=current_user.tenant_id
        )
        
    except ValueError as e:
        return create_error_response(
            code="REGISTRATION_ERROR",
            message=str(e),
            tenant_id=current_user.tenant_id
        )
    except IntegrityError as e:
        return create_error_response(
            code="DUPLICATE_ERROR",
            message="User email already exists in this tenant",
            tenant_id=current_user.tenant_id
        )
    except Exception as e:
        return create_error_response(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred during user registration",
            tenant_id=current_user.tenant_id
        )
```

---

## Part 3: Error Handling and Validation

### 3.1 Enhanced Error Handling

The registration endpoints include comprehensive error handling for:

1. **Validation Errors**: Pydantic validation failures
2. **Business Logic Errors**: Service layer validation (duplicate emails, etc.)
3. **Database Errors**: Integrity constraints and connection issues
4. **Unexpected Errors**: Catch-all for system errors

### 3.2 Custom Exception Handler (Optional)

Create `app/api/exception_handlers.py` for global error handling:

```python
# app/api/exception_handlers.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from app.api.response_helpers import create_error_response, create_validation_error_response

async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors"""
    return JSONResponse(
        status_code=422,
        content=create_validation_error_response(exc.errors())
    )

async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors"""
    return JSONResponse(
        status_code=409,
        content=create_error_response(
            code="INTEGRITY_ERROR",
            message="Data integrity constraint violation"
        )
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with standard format"""
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            code="HTTP_ERROR",
            message=exc.detail
        )
    )
```

---

## Part 4: Integration and Testing

### 4.1 Update Main Router

Update `app/api/__init__.py` to include the registration router:

```python
# app/api/__init__.py
from fastapi import APIRouter
from app.api.routers.registration import router as registration_router

api_router = APIRouter(prefix="/api")
api_router.include_router(registration_router)
```

### 4.2 Update Main Application

Update `app/main.py` to include the API router:

```python
# app/main.py
from fastapi import FastAPI
from app.api import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Quodsi API"
)

# Include API router
app.include_router(api_router)

@app.get("/")
def read_root():
    return {"message": "Quodsi API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

