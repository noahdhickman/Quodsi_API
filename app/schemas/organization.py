# app/schemas/organization.py
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, EmailStr


class OrganizationBase(BaseModel):
    """Base organization schema with common fields"""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Organization name"
    )
    domain: Optional[str] = Field(
        None, max_length=255, description="Primary email domain"
    )
    billing_email: Optional[EmailStr] = Field(None, description="Billing contact email")
    billing_address: Optional[str] = Field(None, description="Billing address details")


class OrganizationCreate(OrganizationBase):
    """Schema for creating a new organization"""

    # Inherits all fields from OrganizationBase
    # tenant_id will be automatically set from the authenticated user's context
    stripe_customer_id: Optional[str] = Field(
        None, max_length=255, description="Stripe customer ID"
    )
    org_metadata: Optional[str] = Field(
        None, description="Additional organization information (JSON)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Acme Corporation",
                "domain": "acme.com",
                "billing_email": "billing@acme.com",
                "billing_address": "123 Business Ave, Suite 100, City, State 12345",
                "stripe_customer_id": "cus_1234567890",
                "org_metadata": '{"industry": "technology", "size": "medium"}',
            }
        }
    )


class OrganizationUpdate(BaseModel):
    """Schema for updating an existing organization"""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Organization name"
    )
    domain: Optional[str] = Field(
        None, max_length=255, description="Primary email domain"
    )
    billing_email: Optional[EmailStr] = Field(None, description="Billing contact email")
    billing_address: Optional[str] = Field(None, description="Billing address details")
    stripe_customer_id: Optional[str] = Field(
        None, max_length=255, description="Stripe customer ID"
    )
    org_metadata: Optional[str] = Field(
        None, description="Additional organization information (JSON)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Acme Corporation Ltd",
                "billing_email": "newbilling@acme.com",
                "org_metadata": '{"industry": "technology", "size": "large"}',
            }
        }
    )


class OrganizationRead(OrganizationBase):
    """Schema for reading organization data"""

    id: UUID = Field(..., description="Organization unique identifier")
    tenant_id: UUID = Field(..., description="Tenant this organization belongs to")
    stripe_customer_id: Optional[str] = Field(None, description="Stripe customer ID")
    org_metadata: Optional[str] = Field(
        None, description="Additional organization information (JSON)"
    )
    created_at: datetime = Field(..., description="When the organization was created")
    updated_at: datetime = Field(
        ..., description="When the organization was last updated"
    )
    is_deleted: bool = Field(
        ..., description="Whether the organization is soft deleted"
    )

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM mode for SQLAlchemy models
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "tenant_id": "456e7890-e89b-12d3-a456-426614174000",
                "name": "Acme Corporation",
                "domain": "acme.com",
                "billing_email": "billing@acme.com",
                "billing_address": "123 Business Ave, Suite 100, City, State 12345",
                "stripe_customer_id": "cus_1234567890",
                "org_metadata": '{"industry": "technology", "size": "medium"}',
                "created_at": "2025-06-02T12:00:00.000Z",
                "updated_at": "2025-06-02T12:00:00.000Z",
                "is_deleted": False,
            }
        },
    )


class OrganizationSummary(BaseModel):
    """Lightweight schema for organization listings"""

    id: UUID = Field(..., description="Organization unique identifier")
    name: str = Field(..., description="Organization name")
    domain: Optional[str] = Field(None, description="Primary email domain")
    created_at: datetime = Field(..., description="When the organization was created")

    model_config = ConfigDict(from_attributes=True)


class OrganizationListResponse(BaseModel):
    """Schema for paginated organization listings"""

    organizations: list[OrganizationSummary] = Field(
        ..., description="List of organizations"
    )
    total: int = Field(..., description="Total number of organizations")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "organizations": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Acme Corporation",
                        "domain": "acme.com",
                        "created_at": "2025-06-02T12:00:00.000Z",
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 50,
            }
        }
    )
