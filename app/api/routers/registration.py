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