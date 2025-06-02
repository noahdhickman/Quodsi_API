# Module 7.3: User Profile Endpoints

## Purpose
Implement user profile management endpoints including profile retrieval, updates, and user management operations.

## Prerequisites
- Completed Module 7.1 (API Response Standard and Mock Authentication)
- Completed Module 7.2 (Registration Endpoint Implementation)
- User service layer implemented
- Mock authentication system available

---

## Overview

In this module, we'll create:
1. **User Profile Request/Response Models** - API contracts for user operations
2. **Profile Management Endpoints** - CRUD operations for user profiles
3. **User Search and Listing** - Endpoints for user discovery within tenants
4. **Profile Security** - Proper access controls and validation

## Learning Objectives

By the end of this module, you'll understand:
- How to implement CRUD operations in FastAPI
- How to secure endpoints with proper access controls
- How to handle user profile updates safely
- How to implement search and filtering functionality

---

## Part 1: User Profile Models

### 1.1 Profile Request/Response Models

Create `app/schemas/user_profile.py`:

```python
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
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
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
```

---

## Part 2: User Profile Endpoints

### 2.1 Create User Profile Router

Create `app/api/routers/user_profile.py`:

```python
# app/api/routers/user_profile.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.services.user_service import UserService
from app.schemas.user_profile import (
    UserProfileResponse,
    UserProfileUpdateRequest,
    PasswordUpdateRequest,
    UserSearchRequest,
    UserListResponse
)
from app.api.response_helpers import (
    create_success_response, 
    create_error_response
)
from app.api.deps import get_current_user_mock, get_current_user_from_db, MockCurrentUser
from app.db.models.user import User

router = APIRouter(prefix="/users", tags=["user-profile"])

@router.get("/me", response_model=dict)
async def get_my_profile(
    current_user: User = Depends(get_current_user_from_db)
):
    """
    Get the current user's profile information.
    """
    try:
        profile_data = UserProfileResponse.from_orm(current_user)
        
        return create_success_response(
            data=profile_data.dict(),
            tenant_id=current_user.tenant_id
        )
        
    except Exception as e:
        return create_error_response(
            code="PROFILE_ERROR",
            message="Unable to retrieve profile information",
            tenant_id=current_user.tenant_id
        )

@router.put("/me", response_model=dict)
async def update_my_profile(
    request: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user_from_db),
    db: Session = Depends(get_db)
):
    """
    Update the current user's profile information.
    """
    try:
        user_service = UserService(db)
        
        # Update user profile
        updated_user = user_service.update_user_profile(
            user_id=current_user.id,
            display_name=request.display_name,
            role=request.role,
            is_active=request.is_active
        )
        
        profile_data = UserProfileResponse.from_orm(updated_user)
        
        return create_success_response(
            data={
                **profile_data.dict(),
                "message": "Profile updated successfully"
            },
            tenant_id=current_user.tenant_id
        )
        
    except ValueError as e:
        return create_error_response(
            code="VALIDATION_ERROR",
            message=str(e),
            tenant_id=current_user.tenant_id
        )
    except Exception as e:
        return create_error_response(
            code="UPDATE_ERROR",
            message="Unable to update profile",
            tenant_id=current_user.tenant_id
        )

@router.post("/me/password", response_model=dict)
async def change_password(
    request: PasswordUpdateRequest,
    current_user: User = Depends(get_current_user_from_db),
    db: Session = Depends(get_db)
):
    """
    Change the current user's password.
    """
    try:
        user_service = UserService(db)
        
        # Verify current password and update
        success = user_service.change_user_password(
            user_id=current_user.id,
            current_password=request.current_password,
            new_password=request.new_password
        )
        
        if not success:
            return create_error_response(
                code="AUTHENTICATION_ERROR",
                message="Current password is incorrect",
                tenant_id=current_user.tenant_id
            )
        
        return create_success_response(
            data={"message": "Password changed successfully"},
            tenant_id=current_user.tenant_id
        )
        
    except ValueError as e:
        return create_error_response(
            code="VALIDATION_ERROR",
            message=str(e),
            tenant_id=current_user.tenant_id
        )
    except Exception as e:
        return create_error_response(
            code="PASSWORD_ERROR",
            message="Unable to change password",
            tenant_id=current_user.tenant_id
        )

@router.get("/{user_id}", response_model=dict)
async def get_user_profile(
    user_id: str,
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Get another user's profile information (within same tenant).
    """
    try:
        user_service = UserService(db)
        
        # Get user profile within same tenant
        user = user_service.get_user_by_id_in_tenant(
            user_id=user_id,
            tenant_id=current_user.tenant_id
        )
        
        if not user:
            return create_error_response(
                code="USER_NOT_FOUND",
                message="User not found in your tenant",
                tenant_id=current_user.tenant_id
            )
        
        profile_data = UserProfileResponse.from_orm(user)
        
        return create_success_response(
            data=profile_data.dict(),
            tenant_id=current_user.tenant_id
        )
        
    except Exception as e:
        return create_error_response(
            code="PROFILE_ERROR",
            message="Unable to retrieve user profile",
            tenant_id=current_user.tenant_id
        )

@router.get("/", response_model=dict)
async def list_users(
    search_term: Optional[str] = Query(None, description="Search in email and display name"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: Optional[int] = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: Optional[int] = Query(0, ge=0, description="Number of results to skip"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    List users within the current tenant with optional filtering.
    """
    try:
        user_service = UserService(db)
        
        # Create search request
        search_request = UserSearchRequest(
            search_term=search_term,
            role=role,
            is_active=is_active,
            limit=limit,
            offset=offset
        )
        
        # Get users with search criteria
        users, total_count = user_service.search_users_in_tenant(
            tenant_id=current_user.tenant_id,
            search_term=search_request.search_term,
            role=search_request.role,
            is_active=search_request.is_active,
            limit=search_request.limit,
            offset=search_request.offset
        )
        
        # Convert to response models
        user_profiles = [UserProfileResponse.from_orm(user) for user in users]
        
        response_data = UserListResponse(
            users=user_profiles,
            total_count=total_count,
            limit=limit,
            offset=offset
        )
        
        return create_success_response(
            data=response_data.dict(),
            tenant_id=current_user.tenant_id
        )
        
    except Exception as e:
        return create_error_response(
            code="SEARCH_ERROR",
            message="Unable to search users",
            tenant_id=current_user.tenant_id
        )

@router.put("/{user_id}", response_model=dict)
async def update_user_profile(
    user_id: str,
    request: UserProfileUpdateRequest,
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Update another user's profile (admin operation).
    
    Note: In a real application, you'd check if current_user has admin privileges.
    """
    try:
        user_service = UserService(db)
        
        # Verify user exists in same tenant
        user = user_service.get_user_by_id_in_tenant(
            user_id=user_id,
            tenant_id=current_user.tenant_id
        )
        
        if not user:
            return create_error_response(
                code="USER_NOT_FOUND",
                message="User not found in your tenant",
                tenant_id=current_user.tenant_id
            )
        
        # Update user profile
        updated_user = user_service.update_user_profile(
            user_id=user_id,
            display_name=request.display_name,
            role=request.role,
            is_active=request.is_active
        )
        
        profile_data = UserProfileResponse.from_orm(updated_user)
        
        return create_success_response(
            data={
                **profile_data.dict(),
                "message": "User profile updated successfully"
            },
            tenant_id=current_user.tenant_id
        )
        
    except ValueError as e:
        return create_error_response(
            code="VALIDATION_ERROR",
            message=str(e),
            tenant_id=current_user.tenant_id
        )
    except Exception as e:
        return create_error_response(
            code="UPDATE_ERROR",
            message="Unable to update user profile",
            tenant_id=current_user.tenant_id
        )

@router.delete("/{user_id}", response_model=dict)
async def deactivate_user(
    user_id: str,
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Deactivate a user (soft delete).
    
    Note: In a real application, you'd check if current_user has admin privileges.
    """
    try:
        user_service = UserService(db)
        
        # Verify user exists in same tenant
        user = user_service.get_user_by_id_in_tenant(
            user_id=user_id,
            tenant_id=current_user.tenant_id
        )
        
        if not user:
            return create_error_response(
                code="USER_NOT_FOUND",
                message="User not found in your tenant",
                tenant_id=current_user.tenant_id
            )
        
        # Prevent self-deactivation
        if str(user.id) == str(current_user.user_id):
            return create_error_response(
                code="SELF_DEACTIVATION_ERROR",
                message="Cannot deactivate your own account",
                tenant_id=current_user.tenant_id
            )
        
        # Deactivate user
        deactivated_user = user_service.deactivate_user(user_id=user_id)
        
        return create_success_response(
            data={
                "user_id": str(deactivated_user.id),
                "email": deactivated_user.email,
                "is_active": deactivated_user.is_active,
                "message": "User deactivated successfully"
            },
            tenant_id=current_user.tenant_id
        )
        
    except Exception as e:
        return create_error_response(
            code="DEACTIVATION_ERROR",
            message="Unable to deactivate user",
            tenant_id=current_user.tenant_id
        )
```

---

## Part 3: Service Layer Updates

### 3.1 Enhanced User Service Methods

Update `app/services/user_service.py` to include the new methods needed by the endpoints:

```python
# Additional methods for app/services/user_service.py

def change_user_password(self, user_id: UUID, current_password: str, new_password: str) -> bool:
    """
    Change a user's password after verifying the current password.
    
    Returns True if successful, False if current password is incorrect.
    """
    user = self.get_user_by_id(user_id)
    if not user:
        raise ValueError("User not found")
    
    # Verify current password (you'll need to implement password hashing)
    # For now, this is a placeholder - you should use proper password hashing
    if not self._verify_password(current_password, user.password_hash):
        return False
    
    # Hash new password and update
    user.password_hash = self._hash_password(new_password)
    user.updated_at = datetime.utcnow()
    
    self.db.commit()
    return True

def get_user_by_id_in_tenant(self, user_id: str, tenant_id: UUID) -> Optional[User]:
    """Get user by ID within a specific tenant"""
    return self.db.query(User).filter(
        User.id == user_id,
        User.tenant_id == tenant_id,
        User.is_deleted == False
    ).first()

def search_users_in_tenant(
    self, 
    tenant_id: UUID, 
    search_term: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0
) -> tuple[List[User], int]:
    """
    Search users within a tenant with filtering and pagination.
    
    Returns tuple of (users, total_count)
    """
    query = self.db.query(User).filter(
        User.tenant_id == tenant_id,
        User.is_deleted == False
    )
    
    # Apply search term filter
    if search_term:
        search_pattern = f"%{search_term}%"
        query = query.filter(
            (User.email.ilike(search_pattern)) | 
            (User.display_name.ilike(search_pattern))
        )
    
    # Apply role filter
    if role:
        query = query.filter(User.role == role)
    
    # Apply active status filter
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # Get total count before pagination
    total_count = query.count()
    
    # Apply pagination
    users = query.offset(offset).limit(limit).all()
    
    return users, total_count

def deactivate_user(self, user_id: UUID) -> User:
    """Deactivate a user (soft delete)"""
    user = self.get_user_by_id(user_id)
    if not user:
        raise ValueError("User not found")
    
    user.is_active = False
    user.updated_at = datetime.utcnow()
    
    self.db.commit()
    return user

def _verify_password(self, password: str, password_hash: str) -> bool:
    """Verify password against hash - implement proper password hashing"""
    # Placeholder - implement with bcrypt or similar
    return password == password_hash  # TEMPORARY - NOT SECURE

def _hash_password(self, password: str) -> str:
    """Hash password - implement proper password hashing"""
    # Placeholder - implement with bcrypt or similar
    return password  # TEMPORARY - NOT SECURE
```

---

## Part 4: Integration and Testing

### 4.1 Update API Router

Update `app/api/__init__.py` to include the user profile router:

```python
# app/api/__init__.py
from fastapi import APIRouter
from app.api.routers.registration import router as registration_router
from app.api.routers.user_profile import router as user_profile_router

api_router = APIRouter(prefix="/api")
api_router.include_router(registration_router)
api_router.include_router(user_profile_router)
```

### 4.2 Manual Testing Procedures

#### Test 1: Get Current User Profile

```bash
curl -X GET "http://localhost:8000/api/users/me" \
     -H "X-Mock-User-Id: 123e4567-e89b-12d3-a456-426614174000" \
     -H "X-Mock-Tenant-Id: 550e8400-e29b-41d4-a716-446655440000"
```

#### Test 2: Update Current User Profile

```bash
curl -X PUT "http://localhost:8000/api/users/me" \
     -H "Content-Type: application/json" \
     -H "X-Mock-User-Id: 123e4567-e89b-12d3-a456-426614174000" \
     -H "X-Mock-Tenant-Id: 550e8400-e29b-41d4-a716-446655440000" \
     -d '{
       "display_name": "Updated Name",
       "role": "admin"
     }'
```

#### Test 3: Search Users

```bash
curl -X GET "http://localhost:8000/api/users/?search_term=test&limit=10&offset=0" \
     -H "X-Mock-User-Id: 123e4567-e89b-12d3-a456-426614174000" \
     -H "X-Mock-Tenant-Id: 550e8400-e29b-41d4-a716-446655440000"
```

#### Test 4: Change Password

```bash
curl -X POST "http://localhost:8000/api/users/me/password" \
     -H "Content-Type: application/json" \
     -H "X-Mock-User-Id: 123e4567-e89b-12d3-a456-426614174000" \
     -H "X-Mock-Tenant-Id: 550e8400-e29b-41d4-a716-446655440000" \
     -d '{
       "current_password": "oldpassword123",
       "new_password": "newpassword123"
     }'
```

---

## Next Steps

Continue to the next module:
- **Module 7.4**: API Router Setup and Integration → `074_API_Router_Setup.md`

## Key Concepts Covered

1. **CRUD Operations**: Complete user profile management
2. **Search and Filtering**: User discovery with query parameters
3. **Security**: Tenant isolation and basic access controls
4. **Password Management**: Secure password change functionality
5. **Pagination**: Handling large result sets efficiently
6. **Validation**: Comprehensive input validation
7. **Error Handling**: Proper error responses for all scenarios
8. **Service Integration**: Clean separation between API and business logic

The user profile endpoints provide comprehensive user management functionality while maintaining security and following API best practices.
