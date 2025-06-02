# app/repositories/organization_repository.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.repositories.base import BaseRepository
from app.db.models.organization import Organization


class OrganizationRepository(BaseRepository[Organization]):
    """
    Repository for Organization entity with organization-specific operations.

    Provides tenant-scoped CRUD operations plus organization-specific queries
    like finding by name, domain, and membership operations.
    """

    def __init__(self):
        """Initialize OrganizationRepository with Organization model."""
        super().__init__(Organization)

    def get_by_name(
        self, db: Session, tenant_id: UUID, name: str
    ) -> Optional[Organization]:
        """
        Find an organization by name within a specific tenant.

        Organization names are unique within a tenant, so this should return
        at most one result.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            name: Organization name to search for (case-sensitive)

        Returns:
            Organization instance or None if not found

        Example:
            org = org_repo.get_by_name(db, tenant_id, "Acme Corporation")
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.name == name,
                    self.model.is_deleted == False,
                )
            )
            .first()
        )

    def get_by_domain(
        self, db: Session, tenant_id: UUID, domain: str
    ) -> List[Organization]:
        """
        Find organizations by domain within a tenant.

        Multiple organizations could potentially share a domain in some
        business scenarios, so this returns a list.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            domain: Email domain to search for (case-insensitive)

        Returns:
            List of Organization instances (may be empty)

        Example:
            orgs = org_repo.get_by_domain(db, tenant_id, "acme.com")
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.domain.ilike(domain.lower()),  # Case-insensitive search
                    self.model.is_deleted == False,
                )
            )
            .order_by(self.model.name)
            .all()
        )

    def get_by_stripe_customer_id(
        self, db: Session, stripe_customer_id: str
    ) -> Optional[Organization]:
        """
        Find an organization by Stripe customer ID.

        Note: This is one of the few queries that doesn't require tenant_id
        because Stripe customer IDs are globally unique.

        Args:
            db: Database session
            stripe_customer_id: Stripe customer identifier

        Returns:
            Organization instance or None if not found

        Example:
            org = org_repo.get_by_stripe_customer_id(db, "cus_1234567890")
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.stripe_customer_id == stripe_customer_id,
                    self.model.is_deleted == False,
                )
            )
            .first()
        )

    def name_exists(
        self, db: Session, tenant_id: UUID, name: str, exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if an organization name already exists within a tenant.

        Useful for validation during creation and updates to enforce
        unique name constraints.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            name: Organization name to check
            exclude_id: Optional organization ID to exclude from check (for updates)

        Returns:
            True if name exists, False otherwise

        Example:
            # For creation
            if org_repo.name_exists(db, tenant_id, "New Corp"):
                raise ValueError("Organization name already exists")

            # For updates
            if org_repo.name_exists(db, tenant_id, "Updated Name", exclude_id=org.id):
                raise ValueError("Organization name already exists")
        """
        query = db.query(self.model.id).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.name == name,
                self.model.is_deleted == False,
            )
        )

        # Exclude current organization when checking for updates
        if exclude_id:
            query = query.filter(self.model.id != exclude_id)

        return query.first() is not None

    def search_by_name_or_domain(
        self,
        db: Session,
        tenant_id: UUID,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Organization]:
        """
        Search organizations by name or domain within a tenant.

        Performs case-insensitive partial matching on both name and domain fields.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            search_term: Term to search for in name or domain
            skip: Pagination offset
            limit: Maximum results to return

        Returns:
            List of matching organizations ordered by name

        Example:
            orgs = org_repo.search_by_name_or_domain(db, tenant_id, "acme")
        """
        return self.search(
            db=db,
            tenant_id=tenant_id,
            search_term=search_term,
            search_fields=["name", "domain"],
            skip=skip,
            limit=limit,
        )

    def get_organizations_with_billing(
        self, db: Session, tenant_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Organization]:
        """
        Get organizations that have billing information configured.

        Returns organizations that have either a billing email or Stripe customer ID.
        Useful for billing and financial operations.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            skip: Pagination offset
            limit: Maximum results to return

        Returns:
            List of organizations with billing information
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.is_deleted == False,
                    # Has either billing email or Stripe customer ID
                    (
                        (self.model.billing_email.isnot(None))
                        | (self.model.stripe_customer_id.isnot(None))
                    ),
                )
            )
            .order_by(self.model.name)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_by_domain(self, db: Session, tenant_id: UUID, domain: str) -> int:
        """
        Count organizations with a specific domain within a tenant.

        Useful for analytics and domain management operations.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            domain: Email domain to count

        Returns:
            Number of organizations with the specified domain
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.domain.ilike(domain.lower()),
                    self.model.is_deleted == False,
                )
            )
            .count()
        )

    def get_recently_created(
        self, db: Session, tenant_id: UUID, days: int = 30, limit: int = 50
    ) -> List[Organization]:
        """
        Get organizations created within the specified number of days.

        Useful for onboarding dashboards and recent activity views.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            days: Number of days back to search (default: 30)
            limit: Maximum results to return

        Returns:
            List of recently created organizations ordered by creation date (newest first)
        """
        return self.get_recent(db=db, tenant_id=tenant_id, days=days, limit=limit)
