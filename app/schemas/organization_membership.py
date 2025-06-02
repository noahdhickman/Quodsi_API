from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, validator
from app.schemas.user import UserSummary
from app.schemas.organization import OrganizationSummary


class OrganizationMembershipBase(BaseModel):
    """Base organization membership schema with common fields"""
    
    role: str = Field(
        ..., 
        description="User role in organization: owner, admin, member, viewer"
    )
    status: str = Field(
        default="active",
        description="Membership status: active, invited, suspended, left"
    )
    
    @validator('role')
    def validate_role(cls, v):
        valid_roles = ['owner', 'admin', 'member', 'viewer']
        if v not in valid_roles:
            raise ValueError(f'Role must be one of: {", ".join(valid_roles)}')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['active', 'invited', 'suspended', 'left']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v


class OrganizationMembershipCreate(OrganizationMembershipBase):
    """Schema for creating a new organization membership (invitation)"""
    
    organization_id: UUID = Field(..., description="Organization UUID")
    user_id: UUID = Field(..., description="User UUID to add to organization")
    invited_by_user_id: Optional[UUID] = Field(None, description="User who sent the invitation")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "organization_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "456e7890-e89b-12d3-a456-426614174000",
                "role": "member",
                "status": "invited",
                "invited_by_user_id": "789e0123-e89b-12d3-a456-426614174000"
            }
        }
    )


class OrganizationMembershipUpdate(BaseModel):
    """Schema for updating an existing organization membership"""
    
    role: Optional[str] = Field(None, description="New role for the user")
    status: Optional[str] = Field(None, description="New status for the membership")
    
    @validator('role')
    def validate_role(cls, v):
        if v is not None:
            valid_roles = ['owner', 'admin', 'member', 'viewer']
            if v not in valid_roles:
                raise ValueError(f'Role must be one of: {", ".join(valid_roles)}')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ['active', 'invited', 'suspended', 'left']
            if v not in valid_statuses:
                raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "admin",
                "status": "active"
            }
        }
    )


class OrganizationMembershipRead(OrganizationMembershipBase):
    """Schema for reading organization membership data"""
    
    id: UUID = Field(..., description="Membership unique identifier")
    tenant_id: UUID = Field(..., description="Tenant this membership belongs to")
    organization_id: UUID = Field(..., description="Organization UUID")
    user_id: UUID = Field(..., description="User UUID")
    invited_by_user_id: Optional[UUID] = Field(None, description="User who invited this member")
    last_active_at: Optional[datetime] = Field(None, description="Last activity timestamp")
    created_at: datetime = Field(..., description="When the membership was created")
    updated_at: datetime = Field(..., description="When the membership was last updated")
    is_deleted: bool = Field(..., description="Whether the membership is soft deleted")
    
    # Nested objects (optional, populated when needed)
    user: Optional[UserSummary] = Field(None, description="User details")
    organization: Optional[OrganizationSummary] = Field(None, description="Organization details")
    invited_by: Optional[UserSummary] = Field(None, description="Inviter details")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "789e0123-e89b-12d3-a456-426614174000",
                "tenant_id": "456e7890-e89b-12d3-a456-426614174000",
                "organization_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "456e7890-e89b-12d3-a456-426614174000",
                "role": "member",
                "status": "active",
                "invited_by_user_id": "789e0123-e89b-12d3-a456-426614174000",
                "last_active_at": "2025-06-02T14:30:00.000Z",
                "created_at": "2025-06-02T12:00:00.000Z",
                "updated_at": "2025-06-02T14:30:00.000Z",
                "is_deleted": False
            }
        }
    )


class OrganizationMembershipSummary(BaseModel):
    """Lightweight schema for membership listings"""
    
    id: UUID = Field(..., description="Membership unique identifier")
    user_id: UUID = Field(..., description="User UUID")
    role: str = Field(..., description="User role in organization")
    status: str = Field(..., description="Membership status")
    created_at: datetime = Field(..., description="When the membership was created")
    last_active_at: Optional[datetime] = Field(None, description="Last activity timestamp")
    
    # User details for display
    user: Optional[UserSummary] = Field(None, description="User details")
    
    model_config = ConfigDict(from_attributes=True)


class OrganizationMembershipListResponse(BaseModel):
    """Schema for paginated organization membership listings"""
    
    memberships: List[OrganizationMembershipSummary] = Field(..., description="List of memberships")
    total: int = Field(..., description="Total number of memberships")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "memberships": [
                    {
                        "id": "789e0123-e89b-12d3-a456-426614174000",
                        "user_id": "456e7890-e89b-12d3-a456-426614174000",
                        "role": "member",
                        "status": "active",
                        "created_at": "2025-06-02T12:00:00.000Z",
                        "last_active_at": "2025-06-02T14:30:00.000Z"
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 50
            }
        }
    )


class UserOrganizationsResponse(BaseModel):
    """Schema for user's organization memberships"""
    
    user_id: UUID = Field(..., description="User UUID")
    organizations: List[OrganizationMembershipRead] = Field(..., description="User's organizations with roles")
    total: int = Field(..., description="Total number of organizations")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "456e7890-e89b-12d3-a456-426614174000",
                "organizations": [],
                "total": 0
            }
        }
    )


class OrganizationMembersResponse(BaseModel):
    """Schema for organization's member listings"""
    
    organization_id: UUID = Field(..., description="Organization UUID")
    members: List[OrganizationMembershipSummary] = Field(..., description="Organization members")
    total: int = Field(..., description="Total number of members")
    by_role: dict = Field(..., description="Member count by role")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "organization_id": "123e4567-e89b-12d3-a456-426614174000",
                "members": [],
                "total": 0,
                "by_role": {
                    "owner": 1,
                    "admin": 0,
                    "member": 3,
                    "viewer": 2
                }
            }
        }
    )


class InvitationRequest(BaseModel):
    """Schema for inviting a user to an organization"""
    
    user_email: str = Field(..., description="Email of user to invite")
    role: str = Field(default="member", description="Role to assign to the user")
    message: Optional[str] = Field(None, description="Optional invitation message")
    
    @validator('role')
    def validate_role(cls, v):
        valid_roles = ['admin', 'member', 'viewer']  # owners cannot be invited
        if v not in valid_roles:
            raise ValueError(f'Role must be one of: {", ".join(valid_roles)}')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_email": "newuser@example.com",
                "role": "member",
                "message": "Welcome to our organization!"
            }
        }
    )


class AcceptInvitationRequest(BaseModel):
    """Schema for accepting an organization invitation"""
    
    membership_id: UUID = Field(..., description="Membership UUID from invitation")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "membership_id": "789e0123-e89b-12d3-a456-426614174000"
            }
        }
    )