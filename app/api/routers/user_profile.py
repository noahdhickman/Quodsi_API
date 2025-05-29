# app/api/routers/user_profile.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from app.db.session import get_db
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
from app.api.deps import get_current_user_mock, MockCurrentUser

router = APIRouter(prefix="/users", tags=["user-profile"])

@router.get("/me", response_model=dict)
async def get_my_profile(
    current_user: MockCurrentUser = Depends(get_current_user_mock)
):
    """
    Return a mock user profile for the current mock user.
    """
    try:
        profile_data = {
            "id": current_user.user_id,
            "tenant_id": current_user.tenant_id,
            "email": "mock@example.com",
            "display_name": "Mock User",
            "role": "user",
            "status": "active",
            "login_count": 1,
            "total_usage_minutes": 15,
            "last_login_at": datetime.now(timezone.utc),
            "last_active_at": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        return create_success_response(
            data=profile_data,
            tenant_id=current_user.tenant_id
        )

    except Exception as e:
        return create_error_response(
            code="PROFILE_ERROR",
            message=f"Unable to retrieve profile information: {str(e)}",
            tenant_id=current_user.tenant_id
        )

@router.put("/me", response_model=dict)
async def update_my_profile(
    request: UserProfileUpdateRequest,
    current_user: MockCurrentUser = Depends(get_current_user_mock)
):
    """
    Update the current mock user's profile (simulated).
    """
    try:
        updated_profile = {
            "id": current_user.user_id,
            "tenant_id": current_user.tenant_id,
            "email": "mock@example.com",
            "display_name": request.display_name or "Mock User",
            "role": request.role or "user",
            "status": "active",
            "login_count": 1,
            "total_usage_minutes": 15,
            "last_login_at": datetime.now(timezone.utc),
            "last_active_at": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        return create_success_response(
            data={**updated_profile, "message": "Profile updated successfully"},
            tenant_id=current_user.tenant_id
        )

    except Exception as e:
        return create_error_response(
            code="UPDATE_ERROR",
            message=f"Unable to update profile: {str(e)}",
            tenant_id=current_user.tenant_id
        )

@router.post("/me/password", response_model=dict)
async def change_password(
    request: PasswordUpdateRequest,
    current_user: MockCurrentUser = Depends(get_current_user_mock)
):
    """
    Simulate a successful password change for the mock user.
    """
    try:
        return create_success_response(
            data={"message": "Password changed successfully"},
            tenant_id=current_user.tenant_id
        )

    except Exception as e:
        return create_error_response(
            code="PASSWORD_ERROR",
            message=f"Unable to change password: {str(e)}",
            tenant_id=current_user.tenant_id
        )

@router.get("/", response_model=dict)
async def list_users(
    search_term: Optional[str] = Query(None, description="Search in email and display name"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: Optional[int] = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: Optional[int] = Query(0, ge=0, description="Number of results to skip"),
    current_user: MockCurrentUser = Depends(get_current_user_mock)
):
    """
    List mock users within the current tenant (simulated).
    """
    try:
        users = [
            {
                "id": UUID("123e4567-e89b-12d3-a456-426614174000"),
                "tenant_id": current_user.tenant_id,
                "email": "mock@example.com",
                "display_name": "Mock User",
                "role": "admin",
                "status": "active",
                "login_count": 1,
                "total_usage_minutes": 15,
                "last_login_at": datetime.now(timezone.utc),
                "last_active_at": datetime.now(timezone.utc),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
        ]

        response_data = {
            "users": users,
            "total_count": len(users),
            "limit": limit,
            "offset": offset
        }

        return create_success_response(
            data=response_data,
            tenant_id=current_user.tenant_id
        )

    except Exception as e:
        return create_error_response(
            code="SEARCH_ERROR",
            message=f"Unable to list users: {str(e)}",
            tenant_id=current_user.tenant_id
        )
