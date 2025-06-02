# app/api/routers/user_profile.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
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
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/users")

@router.get("/me", response_model=dict)
async def get_my_profile(
    request: Request,
    current_user: User = Depends(get_current_user_from_db)
):
    """
    Get the current user's profile information.
    """
    # Get request ID from middleware
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Log request entry with context
    logger.info(
        "User profile request received",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "user_id": str(current_user.id),
                "tenant_id": str(current_user.tenant_id),
                "endpoint": "/users/me",
                "method": "GET"
            }
        }
    )
    
    try:
        profile_data = UserProfileResponse.from_orm(current_user)
        
        # Log successful completion
        logger.info(
            "User profile retrieved successfully",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.id),
                    "tenant_id": str(current_user.tenant_id),
                    "endpoint": "/users/me",
                    "status": "success"
                }
            }
        )
        
        return create_success_response(
            data=profile_data.dict(),
            tenant_id=current_user.tenant_id
        )
        
    except Exception as e:
        # Log error with context
        logger.error(
            f"Profile retrieval failed: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.id),
                    "tenant_id": str(current_user.tenant_id),
                    "endpoint": "/users/me",
                    "error_type": "profile_error",
                    "status": "failed"
                }
            }
        )
        
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
        print(f"Starting get_user_profile with user_id: {user_id}")
        print(f"Current user mock: {current_user}")
        print(f"Current user tenant_id: {current_user.tenant_id}")
        
        # Try to find the user directly from the database
        # This bypasses potential service layer issues
        from app.db.models.user import User
        from uuid import UUID
        
        # Convert string to UUID
        try:
            user_id_uuid = UUID(user_id)
            print(f"Converted user_id to UUID: {user_id_uuid}")
        except ValueError:
            print(f"Invalid UUID format: {user_id}")
            return create_error_response(
                code="INVALID_ID",
                message="Invalid user ID format",
                tenant_id=current_user.tenant_id
            )
        
        # Query the database directly to handle SQL Server UUID specifics
        print(f"Querying database directly")
        
        # Convert UUIDs to strings for comparison if needed
        user_id_str = str(user_id_uuid)
        tenant_id_str = str(current_user.tenant_id)
        
        # Query with direct comparison, respecting SQL Server's UNIQUEIDENTIFIER format
        user = db.query(User).filter(
            User.id == user_id_uuid,
            User.tenant_id == current_user.tenant_id
        ).first()
        
        print(f"Direct query result: {user}")
        
        if not user:
            print(f"User not found error")
            return create_error_response(
                code="USER_NOT_FOUND",
                message="User not found in your tenant",
                tenant_id=current_user.tenant_id
            )
        
        # Convert user to response model
        print(f"Creating UserProfileResponse")
        profile_data = UserProfileResponse.from_orm(user)
        print(f"Created profile_data: {profile_data}")
        
        # Return response
        print(f"Creating success response")
        return create_success_response(
            data=profile_data.dict(),
            tenant_id=current_user.tenant_id
        )
        
    except Exception as e:
        print(f"ERROR in get_user_profile: {type(e).__name__}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        return create_error_response(
            code="PROFILE_ERROR",
            message=f"Unable to retrieve user profile: {str(e)}",
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
        print(f"Starting list_users with tenant_id: {current_user.tenant_id}")
        print(f"Search parameters: term={search_term}, role={role}, is_active={is_active}")
        
        # Validate that we have a valid UUID for tenant_id
        try:
            from uuid import UUID
            tenant_id = current_user.tenant_id
            if isinstance(tenant_id, str):
                tenant_id = UUID(tenant_id)
            print(f"Validated tenant_id: {tenant_id}")
        except ValueError as ve:
            print(f"Invalid tenant_id format: {current_user.tenant_id}")
            return create_error_response(
                code="INVALID_TENANT_ID",
                message=f"Invalid tenant ID format: {str(ve)}",
                tenant_id=current_user.tenant_id
            )
            
        user_service = UserService(db)
        print(f"Initialized UserService")
        
        # Create search request
        search_request = UserSearchRequest(
            search_term=search_term,
            role=role,
            is_active=is_active,
            limit=limit,
            offset=offset
        )
        print(f"Created search request: {search_request}")
        
        # Try direct database query first (as a fallback)
        try:
            # Get users with search criteria
            users, total_count = user_service.search_users_in_tenant(
                tenant_id=tenant_id,
                search_term=search_request.search_term,
                role=search_request.role,
                is_active=search_request.is_active,
                limit=search_request.limit,
                offset=search_request.offset
            )
            print(f"Search found {total_count} total users, returning {len(users)} results")
            
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
        except Exception as search_error:
            print(f"Error in search_users_in_tenant: {type(search_error).__name__}: {str(search_error)}")
            import traceback
            print(traceback.format_exc())
            
            # Return detailed error
            return create_error_response(
                code="SEARCH_ERROR",
                message=f"Error searching users: {str(search_error)}",
                tenant_id=current_user.tenant_id
            )
        
    except Exception as e:
        print(f"Unhandled exception in list_users: {type(e).__name__}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        return create_error_response(
            code="SEARCH_ERROR",
            message=f"Unable to search users: {str(e)}",
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
        print(f"Starting update_user_profile endpoint with user_id: {user_id}")
        print(f"Request data: {request}")
        
        # Try a direct database update approach 
        from uuid import UUID
        from app.db.models.user import User
        
        # Convert string UUIDs to UUID objects
        try:
            user_id_uuid = UUID(user_id)
            tenant_id_uuid = current_user.tenant_id
            print(f"Converted IDs: user_id={user_id_uuid}, tenant_id={tenant_id_uuid}")
        except ValueError as e:
            print(f"Error converting UUIDs: {str(e)}")
            return create_error_response(
                code="INVALID_ID",
                message="Invalid UUID format",
                tenant_id=current_user.tenant_id
            )
        
        # Find the user directly in the database
        user = db.query(User).filter(
            User.id == user_id_uuid,
            User.tenant_id == tenant_id_uuid
        ).first()
        
        if not user:
            print(f"User not found")
            return create_error_response(
                code="USER_NOT_FOUND",
                message="User not found in your tenant",
                tenant_id=current_user.tenant_id
            )
        
        print(f"User found: {user}")
        
        # Update user fields directly
        if request.display_name:
            print(f"Updating display_name to: {request.display_name}")
            user.display_name = request.display_name
        
        # Handle status/role field
        if request.status:
            print(f"Updating status to: {request.status}")
            user.status = request.status
        elif request.role:
            print(f"Updating status (from role) to: {request.role}")
            user.status = request.role
        
        # Update is_active via status if needed
        if request.is_active is not None:
            print(f"Setting status based on is_active: {request.is_active}")
            if request.is_active and user.status != 'active':
                user.status = 'active'
            elif not request.is_active and user.status == 'active':
                user.status = 'inactive'
        
        # Update timestamp
        from datetime import datetime
        user.updated_at = datetime.utcnow()
        
        # Commit changes
        try:
            print(f"Committing changes to database")
            db.commit()
            print(f"Database commit successful")
        except Exception as commit_error:
            db.rollback()
            print(f"Error committing changes: {str(commit_error)}")
            raise commit_error
        
        # Return updated user profile
        try:
            print(f"Converting user to UserProfileResponse")
            profile_data = UserProfileResponse.from_orm(user)
            print(f"Conversion successful")
        except Exception as conversion_error:
            print(f"Error converting to UserProfileResponse: {str(conversion_error)}")
            raise conversion_error
        
        print(f"Creating success response")
        return create_success_response(
            data={
                **profile_data.dict(),
                "message": "User profile updated successfully"
            },
            tenant_id=current_user.tenant_id
        )
        
    except ValueError as e:
        print(f"Validation error: {str(e)}")
        return create_error_response(
            code="VALIDATION_ERROR",
            message=str(e),
            tenant_id=current_user.tenant_id
        )
    except Exception as e:
        print(f"Unhandled exception in update_user_profile: {type(e).__name__}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return create_error_response(
            code="UPDATE_ERROR",
            message=f"Unable to update user profile: {str(e)}",
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
