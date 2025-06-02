from sqlalchemy import Column, String, Index, CheckConstraint, ForeignKey
from sqlalchemy.dialects.mssql import NVARCHAR
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from app.db.models.base_entity import BaseEntity


class Organization(BaseEntity):
    """
    Organization model for B2B customer organizations within tenants.

    Represents customer organizations or distinct business units within a tenant,
    often used for B2B subscriptions or departmental separation.
    """

    __tablename__ = "organizations"

    # Organization details
    name = Column(String(255), nullable=False, comment="Organization name")

    domain = Column(
        String(255), nullable=True, comment="Primary email domain for the organization"
    )

    billing_email = Column(
        String(255), nullable=True, comment="Billing contact email address"
    )

    billing_address = Column(
        NVARCHAR(None),  # NVARCHAR(MAX) in SQL Server
        nullable=True,
        comment="Billing address details",
    )

    stripe_customer_id = Column(
        String(255), nullable=True, comment="Stripe customer identifier for billing"
    )

    # Using 'org_metadata' to avoid conflict with SQLAlchemy's reserved 'metadata' attribute
    org_metadata = Column(
        "metadata",  # Column name in database will still be 'metadata'
        NVARCHAR(None),  # NVARCHAR(MAX) for JSON data
        nullable=True,
        comment="Additional organization information (JSON data)",
    )

    # Relationships
    models = relationship("Model", back_populates="organization")
    memberships = relationship("OrganizationMembership", back_populates="organization")

    @declared_attr
    def __table_args__(cls):
        """
        Define organization-specific indexes and constraints.
        Extends BaseEntity's table args with organization-specific requirements.
        """
        # Get base table args from BaseEntity
        base_args = list(super().__table_args__)

        # Add organization-specific indexes
        organization_args = [
            # Unique constraint: organization name must be unique within tenant
            Index(
                "ix_organizations_tenant_name",
                "tenant_id",
                "name",
                unique=True,
                mssql_where="is_deleted = 0",
            ),
            # Index for domain lookups within tenant
            Index(
                "ix_organizations_tenant_domain",
                "tenant_id",
                "domain",
                mssql_where="domain IS NOT NULL AND is_deleted = 0",
            ),
            # Index for Stripe customer ID lookups
            Index(
                "ix_organizations_stripe_customer_id",
                "stripe_customer_id",
                mssql_where="stripe_customer_id IS NOT NULL",
            ),
            # Check constraint for domain format validation
            CheckConstraint(
                "domain IS NULL OR domain LIKE '%.%'",
                name="ck_organizations_domain_format",
            ),
            # Foreign key constraint to tenants table
            # Note: Uncommented since BaseEntity has FK commented out
            # ForeignKey constraint will be added in migration
        ]

        return tuple(base_args + organization_args)

    def __repr__(self):
        """String representation for debugging"""
        return (
            f"<Organization("
            f"id={self.id}, "
            f"tenant_id={self.tenant_id}, "
            f"name='{self.name}', "
            f"domain='{self.domain}'"
            f")>"
        )

    @property
    def display_name(self):
        """Get display name for the organization"""
        return self.name

    @property
    def has_billing_info(self):
        """Check if organization has billing information configured"""
        return bool(self.billing_email or self.stripe_customer_id)

    def get_primary_domain(self):
        """Get the primary domain for this organization"""
        return self.domain

    def is_domain_match(self, email_domain: str) -> bool:
        """Check if an email domain matches this organization's domain"""
        if not self.domain or not email_domain:
            return False
        return self.domain.lower() == email_domain.lower()
    
    def user_belongs_to_organization(self, user_email: str) -> bool:
        """Check if a user email belongs to this organization based on domain"""
        if not self.domain or not user_email or "@" not in user_email:
            return False
        email_domain = user_email.split("@")[1].lower()
        return self.is_domain_match(email_domain)
    
    def get_members(self):
        """Get active members of this organization"""
        return [m for m in self.memberships if m.is_active()]
    
    def get_owners(self):
        """Get owners of this organization"""
        return [m for m in self.memberships if m.is_owner()]
    
    def get_user_role(self, user_id) -> str:
        """Get user's role in this organization"""
        for membership in self.memberships:
            if membership.user_id == user_id and membership.is_active():
                return membership.role
        return None
    
    def get_member_count(self) -> int:
        """Get count of active members"""
        return len(self.get_members())
