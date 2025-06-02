# app/services/organization_service.py
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone
import json

from app.db.models.organization import Organization
from app.repositories import organization_repo
from app.repositories import user_repo
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationRead,
    OrganizationSummary,
    OrganizationListResponse,
)


class OrganizationService:
    """
    Service for organization-focused business operations.

    Handles organization management, membership validation, billing coordination,
    and domain-based operations while maintaining proper business logic
    separation from data access.

    Key Responsibilities:
    - Organization CRUD with business validation
    - Domain membership verification
    - Billing integration coordination
    - Organization-user relationship management
    - Business rule enforcement for organization data
    """

    def __init__(self, db: Session):
        """
        Initialize service with database session.

        Args:
            db: Database session for all operations
        """
        self.db = db
        self.organization_repo = organization_repo
        self.user_repo = user_repo

    # === Core CRUD Operations ===

    def create_organization(
        self, tenant_id: UUID, organization_data: OrganizationCreate
    ) -> OrganizationRead:
        """
        Create a new organization with business validation.

        Args:
            tenant_id: Tenant UUID for isolation
            organization_data: Organization creation data

        Returns:
            Created organization data

        Raises:
            ValueError: If validation fails or name already exists

        Example:
            org_data = OrganizationCreate(name="Acme Corp", domain="acme.com")
            new_org = org_service.create_organization(tenant_id, org_data)
        """
        try:
            # Validate organization name uniqueness
            if self.organization_repo.name_exists(
                self.db, tenant_id, organization_data.name
            ):
                raise ValueError(
                    f"Organization name '{organization_data.name}' already exists"
                )

            # Validate domain format if provided
            if organization_data.domain:
                self._validate_domain_format(organization_data.domain)

            # Validate JSON metadata if provided
            if organization_data.org_metadata:
                self._validate_json_metadata(organization_data.org_metadata)

            # Prepare creation data
            create_data = organization_data.model_dump(exclude_unset=True)

            # Create organization
            db_organization = self.organization_repo.create(
                db=self.db, obj_in=create_data, tenant_id=tenant_id
            )

            # Commit transaction
            self.db.commit()

            # Return formatted response
            return OrganizationRead.model_validate(db_organization)

        except Exception as e:
            self.db.rollback()
            raise e

    def get_organization(
        self, tenant_id: UUID, organization_id: UUID
    ) -> Optional[OrganizationRead]:
        """
        Get organization by ID with tenant isolation.

        Args:
            tenant_id: Tenant UUID for isolation
            organization_id: Organization UUID to retrieve

        Returns:
            Organization data or None if not found
        """
        db_organization = self.organization_repo.get_by_id(
            self.db, tenant_id, organization_id
        )

        if not db_organization:
            return None

        return OrganizationRead.model_validate(db_organization)

    def update_organization(
        self, tenant_id: UUID, organization_id: UUID, update_data: OrganizationUpdate
    ) -> Optional[OrganizationRead]:
        """
        Update organization with business validation.

        Args:
            tenant_id: Tenant UUID for isolation
            organization_id: Organization UUID to update
            update_data: Fields to update

        Returns:
            Updated organization data or None if not found

        Raises:
            ValueError: If validation fails
        """
        try:
            # Get existing organization
            db_organization = self.organization_repo.get_by_id(
                self.db, tenant_id, organization_id
            )

            if not db_organization:
                return None

            # Validate name uniqueness if name is being changed
            if update_data.name and update_data.name != db_organization.name:
                if self.organization_repo.name_exists(
                    self.db, tenant_id, update_data.name, exclude_id=organization_id
                ):
                    raise ValueError(
                        f"Organization name '{update_data.name}' already exists"
                    )

            # Validate domain format if being changed
            if update_data.domain:
                self._validate_domain_format(update_data.domain)

            # Validate JSON metadata if being changed
            if update_data.org_metadata:
                self._validate_json_metadata(update_data.org_metadata)

            # Prepare update data (exclude None values)
            update_dict = update_data.model_dump(exclude_unset=True)

            # Update organization
            updated_organization = self.organization_repo.update(
                db=self.db, db_obj=db_organization, obj_in=update_dict
            )

            # Commit transaction
            self.db.commit()

            return OrganizationRead.model_validate(updated_organization)

        except Exception as e:
            self.db.rollback()
            raise e

    def delete_organization(self, tenant_id: UUID, organization_id: UUID) -> bool:
        """
        Soft delete organization with business validation.

        Args:
            tenant_id: Tenant UUID for isolation
            organization_id: Organization UUID to delete

        Returns:
            True if deletion successful, False if not found

        Note:
            This performs a soft delete, preserving data for audit trails
        """
        try:
            success = self.organization_repo.soft_delete(
                self.db, tenant_id, organization_id
            )

            if success:
                self.db.commit()

            return success

        except Exception as e:
            self.db.rollback()
            raise e

    # === Listing and Search Operations ===

    def list_organizations(
        self, tenant_id: UUID, skip: int = 0, limit: int = 50
    ) -> OrganizationListResponse:
        """
        Get paginated list of organizations for a tenant.

        Args:
            tenant_id: Tenant UUID for isolation
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return

        Returns:
            Paginated organization list with metadata
        """
        # Get organizations
        organizations = self.organization_repo.get_all(
            self.db, tenant_id, skip=skip, limit=limit
        )

        # Get total count
        total = self.organization_repo.count(self.db, tenant_id)

        # Convert to summary format
        org_summaries = [
            OrganizationSummary.model_validate(org) for org in organizations
        ]

        return OrganizationListResponse(
            organizations=org_summaries, total=total, skip=skip, limit=limit
        )

    def search_organizations(
        self, tenant_id: UUID, search_term: str, skip: int = 0, limit: int = 50
    ) -> OrganizationListResponse:
        """
        Search organizations by name or domain.

        Args:
            tenant_id: Tenant UUID for isolation
            search_term: Term to search for in name or domain
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return

        Returns:
            Paginated search results
        """
        # Search organizations
        organizations = self.organization_repo.search_by_name_or_domain(
            self.db, tenant_id, search_term, skip=skip, limit=limit
        )

        # For search, we'd need a separate count method - for now, use found results
        total = len(
            organizations
        )  # This is approximate - you might want to add a search count method

        # Convert to summary format
        org_summaries = [
            OrganizationSummary.model_validate(org) for org in organizations
        ]

        return OrganizationListResponse(
            organizations=org_summaries, total=total, skip=skip, limit=limit
        )

    # === Business Logic Methods ===

    def get_organization_by_name(
        self, tenant_id: UUID, name: str
    ) -> Optional[OrganizationRead]:
        """
        Find organization by name within tenant.

        Args:
            tenant_id: Tenant UUID for isolation
            name: Organization name to search for

        Returns:
            Organization data or None if not found
        """
        db_organization = self.organization_repo.get_by_name(self.db, tenant_id, name)

        if not db_organization:
            return None

        return OrganizationRead.model_validate(db_organization)

    def get_organizations_by_domain(
        self, tenant_id: UUID, domain: str
    ) -> List[OrganizationRead]:
        """
        Find organizations by domain within tenant.

        Args:
            tenant_id: Tenant UUID for isolation
            domain: Email domain to search for

        Returns:
            List of organizations with matching domain
        """
        db_organizations = self.organization_repo.get_by_domain(
            self.db, tenant_id, domain
        )

        return [OrganizationRead.model_validate(org) for org in db_organizations]

    def user_belongs_to_organization(
        self, tenant_id: UUID, user_id: UUID, organization_id: UUID
    ) -> bool:
        """
        Check if a user belongs to a specific organization.

        This method implements the business logic for determining organization
        membership. Currently checks if user's email domain matches organization domain.

        Args:
            tenant_id: Tenant UUID for isolation
            user_id: User UUID to check
            organization_id: Organization UUID to check against

        Returns:
            True if user belongs to organization, False otherwise

        Example:
            belongs = org_service.user_belongs_to_organization(
                tenant_id, user_id, org_id
            )
        """
        try:
            # Get user
            user = self.user_repo.get_by_id(self.db, tenant_id, user_id)
            if not user:
                return False

            # Get organization
            organization = self.organization_repo.get_by_id(
                self.db, tenant_id, organization_id
            )
            if not organization:
                return False

            # Use the organization model's membership check method
            return organization.user_belongs_to_organization(user.email)

        except Exception:
            return False

    def get_user_organizations(
        self, tenant_id: UUID, user_id: UUID
    ) -> List[OrganizationRead]:
        """
        Get all organizations that a user belongs to.

        Args:
            tenant_id: Tenant UUID for isolation
            user_id: User UUID to find organizations for

        Returns:
            List of organizations the user belongs to
        """
        try:
            # Get user
            user = self.user_repo.get_by_id(self.db, tenant_id, user_id)
            if not user:
                return []

            # Get user's email domain
            email_domain = (
                user.email.split("@")[1].lower() if "@" in user.email else None
            )
            if not email_domain:
                return []

            # Find organizations with matching domain
            organizations = self.organization_repo.get_by_domain(
                self.db, tenant_id, email_domain
            )

            return [OrganizationRead.model_validate(org) for org in organizations]

        except Exception:
            return []

    # === Billing Integration ===

    def get_organization_by_stripe_customer(
        self, stripe_customer_id: str
    ) -> Optional[OrganizationRead]:
        """
        Find organization by Stripe customer ID.

        Note: This method doesn't require tenant_id because Stripe IDs are globally unique.

        Args:
            stripe_customer_id: Stripe customer identifier

        Returns:
            Organization data or None if not found
        """
        db_organization = self.organization_repo.get_by_stripe_customer_id(
            self.db, stripe_customer_id
        )

        if not db_organization:
            return None

        return OrganizationRead.model_validate(db_organization)

    def update_stripe_customer_id(
        self, tenant_id: UUID, organization_id: UUID, stripe_customer_id: str
    ) -> Optional[OrganizationRead]:
        """
        Update organization's Stripe customer ID.

        Args:
            tenant_id: Tenant UUID for isolation
            organization_id: Organization UUID to update
            stripe_customer_id: New Stripe customer ID

        Returns:
            Updated organization data or None if not found
        """
        update_data = OrganizationUpdate(stripe_customer_id=stripe_customer_id)
        return self.update_organization(tenant_id, organization_id, update_data)

    def get_organizations_with_billing(
        self, tenant_id: UUID, skip: int = 0, limit: int = 50
    ) -> OrganizationListResponse:
        """
        Get organizations that have billing information configured.

        Args:
            tenant_id: Tenant UUID for isolation
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return

        Returns:
            Paginated list of organizations with billing info
        """
        # Get organizations with billing
        organizations = self.organization_repo.get_organizations_with_billing(
            self.db, tenant_id, skip=skip, limit=limit
        )

        # Get total count (approximate for now)
        total = len(organizations)

        # Convert to summary format
        org_summaries = [
            OrganizationSummary.model_validate(org) for org in organizations
        ]

        return OrganizationListResponse(
            organizations=org_summaries, total=total, skip=skip, limit=limit
        )

    # === Analytics and Reporting ===

    def get_organization_statistics(self, tenant_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive organization statistics for tenant.

        Args:
            tenant_id: Tenant UUID for isolation

        Returns:
            Dictionary with organization analytics
        """
        try:
            total_organizations = self.organization_repo.count(self.db, tenant_id)

            organizations_with_billing = len(
                self.organization_repo.get_organizations_with_billing(
                    self.db, tenant_id, limit=1000
                )
            )

            recent_organizations = self.organization_repo.get_recently_created(
                self.db, tenant_id, days=30, limit=100
            )

            return {
                "total_organizations": total_organizations,
                "organizations_with_billing": organizations_with_billing,
                "recent_organizations_30_days": len(recent_organizations),
                "billing_setup_percentage": round(
                    (organizations_with_billing / max(total_organizations, 1)) * 100, 2
                ),
                "analysis_date": datetime.now(timezone.utc).isoformat(),
            }

        except Exception:
            return {
                "total_organizations": 0,
                "organizations_with_billing": 0,
                "recent_organizations_30_days": 0,
                "billing_setup_percentage": 0,
                "analysis_date": datetime.now(timezone.utc).isoformat(),
            }

    # === Validation Helpers ===

    def _validate_domain_format(self, domain: str) -> None:
        """
        Validate domain format.

        Args:
            domain: Domain string to validate

        Raises:
            ValueError: If domain format is invalid
        """
        if not domain or not isinstance(domain, str):
            raise ValueError("Domain must be a non-empty string")

        # Basic domain validation - contains at least one dot
        if "." not in domain:
            raise ValueError(
                "Domain must contain at least one dot (e.g., 'example.com')"
            )

        # Check for invalid characters (basic validation)
        invalid_chars = [" ", "/", "\\", "@", "#"]
        for char in invalid_chars:
            if char in domain:
                raise ValueError(f"Domain cannot contain '{char}' character")

    def _validate_json_metadata(self, metadata: str) -> None:
        """
        Validate JSON metadata format.

        Args:
            metadata: JSON string to validate

        Raises:
            ValueError: If JSON is invalid
        """
        try:
            json.loads(metadata)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON metadata: {str(e)}")


# Dependency injection helper for FastAPI
def get_organization_service(db: Session) -> OrganizationService:
    """
    Dependency injection helper for FastAPI endpoints.

    Usage in FastAPI:
        @router.post("/organizations")
        async def create_organization(
            org_data: OrganizationCreate,
            current_user: User = Depends(get_current_user),
            org_service: OrganizationService = Depends(get_organization_service)
        ):
            return org_service.create_organization(current_user.tenant_id, org_data)
    """
    return OrganizationService(db)
