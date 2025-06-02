# app/api/routers/registration.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional

from app.db.session import get_db
from app.services.registration_service import RegistrationService, get_registration_service
from app.repositories.tenant_repository import tenant_repo
from app.repositories.user_repository import user_repo
from app.schemas.registration import (
    TenantRegistrationRequest, 
    UserRegistrationRequest,
    RegistrationResponse,
    TenantRegistrationResponse
)
from app.schemas.user import UserRegistration, UserCreate
from app.schemas.tenant import TenantCreate
from app.api.response_helpers import (
    create_success_response, 
    create_error_response,
    create_validation_error_response
)
from app.api.deps import get_current_user_mock, MockCurrentUser
from pydantic import ValidationError
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/registration")

@router.post("/tenant", response_model=dict)
async def register_tenant(
    request: Request,
    registration_data: TenantRegistrationRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new tenant with admin user.
    
    This endpoint creates both a tenant and its first admin user.
    """
    # Get request ID from middleware
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Log request entry with context
    logger.info(
        "Tenant registration request received",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "email": registration_data.admin_email,
                "company_name": registration_data.name,
                "domain": registration_data.domain,
                "endpoint": "/registration/tenant",
                "method": "POST"
            }
        }
    )
    
    try:
        registration_service = RegistrationService(db)
        
        # Create tenant with admin using the service
        result = registration_service.register_tenant_with_admin(
            tenant_name=registration_data.name,
            domain=registration_data.domain,
            admin_email=registration_data.admin_email,
            admin_password=registration_data.admin_password,
            admin_display_name=registration_data.admin_display_name,
            request_id=request_id  # Pass request_id to service
        )
        
        # Log successful completion
        logger.info(
            "Tenant registration completed successfully",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(result["admin_user_id"]),
                    "tenant_id": str(result["tenant_id"]),
                    "email": result["admin_email"],
                    "tenant_name": result["tenant_name"],
                    "endpoint": "/registration/tenant",
                    "status": "success"
                }
            }
        )
        
        # Create response data
        response_data = TenantRegistrationResponse(
            tenant_id=result["tenant_id"],
            tenant_name=result["tenant_name"],
            domain=result["domain"],
            admin_user_id=result["admin_user_id"],
            admin_email=result["admin_email"],
            message="Tenant and admin user registered successfully"
        )
        
        return create_success_response(
            data=response_data.dict(),
            tenant_id=result["tenant_id"]
        )
        
    except ValueError as e:
        # Business logic errors (validation, duplicates, etc.)
        logger.warning(
            f"Registration failed - validation error: {str(e)}",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "email": registration_data.admin_email,
                    "company_name": registration_data.name,
                    "domain": registration_data.domain,
                    "error_type": "validation_error",
                    "endpoint": "/registration/tenant"
                }
            }
        )
        return create_error_response(
            code="REGISTRATION_ERROR",
            message=str(e)
        )
    except IntegrityError as e:
        # Database integrity errors
        logger.warning(
            f"Registration failed - integrity error: {str(e)}",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "email": registration_data.admin_email,
                    "domain": registration_data.domain,
                    "error_type": "duplicate_error",
                    "endpoint": "/registration/tenant"
                }
            }
        )
        db.rollback()
        return create_error_response(
            code="DUPLICATE_ERROR",
            message="Tenant domain or admin email already exists"
        )
    except Exception as e:
        # Unexpected system errors
        logger.error(
            f"Registration failed - unexpected error: {str(e)}",
            exc_info=True,  # Include stack trace
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "email": registration_data.admin_email,
                    "company_name": registration_data.name,
                    "error_type": "internal_error",
                    "endpoint": "/registration/tenant"
                }
            }
        )
        db.rollback()
        return create_error_response(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred during registration"
        )

@router.post("/tenant/sso", response_model=dict)
async def register_tenant_sso(
    request: UserRegistration,
    db: Session = Depends(get_db)
):
    """
    Register a new tenant with SSO user (alternative endpoint).
    
    This endpoint accepts the SSO-style registration format.
    """
    try:
        registration_service = RegistrationService(db)
        
        # Use the existing SSO registration method
        tenant, user = registration_service.register_user_and_tenant(request)
        
        # Create response data
        response_data = TenantRegistrationResponse(
            tenant_id=tenant.id,
            tenant_name=tenant.name,
            domain=tenant.slug,
            admin_user_id=user.id,
            admin_email=user.email,
            message="Tenant and admin user registered successfully"
        )
        
        return create_success_response(
            data=response_data.dict(),
            tenant_id=tenant.id
        )
        
    except ValueError as e:
        return create_error_response(
            code="REGISTRATION_ERROR",
            message=str(e)
        )
    except IntegrityError as e:
        db.rollback()
        return create_error_response(
            code="DUPLICATE_ERROR",
            message="Tenant or user already exists"
        )
    except Exception as e:
        db.rollback()
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
        # Check if email is already taken in this tenant
        existing_user = user_repo.get_by_email(db, current_user.tenant_id, request.email)
        if existing_user:
            return create_error_response(
                code="DUPLICATE_ERROR",
                message="Email already exists in this tenant",
                tenant_id=current_user.tenant_id
            )
        
        # Create user data
        user_data = {
            "email": request.email,
            "display_name": request.display_name,
            "identity_provider": "local",
            "identity_provider_id": request.email,
            "tenant_id": current_user.tenant_id,
            "status": "active"
        }
        
        # Create user
        user = user_repo.create(db, obj_in=user_data, tenant_id=current_user.tenant_id)
        
        # Commit the transaction
        db.commit()
        
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
        db.rollback()
        return create_error_response(
            code="DUPLICATE_ERROR",
            message="User email already exists in this tenant",
            tenant_id=current_user.tenant_id
        )
    except Exception as e:
        db.rollback()
        return create_error_response(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred during user registration",
            tenant_id=current_user.tenant_id
        )