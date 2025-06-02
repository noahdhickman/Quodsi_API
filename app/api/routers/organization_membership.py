# app/api/routers/organization_membership.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Path
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.services.organization_service import (
    OrganizationService,
    get_organization_service,
)
from app.schemas.organization_membership import (
    OrganizationMembershipCreate,
    OrganizationMembershipUpdate,
    OrganizationMembershipRead,
    OrganizationMembershipListResponse,
    OrganizationMembersResponse,
    UserOrganizationsResponse,
    InvitationRequest,
    AcceptInvitationRequest,
)
from app.api.response_helpers import create_success_response, create_error_response
from app.api.deps import (
    get_current_user_mock,
    MockCurrentUser,
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/memberships")


@router.post("/invite", response_model=dict)
async def invite_user_to_organization(
    request: Request,
    invitation: InvitationRequest,
    organization_id: UUID = Query(..., description="Organization UUID"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    Invite a user to join an organization.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.info(
        "Organization invitation request received",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "inviter_user_id": str(current_user.user_id),
                "tenant_id": str(current_user.tenant_id),
                "organization_id": str(organization_id),
                "invitee_email": invitation.user_email,
                "role": invitation.role,
                "endpoint": "/memberships/invite",
                "method": "POST",
            }
        },
    )

    try:
        organization_service = OrganizationService(db)

        # Invite user to organization
        membership = organization_service.invite_user_to_organization(
            tenant_id=current_user.tenant_id,
            organization_id=organization_id,
            user_email=invitation.user_email,
            role=invitation.role,
            inviter_user_id=current_user.user_id,
            message=invitation.message
        )

        logger.info(
            "User invited to organization successfully",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "inviter_user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "organization_id": str(organization_id),
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
        logger.warning(
            f"Organization invitation failed - validation error: {str(e)}",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "inviter_user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "organization_id": str(organization_id),
                    "invitee_email": invitation.user_email,
                    "error_type": "validation_error",
                }
            },
        )
        return create_error_response(
            code="INVITATION_ERROR", message=str(e), tenant_id=current_user.tenant_id
        )
    except Exception as e:
        logger.error(
            f"Organization invitation failed: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "inviter_user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "organization_id": str(organization_id),
                    "error_type": "invitation_error",
                    "status": "failed",
                }
            },
        )

        return create_error_response(
            code="INVITATION_ERROR",
            message="Unable to send invitation",
            tenant_id=current_user.tenant_id,
        )


@router.post("/{membership_id}/accept", response_model=dict)
async def accept_organization_invitation(
    membership_id: str = Path(..., description="Membership UUID"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    Accept an organization invitation.
    """
    try:
        # Convert string to UUID
        try:
            membership_uuid = UUID(membership_id)
        except ValueError:
            return create_error_response(
                code="INVALID_ID",
                message="Invalid membership ID format",
                tenant_id=current_user.tenant_id,
            )

        organization_service = OrganizationService(db)

        # Accept invitation
        membership = organization_service.accept_invitation(
            tenant_id=current_user.tenant_id,
            membership_id=membership_uuid,
            user_id=current_user.user_id
        )

        logger.info(
            "Organization invitation accepted",
            extra={
                "extra_fields": {
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "membership_id": membership_id,
                    "organization_id": str(membership.organization_id),
                    "status": "success",
                }
            },
        )

        return create_success_response(
            data={
                **membership.model_dump(),
                "message": "Invitation accepted successfully",
            },
            tenant_id=current_user.tenant_id,
        )

    except ValueError as e:
        return create_error_response(
            code="ACCEPTANCE_ERROR", message=str(e), tenant_id=current_user.tenant_id
        )
    except Exception as e:
        logger.error(
            f"Invitation acceptance failed: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "membership_id": membership_id,
                    "status": "failed",
                }
            },
        )

        return create_error_response(
            code="ACCEPTANCE_ERROR",
            message="Unable to accept invitation",
            tenant_id=current_user.tenant_id,
        )


@router.get("/{membership_id}", response_model=dict)
async def get_membership(
    membership_id: str = Path(..., description="Membership UUID"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    Get membership details by ID.
    """
    try:
        # Convert string to UUID
        try:
            membership_uuid = UUID(membership_id)
        except ValueError:
            return create_error_response(
                code="INVALID_ID",
                message="Invalid membership ID format",
                tenant_id=current_user.tenant_id,
            )

        organization_service = OrganizationService(db)

        # Get membership (this would need to be added to the service)
        # For now, we'll return a placeholder
        return create_error_response(
            code="NOT_IMPLEMENTED",
            message="Get membership endpoint not yet implemented",
            tenant_id=current_user.tenant_id,
        )

    except Exception as e:
        return create_error_response(
            code="RETRIEVAL_ERROR",
            message="Unable to retrieve membership",
            tenant_id=current_user.tenant_id,
        )


@router.put("/{membership_id}", response_model=dict)
async def update_membership(
    membership_id: str = Path(..., description="Membership UUID"),
    update_data: OrganizationMembershipUpdate = ...,
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    Update membership role or status.
    """
    try:
        # Convert string to UUID
        try:
            membership_uuid = UUID(membership_id)
        except ValueError:
            return create_error_response(
                code="INVALID_ID",
                message="Invalid membership ID format",
                tenant_id=current_user.tenant_id,
            )

        organization_service = OrganizationService(db)

        # This would require adding a method to get membership details first
        # Then update based on the organization and user
        return create_error_response(
            code="NOT_IMPLEMENTED",
            message="Update membership endpoint not yet implemented",
            tenant_id=current_user.tenant_id,
        )

    except Exception as e:
        return create_error_response(
            code="UPDATE_ERROR",
            message="Unable to update membership",
            tenant_id=current_user.tenant_id,
        )


@router.delete("/{membership_id}", response_model=dict)
async def remove_membership(
    membership_id: str = Path(..., description="Membership UUID"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    Remove membership (leave organization).
    """
    try:
        # Convert string to UUID
        try:
            membership_uuid = UUID(membership_id)
        except ValueError:
            return create_error_response(
                code="INVALID_ID",
                message="Invalid membership ID format",
                tenant_id=current_user.tenant_id,
            )

        organization_service = OrganizationService(db)

        # This would require getting the membership first to extract org and user IDs
        return create_error_response(
            code="NOT_IMPLEMENTED",
            message="Remove membership endpoint not yet implemented",
            tenant_id=current_user.tenant_id,
        )

    except Exception as e:
        return create_error_response(
            code="REMOVAL_ERROR",
            message="Unable to remove membership",
            tenant_id=current_user.tenant_id,
        )


@router.get("/invitations/pending", response_model=dict)
async def get_pending_invitations(
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    limit: Optional[int] = Query(50, ge=1, le=100, description="Number of results"),
    skip: Optional[int] = Query(0, ge=0, description="Number of results to skip"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db),
):
    """
    Get pending invitations for the current user or organization.
    """
    try:
        organization_service = OrganizationService(db)

        # Convert organization_id if provided
        org_uuid = None
        if organization_id:
            try:
                org_uuid = UUID(organization_id)
            except ValueError:
                return create_error_response(
                    code="INVALID_ID",
                    message="Invalid organization ID format",
                    tenant_id=current_user.tenant_id,
                )

        # Get pending invitations
        result = organization_service.get_pending_invitations(
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id,
            organization_id=org_uuid,
            skip=skip,
            limit=limit
        )

        return create_success_response(
            data=result.model_dump(), tenant_id=current_user.tenant_id
        )

    except Exception as e:
        logger.error(
            f"Pending invitations retrieval failed: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "organization_id": organization_id,
                    "endpoint": "/memberships/invitations/pending",
                    "status": "failed",
                }
            },
        )

        return create_error_response(
            code="RETRIEVAL_ERROR",
            message="Unable to retrieve pending invitations",
            tenant_id=current_user.tenant_id,
        )