# app/api/routers/organization.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Path
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.services.organization_service import (
    OrganizationService,
    get_organization_service,
)
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationRead,
    OrganizationListResponse,
)
from app.schemas.organization_membership import (
    InvitationRequest,
)
from app.api.response_helpers import create_success_response, create_error_response
from app.api.deps import (
    get_current_user_mock,
    get_current_user_from_db,
    MockCurrentUser,
)
from app.db.models.user import User
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("/", response_model=dict)
async def create_organization(
    request: Request,
    organization_data: OrganizationCreate,
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    Create a new organization within the current tenant.
    """
    # Get request ID from middleware
    request_id = getattr(request.state, "request_id", "unknown")

    # Log request entry with context
    logger.info(
        "Organization creation request received",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "user_id": str(current_user.user_id),
                "tenant_id": str(current_user.tenant_id),
                "organization_name": organization_data.name,
                "domain": organization_data.domain,
                "endpoint": "/organizations/",
                "method": "POST",
            }
        },
    )

    try:
        organization_service = OrganizationService(db)

        # Create organization with creator as owner
        new_organization = organization_service.create_organization_with_owner(
            tenant_id=current_user.tenant_id, 
            organization_data=organization_data,
            owner_user_id=current_user.user_id
        )

        # Log successful completion
        logger.info(
            "Organization created successfully",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "organization_id": str(new_organization.id),
                    "organization_name": new_organization.name,
                    "endpoint": "/organizations/",
                    "status": "success",
                }
            },
        )

        return create_success_response(
            data={
                **new_organization.model_dump(),
                "message": "Organization created successfully",
            },
            tenant_id=current_user.tenant_id,
        )

    except ValueError as e:
        # Business logic errors (validation, duplicates, etc.)
        logger.warning(
            f"Organization creation failed - validation error: {str(e)}",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "organization_name": organization_data.name,
                    "error_type": "validation_error",
                    "endpoint": "/organizations/",
                }
            },
        )
        return create_error_response(
            code="VALIDATION_ERROR", message=str(e), tenant_id=current_user.tenant_id
        )
    except Exception as e:
        # Log error with context
        logger.error(
            f"Organization creation failed: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "organization_name": organization_data.name,
                    "error_type": "creation_error",
                    "status": "failed",
                }
            },
        )

        return create_error_response(
            code="CREATION_ERROR",
            message="Unable to create organization",
            tenant_id=current_user.tenant_id,
        )


@router.get("/", response_model=dict)
async def list_organizations(
    search_term: Optional[str] = Query(
        None, description="Search in organization name or domain"
    ),
    limit: Optional[int] = Query(
        50, ge=1, le=100, description="Number of results to return"
    ),
    skip: Optional[int] = Query(0, ge=0, description="Number of results to skip"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    List organizations within the current tenant with optional search.
    """
    try:
        organization_service = OrganizationService(db)

        if search_term:
            # Search organizations
            result = organization_service.search_organizations(
                tenant_id=current_user.tenant_id,
                search_term=search_term,
                skip=skip,
                limit=limit,
            )
        else:
            # List all organizations
            result = organization_service.list_organizations(
                tenant_id=current_user.tenant_id, skip=skip, limit=limit
            )

        return create_success_response(
            data=result.model_dump(), tenant_id=current_user.tenant_id
        )

    except Exception as e:
        logger.error(
            f"Organization listing failed: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "search_term": search_term,
                    "endpoint": "/organizations/",
                    "status": "failed",
                }
            },
        )

        return create_error_response(
            code="LISTING_ERROR",
            message="Unable to retrieve organizations",
            tenant_id=current_user.tenant_id,
        )


@router.get("/{organization_id}", response_model=dict)
async def get_organization(
    organization_id: str = Path(..., description="Organization UUID"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    Get organization details by ID.
    """
    try:
        # Convert string to UUID
        try:
            org_id_uuid = UUID(organization_id)
        except ValueError:
            return create_error_response(
                code="INVALID_ID",
                message="Invalid organization ID format",
                tenant_id=current_user.tenant_id,
            )

        organization_service = OrganizationService(db)

        # Get organization
        organization = organization_service.get_organization(
            tenant_id=current_user.tenant_id, organization_id=org_id_uuid
        )

        if not organization:
            return create_error_response(
                code="ORGANIZATION_NOT_FOUND",
                message="Organization not found in your tenant",
                tenant_id=current_user.tenant_id,
            )

        return create_success_response(
            data=organization.model_dump(), tenant_id=current_user.tenant_id
        )

    except Exception as e:
        logger.error(
            f"Organization retrieval failed: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "organization_id": organization_id,
                    "endpoint": f"/organizations/{organization_id}",
                    "status": "failed",
                }
            },
        )

        return create_error_response(
            code="RETRIEVAL_ERROR",
            message="Unable to retrieve organization",
            tenant_id=current_user.tenant_id,
        )


@router.put("/{organization_id}", response_model=dict)
async def update_organization(
    organization_id: str = Path(..., description="Organization UUID"),
    update_data: OrganizationUpdate = ...,
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    Update organization details.
    """
    try:
        # Convert string to UUID
        try:
            org_id_uuid = UUID(organization_id)
        except ValueError:
            return create_error_response(
                code="INVALID_ID",
                message="Invalid organization ID format",
                tenant_id=current_user.tenant_id,
            )

        organization_service = OrganizationService(db)

        # Update organization
        updated_organization = organization_service.update_organization(
            tenant_id=current_user.tenant_id,
            organization_id=org_id_uuid,
            update_data=update_data,
        )

        if not updated_organization:
            return create_error_response(
                code="ORGANIZATION_NOT_FOUND",
                message="Organization not found in your tenant",
                tenant_id=current_user.tenant_id,
            )

        logger.info(
            "Organization updated successfully",
            extra={
                "extra_fields": {
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "organization_id": organization_id,
                    "endpoint": f"/organizations/{organization_id}",
                    "status": "success",
                }
            },
        )

        return create_success_response(
            data={
                **updated_organization.model_dump(),
                "message": "Organization updated successfully",
            },
            tenant_id=current_user.tenant_id,
        )

    except ValueError as e:
        return create_error_response(
            code="VALIDATION_ERROR", message=str(e), tenant_id=current_user.tenant_id
        )
    except Exception as e:
        logger.error(
            f"Organization update failed: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "organization_id": organization_id,
                    "endpoint": f"/organizations/{organization_id}",
                    "status": "failed",
                }
            },
        )

        return create_error_response(
            code="UPDATE_ERROR",
            message="Unable to update organization",
            tenant_id=current_user.tenant_id,
        )


@router.delete("/{organization_id}", response_model=dict)
async def delete_organization(
    organization_id: str = Path(..., description="Organization UUID"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    Delete (soft delete) an organization.
    """
    try:
        # Convert string to UUID
        try:
            org_id_uuid = UUID(organization_id)
        except ValueError:
            return create_error_response(
                code="INVALID_ID",
                message="Invalid organization ID format",
                tenant_id=current_user.tenant_id,
            )

        organization_service = OrganizationService(db)

        # Delete organization
        success = organization_service.delete_organization(
            tenant_id=current_user.tenant_id, organization_id=org_id_uuid
        )

        if not success:
            return create_error_response(
                code="ORGANIZATION_NOT_FOUND",
                message="Organization not found in your tenant",
                tenant_id=current_user.tenant_id,
            )

        logger.info(
            "Organization deleted successfully",
            extra={
                "extra_fields": {
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "organization_id": organization_id,
                    "endpoint": f"/organizations/{organization_id}",
                    "status": "success",
                }
            },
        )

        return create_success_response(
            data={
                "organization_id": organization_id,
                "message": "Organization deleted successfully",
            },
            tenant_id=current_user.tenant_id,
        )

    except Exception as e:
        logger.error(
            f"Organization deletion failed: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "organization_id": organization_id,
                    "endpoint": f"/organizations/{organization_id}",
                    "status": "failed",
                }
            },
        )

        return create_error_response(
            code="DELETION_ERROR",
            message="Unable to delete organization",
            tenant_id=current_user.tenant_id,
        )


# === Business Logic Endpoints ===


@router.get("/by-name/{organization_name}", response_model=dict)
async def get_organization_by_name(
    organization_name: str = Path(..., description="Organization name"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    Get organization by name within the current tenant.
    """
    try:
        organization_service = OrganizationService(db)

        organization = organization_service.get_organization_by_name(
            tenant_id=current_user.tenant_id, name=organization_name
        )

        if not organization:
            return create_error_response(
                code="ORGANIZATION_NOT_FOUND",
                message=f"Organization '{organization_name}' not found in your tenant",
                tenant_id=current_user.tenant_id,
            )

        return create_success_response(
            data=organization.model_dump(), tenant_id=current_user.tenant_id
        )

    except Exception as e:
        return create_error_response(
            code="RETRIEVAL_ERROR",
            message="Unable to retrieve organization by name",
            tenant_id=current_user.tenant_id,
        )


@router.get("/by-domain/{domain}", response_model=dict)
async def get_organizations_by_domain(
    domain: str = Path(..., description="Email domain"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    Get organizations by domain within the current tenant.
    """
    try:
        organization_service = OrganizationService(db)

        organizations = organization_service.get_organizations_by_domain(
            tenant_id=current_user.tenant_id, domain=domain
        )

        return create_success_response(
            data={
                "domain": domain,
                "organizations": [org.model_dump() for org in organizations],
                "count": len(organizations),
            },
            tenant_id=current_user.tenant_id,
        )

    except Exception as e:
        return create_error_response(
            code="RETRIEVAL_ERROR",
            message="Unable to retrieve organizations by domain",
            tenant_id=current_user.tenant_id,
        )


@router.get("/{organization_id}/check-membership/{user_id}", response_model=dict)
async def check_user_organization_membership(
    organization_id: str = Path(..., description="Organization UUID"),
    user_id: str = Path(..., description="User UUID"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    Check if a user belongs to a specific organization.
    """
    try:
        # Convert strings to UUIDs
        try:
            org_id_uuid = UUID(organization_id)
            user_id_uuid = UUID(user_id)
        except ValueError:
            return create_error_response(
                code="INVALID_ID",
                message="Invalid UUID format",
                tenant_id=current_user.tenant_id,
            )

        organization_service = OrganizationService(db)

        belongs = organization_service.user_belongs_to_organization(
            tenant_id=current_user.tenant_id,
            user_id=user_id_uuid,
            organization_id=org_id_uuid,
        )

        return create_success_response(
            data={
                "user_id": user_id,
                "organization_id": organization_id,
                "belongs_to_organization": belongs,
            },
            tenant_id=current_user.tenant_id,
        )

    except Exception as e:
        return create_error_response(
            code="MEMBERSHIP_CHECK_ERROR",
            message="Unable to check organization membership",
            tenant_id=current_user.tenant_id,
        )


@router.get("/user/{user_id}/organizations", response_model=dict)
async def get_user_organizations(
    user_id: str = Path(..., description="User UUID"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    Get all organizations that a user belongs to.
    """
    try:
        # Convert string to UUID
        try:
            user_id_uuid = UUID(user_id)
        except ValueError:
            return create_error_response(
                code="INVALID_ID",
                message="Invalid user ID format",
                tenant_id=current_user.tenant_id,
            )

        organization_service = OrganizationService(db)

        organizations = organization_service.get_user_organizations(
            tenant_id=current_user.tenant_id, user_id=user_id_uuid
        )

        return create_success_response(
            data={
                "user_id": user_id,
                "organizations": [org.model_dump() for org in organizations],
                "count": len(organizations),
            },
            tenant_id=current_user.tenant_id,
        )

    except Exception as e:
        return create_error_response(
            code="RETRIEVAL_ERROR",
            message="Unable to retrieve user organizations",
            tenant_id=current_user.tenant_id,
        )


# === Analytics Endpoints ===


@router.get("/analytics/statistics", response_model=dict)
async def get_organization_statistics(
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    Get comprehensive organization statistics for the current tenant.
    """
    try:
        organization_service = OrganizationService(db)

        stats = organization_service.get_organization_statistics(
            tenant_id=current_user.tenant_id
        )

        return create_success_response(data=stats, tenant_id=current_user.tenant_id)

    except Exception as e:
        return create_error_response(
            code="ANALYTICS_ERROR",
            message="Unable to retrieve organization statistics",
            tenant_id=current_user.tenant_id,
        )


@router.get("/with-billing", response_model=dict)
async def get_organizations_with_billing(
    limit: Optional[int] = Query(
        50, ge=1, le=100, description="Number of results to return"
    ),
    skip: Optional[int] = Query(0, ge=0, description="Number of results to skip"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    Get organizations that have billing information configured.
    """
    try:
        organization_service = OrganizationService(db)

        result = organization_service.get_organizations_with_billing(
            tenant_id=current_user.tenant_id, skip=skip, limit=limit
        )

        return create_success_response(
            data=result.model_dump(), tenant_id=current_user.tenant_id
        )

    except Exception as e:
        return create_error_response(
            code="RETRIEVAL_ERROR",
            message="Unable to retrieve organizations with billing",
            tenant_id=current_user.tenant_id,
        )


# === Organization Membership Endpoints ===


@router.post("/{organization_id}/members/invite", response_model=dict)
async def invite_user_to_organization(
    organization_id: str = Path(..., description="Organization UUID"),
    invitation: InvitationRequest = ...,
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    Invite a user to join an organization.
    """
    try:
        # Convert string to UUID
        try:
            org_id_uuid = UUID(organization_id)
        except ValueError:
            return create_error_response(
                code="INVALID_ID",
                message="Invalid organization ID format",
                tenant_id=current_user.tenant_id,
            )

        organization_service = OrganizationService(db)

        # Invite user to organization
        membership = organization_service.invite_user_to_organization(
            tenant_id=current_user.tenant_id,
            organization_id=org_id_uuid,
            user_email=invitation.user_email,
            role=invitation.role,
            inviter_user_id=current_user.user_id,
            message=invitation.message
        )

        logger.info(
            "User invited to organization successfully",
            extra={
                "extra_fields": {
                    "inviter_user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "organization_id": organization_id,
                    "membership_id": str(membership.id),
                    "invitee_email": invitation.user_email,
                    "status": "success",
                }
            },
        )

        return create_success_response(
            data={
                **membership.model_dump(),
                "message": f"Invitation sent to {invitation.user_email}",
            },
            tenant_id=current_user.tenant_id,
        )

    except ValueError as e:
        return create_error_response(
            code="INVITATION_ERROR", message=str(e), tenant_id=current_user.tenant_id
        )
    except Exception as e:
        logger.error(
            f"Organization invitation failed: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "inviter_user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "organization_id": organization_id,
                    "status": "failed",
                }
            },
        )

        return create_error_response(
            code="INVITATION_ERROR",
            message="Unable to send invitation",
            tenant_id=current_user.tenant_id,
        )


@router.get("/{organization_id}/members", response_model=dict)
async def list_organization_members(
    organization_id: str = Path(..., description="Organization UUID"),
    status_filter: Optional[str] = Query("active", description="Filter by status"),
    role_filter: Optional[str] = Query(None, description="Filter by role"),
    limit: Optional[int] = Query(50, ge=1, le=100, description="Number of results"),
    skip: Optional[int] = Query(0, ge=0, description="Number of results to skip"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    List members of an organization.
    """
    try:
        # Convert string to UUID
        try:
            org_id_uuid = UUID(organization_id)
        except ValueError:
            return create_error_response(
                code="INVALID_ID",
                message="Invalid organization ID format",
                tenant_id=current_user.tenant_id,
            )

        organization_service = OrganizationService(db)

        # Check if user has permission to view members
        if not organization_service.user_has_organization_permission(
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id,
            organization_id=org_id_uuid,
            required_roles=["owner", "admin", "member"]  # members can see other members
        ):
            return create_error_response(
                code="PERMISSION_DENIED",
                message="You don't have permission to view organization members",
                tenant_id=current_user.tenant_id,
            )

        # List organization members
        result = organization_service.list_organization_members(
            tenant_id=current_user.tenant_id,
            organization_id=org_id_uuid,
            skip=skip,
            limit=limit,
            status_filter=status_filter,
            role_filter=role_filter
        )

        return create_success_response(
            data=result.model_dump(), tenant_id=current_user.tenant_id
        )

    except Exception as e:
        logger.error(
            f"Organization members listing failed: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "organization_id": organization_id,
                    "status": "failed",
                }
            },
        )

        return create_error_response(
            code="LISTING_ERROR",
            message="Unable to retrieve organization members",
            tenant_id=current_user.tenant_id,
        )


@router.put("/{organization_id}/members/{user_id}", response_model=dict)
async def update_member_role(
    organization_id: str = Path(..., description="Organization UUID"),
    user_id: str = Path(..., description="User UUID"),
    new_role: str = Query(..., description="New role to assign"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    Update a member's role in an organization.
    """
    try:
        # Convert strings to UUIDs
        try:
            org_id_uuid = UUID(organization_id)
            user_id_uuid = UUID(user_id)
        except ValueError:
            return create_error_response(
                code="INVALID_ID",
                message="Invalid UUID format",
                tenant_id=current_user.tenant_id,
            )

        organization_service = OrganizationService(db)

        # Update user role
        updated_membership = organization_service.update_user_role_in_organization(
            tenant_id=current_user.tenant_id,
            organization_id=org_id_uuid,
            user_id=user_id_uuid,
            new_role=new_role,
            updater_user_id=current_user.user_id
        )

        if not updated_membership:
            return create_error_response(
                code="MEMBER_NOT_FOUND",
                message="Member not found in organization",
                tenant_id=current_user.tenant_id,
            )

        logger.info(
            "Member role updated successfully",
            extra={
                "extra_fields": {
                    "updater_user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "organization_id": organization_id,
                    "target_user_id": user_id,
                    "new_role": new_role,
                    "status": "success",
                }
            },
        )

        return create_success_response(
            data={
                **updated_membership.model_dump(),
                "message": f"Member role updated to {new_role}",
            },
            tenant_id=current_user.tenant_id,
        )

    except ValueError as e:
        return create_error_response(
            code="ROLE_UPDATE_ERROR", message=str(e), tenant_id=current_user.tenant_id
        )
    except Exception as e:
        logger.error(
            f"Member role update failed: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "updater_user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "organization_id": organization_id,
                    "target_user_id": user_id,
                    "status": "failed",
                }
            },
        )

        return create_error_response(
            code="ROLE_UPDATE_ERROR",
            message="Unable to update member role",
            tenant_id=current_user.tenant_id,
        )


@router.delete("/{organization_id}/members/{user_id}", response_model=dict)
async def remove_member_from_organization(
    organization_id: str = Path(..., description="Organization UUID"),
    user_id: str = Path(..., description="User UUID"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    Remove a member from an organization.
    """
    try:
        # Convert strings to UUIDs
        try:
            org_id_uuid = UUID(organization_id)
            user_id_uuid = UUID(user_id)
        except ValueError:
            return create_error_response(
                code="INVALID_ID",
                message="Invalid UUID format",
                tenant_id=current_user.tenant_id,
            )

        organization_service = OrganizationService(db)

        # Remove user from organization
        success = organization_service.remove_user_from_organization(
            tenant_id=current_user.tenant_id,
            organization_id=org_id_uuid,
            user_id=user_id_uuid,
            remover_user_id=current_user.user_id
        )

        if not success:
            return create_error_response(
                code="MEMBER_NOT_FOUND",
                message="Member not found in organization",
                tenant_id=current_user.tenant_id,
            )

        logger.info(
            "Member removed from organization successfully",
            extra={
                "extra_fields": {
                    "remover_user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "organization_id": organization_id,
                    "removed_user_id": user_id,
                    "status": "success",
                }
            },
        )

        return create_success_response(
            data={
                "organization_id": organization_id,
                "removed_user_id": user_id,
                "message": "Member removed from organization successfully",
            },
            tenant_id=current_user.tenant_id,
        )

    except ValueError as e:
        return create_error_response(
            code="REMOVAL_ERROR", message=str(e), tenant_id=current_user.tenant_id
        )
    except Exception as e:
        logger.error(
            f"Member removal failed: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "remover_user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "organization_id": organization_id,
                    "target_user_id": user_id,
                    "status": "failed",
                }
            },
        )

        return create_error_response(
            code="REMOVAL_ERROR",
            message="Unable to remove member from organization",
            tenant_id=current_user.tenant_id,
        )


@router.get("/user/{user_id}/organizations", response_model=dict)
async def get_user_organizations(
    user_id: str = Path(..., description="User UUID"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    Get all organizations that a user belongs to.
    """
    try:
        # Convert string to UUID
        try:
            user_id_uuid = UUID(user_id)
        except ValueError:
            return create_error_response(
                code="INVALID_ID",
                message="Invalid user ID format",
                tenant_id=current_user.tenant_id,
            )

        organization_service = OrganizationService(db)

        # Get user's organizations
        result = organization_service.list_user_organizations(
            tenant_id=current_user.tenant_id, 
            user_id=user_id_uuid
        )

        return create_success_response(
            data=result.model_dump(), tenant_id=current_user.tenant_id
        )

    except Exception as e:
        logger.error(
            f"User organizations retrieval failed: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "requester_user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "target_user_id": user_id,
                    "status": "failed",
                }
            },
        )

        return create_error_response(
            code="RETRIEVAL_ERROR",
            message="Unable to retrieve user organizations",
            tenant_id=current_user.tenant_id,
        )
