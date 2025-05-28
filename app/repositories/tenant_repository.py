from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, List, Dict, Any
from uuid import UUID
from app.db.models.tenant import Tenant
from app.schemas.tenant import TenantCreate

class TenantRepository:
    """
    Repository for tenant operations.
    
    Unlike other repositories, TenantRepository operates globally since
    tenants don't have a parent tenant_id constraint. Tenants ARE the
    top-level organizational unit in our multi-tenant architecture.
    
    Security is enforced through:
    - Slug/subdomain uniqueness validation
    - Tenant status checks
    - Proper access controls in the service layer
    """
    
    def get_by_id(self, db: Session, id: UUID) -> Optional[Tenant]:
        """
        Get tenant by UUID.
        
        This is a global lookup - no tenant scoping needed since
        tenants are the top-level organizational unit.
        
        Args:
            db: Database session
            id: Tenant UUID
            
        Returns:
            Tenant instance or None if not found
        """
        return db.query(Tenant).filter(
            and_(
                Tenant.id == id,
                Tenant.is_deleted == False
            )
        ).first()
    
    def get_by_slug(self, db: Session, slug: str) -> Optional[Tenant]:
        """
        Get tenant by slug (unique identifier for routing).
        
        Slugs are used in URLs and API routing to identify tenants.
        Example: https://api.quodsi.com/tenants/acme-corp/...
        
        Args:
            db: Database session
            slug: Tenant slug (URL-safe identifier)
            
        Returns:
            Tenant instance or None if not found
        """
        return db.query(Tenant).filter(
            and_(
                Tenant.slug == slug,
                Tenant.is_deleted == False
            )
        ).first()
    
    def get_by_subdomain(self, db: Session, subdomain: str) -> Optional[Tenant]:
        """
        Get tenant by subdomain (for subdomain-based routing).
        
        Subdomains are used for tenant-specific web interfaces.
        Example: https://acme-corp.quodsi.com
        
        Args:
            db: Database session
            subdomain: Tenant subdomain
            
        Returns:
            Tenant instance or None if not found
        """
        return db.query(Tenant).filter(
            and_(
                Tenant.subdomain == subdomain,
                Tenant.is_deleted == False
            )
        ).first()
    
    def check_slug_availability(self, db: Session, slug: str, exclude_id: Optional[UUID] = None) -> bool:
        """
        Check if a slug is available for use.
        
        Used during tenant creation and updates to prevent conflicts.
        
        Args:
            db: Database session
            slug: Slug to check
            exclude_id: Tenant ID to exclude from check (for updates)
            
        Returns:
            True if slug is available, False if taken
        """
        query = db.query(Tenant.id).filter(
            and_(
                Tenant.slug == slug,
                Tenant.is_deleted == False
            )
        )
        
        # Exclude specific tenant (useful for updates)
        if exclude_id:
            query = query.filter(Tenant.id != exclude_id)
        
        return query.first() is None
    
    def check_subdomain_availability(self, db: Session, subdomain: str, exclude_id: Optional[UUID] = None) -> bool:
        """
        Check if a subdomain is available for use.
        
        Args:
            db: Database session
            subdomain: Subdomain to check
            exclude_id: Tenant ID to exclude from check (for updates)
            
        Returns:
            True if subdomain is available, False if taken
        """
        query = db.query(Tenant.id).filter(
            and_(
                Tenant.subdomain == subdomain,
                Tenant.is_deleted == False
            )
        )
        
        # Exclude specific tenant (useful for updates)
        if exclude_id:
            query = query.filter(Tenant.id != exclude_id)
        
        return query.first() is None
    
    def generate_unique_slug(self, db: Session, name: str, exclude_id: Optional[UUID] = None) -> str:
        """
        Generate a unique slug from a company name.
        
        Creates URL-safe slugs and ensures uniqueness by appending
        numbers if conflicts exist.
        
        Args:
            db: Database session
            name: Company name to convert to slug
            exclude_id: Tenant ID to exclude from uniqueness check
            
        Returns:
            Unique slug string
            
        Example:
            "Acme Corporation" -> "acme-corporation"
            If taken: "acme-corporation-2", "acme-corporation-3", etc.
        """
        import re
        
        # Convert name to slug format
        # Remove special characters, convert to lowercase, replace spaces with hyphens
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
        slug = re.sub(r'\s+', '-', slug.strip())
        slug = re.sub(r'-+', '-', slug)  # Remove multiple consecutive hyphens
        slug = slug.strip('-')  # Remove leading/trailing hyphens
        
        # Ensure minimum length
        if len(slug) < 3:
            slug = f"tenant-{slug}"
        
        # Check availability and add suffix if needed
        original_slug = slug
        counter = 1
        
        while not self.check_slug_availability(db, slug, exclude_id):
            counter += 1
            slug = f"{original_slug}-{counter}"
        
        return slug
    
    def generate_unique_subdomain(self, db: Session, name: str, exclude_id: Optional[UUID] = None) -> str:
        """
        Generate a unique subdomain from a company name.
        
        Similar to slug generation but optimized for subdomain use.
        
        Args:
            db: Database session
            name: Company name to convert to subdomain
            exclude_id: Tenant ID to exclude from uniqueness check
            
        Returns:
            Unique subdomain string
        """
        import re
        
        # Convert name to subdomain format (similar to slug but more restrictive)
        subdomain = re.sub(r'[^a-zA-Z0-9]', '', name.lower())
        
        # Ensure minimum length
        if len(subdomain) < 3:
            subdomain = f"tenant{subdomain}"
        
        # Limit maximum length for subdomains
        if len(subdomain) > 20:
            subdomain = subdomain[:20]
        
        # Check availability and add suffix if needed
        original_subdomain = subdomain
        counter = 1
        
        while not self.check_subdomain_availability(db, subdomain, exclude_id):
            counter += 1
            # Keep within reasonable length limits
            base_length = min(len(original_subdomain), 15)
            subdomain = f"{original_subdomain[:base_length]}{counter}"
        
        return subdomain
    
    def create(self, db: Session, *, obj_in: TenantCreate) -> Tenant:
        """
        Create a new tenant with auto-generated slug and subdomain if needed.
        
        Handles the complex logic of ensuring unique slugs/subdomains
        and setting appropriate defaults for new tenants.
        
        Args:
            db: Database session
            obj_in: Tenant creation schema
            
        Returns:
            Created tenant instance
            
        Raises:
            ValueError: If provided slug/subdomain is already taken
        """
        # Generate slug if not provided
        slug = obj_in.slug
        if not slug:
            slug = self.generate_unique_slug(db, obj_in.name)
        else:
            # Validate provided slug is available
            if not self.check_slug_availability(db, slug):
                raise ValueError(f"Slug '{slug}' is already taken")
        
        # Generate subdomain if not provided
        subdomain = obj_in.subdomain
        if not subdomain:
            subdomain = self.generate_unique_subdomain(db, obj_in.name)
        else:
            # Validate provided subdomain is available
            if not self.check_subdomain_availability(db, subdomain):
                raise ValueError(f"Subdomain '{subdomain}' is already taken")
        
        # Create tenant with generated/validated values
        db_obj = Tenant(
            name=obj_in.name,
            slug=slug,
            subdomain=subdomain,
            plan_type=obj_in.plan_type,
            status=obj_in.status,
            # Set tenant_id to None (tenants don't belong to other tenants)
            tenant_id=None,
            # Set trial defaults (use getattr to handle optional schema fields)
            # The TenantCreate schema may not include limit fields, so we use getattr
            # with defaults to ensure plan-based limits are applied automatically
            max_users=getattr(obj_in, 'max_users', None) or 5,
            max_models=getattr(obj_in, 'max_models', None) or 10,
            max_scenarios_per_month=getattr(obj_in, 'max_scenarios_per_month', None) or 100,
            max_storage_gb=getattr(obj_in, 'max_storage_gb', None) or 1.0,
            # Set billing email if provided in schema
            billing_email=getattr(obj_in, 'billing_email', None)
        )
        
        # Add trial expiration if it's a trial tenant
        if obj_in.plan_type == "trial":
            from datetime import datetime, timezone, timedelta
            db_obj.trial_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        
        db.add(db_obj)
        db.flush()  # Flush to get the generated ID
        db.refresh(db_obj)
        
        return db_obj
    
    def update(self, db: Session, *, db_obj: Tenant, obj_in: Dict[str, Any]) -> Tenant:
        """
        Update tenant with validation for unique constraints.
        
        Ensures that slug/subdomain changes don't conflict with existing tenants.
        
        Args:
            db: Database session
            db_obj: Existing tenant instance
            obj_in: Dictionary of fields to update
            
        Returns:
            Updated tenant instance
            
        Raises:
            ValueError: If slug/subdomain conflicts exist
        """
        from datetime import datetime, timezone
        
        # Validate slug uniqueness if being changed
        if "slug" in obj_in and obj_in["slug"] != db_obj.slug:
            if not self.check_slug_availability(db, obj_in["slug"], exclude_id=db_obj.id):
                raise ValueError(f"Slug '{obj_in['slug']}' is already taken")
        
        # Validate subdomain uniqueness if being changed
        if "subdomain" in obj_in and obj_in["subdomain"] != db_obj.subdomain:
            if not self.check_subdomain_availability(db, obj_in["subdomain"], exclude_id=db_obj.id):
                raise ValueError(f"Subdomain '{obj_in['subdomain']}' is already taken")
        
        # Update fields (excluding protected fields)
        protected_fields = {"id", "index_id", "created_at", "tenant_id"}
        
        for field, value in obj_in.items():
            if field not in protected_fields and hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        # Handle status changes
        if "status" in obj_in:
            if obj_in["status"] == "active" and db_obj.status != "active":
                # Activating tenant
                db_obj.activated_at = datetime.now(timezone.utc)
        
        # Update timestamp
        db_obj.updated_at = datetime.now(timezone.utc)
        
        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        
        return db_obj
    
    def soft_delete(self, db: Session, tenant_id: UUID, id: UUID) -> bool:
        """
        Soft delete a tenant.
        
        Note: The tenant_id parameter is ignored for tenants since they
        don't have parent tenants, but we maintain the signature for
        consistency with other repositories.
        
        ⚠️  WARNING: Soft deleting a tenant effectively disables the entire
        organization. This should only be done with proper authorization.
        
        Args:
            db: Database session
            tenant_id: Ignored (for signature consistency)
            id: Tenant UUID to soft delete
            
        Returns:
            True if tenant was found and deleted, False otherwise
        """
        from datetime import datetime, timezone
        
        db_obj = self.get_by_id(db, id)
        if db_obj:
            db_obj.is_deleted = True
            db_obj.status = "deleted"
            db_obj.updated_at = datetime.now(timezone.utc)
            db.add(db_obj)
            db.flush()
            return True
        return False
    
    def get_active_tenants(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Tenant]:
        """
        Get all active tenants (admin operation).
        
        This is typically used for admin dashboards and system monitoring.
        Should be restricted to system administrators.
        
        Args:
            db: Database session
            skip: Pagination offset
            limit: Maximum results to return
            
        Returns:
            List of active tenants
        """
        return db.query(Tenant).filter(
            and_(
                Tenant.status == "active",
                Tenant.is_deleted == False
            )
        ).order_by(Tenant.created_at.desc()).offset(skip).limit(limit).all()
    
    def count_active_tenants(self, db: Session) -> int:
        """
        Count all active tenants.
        
        Useful for system metrics and billing calculations.
        
        Args:
            db: Database session
            
        Returns:
            Number of active tenants
        """
        return db.query(Tenant).filter(
            and_(
                Tenant.status == "active",
                Tenant.is_deleted == False
            )
        ).count()
    
    def get_tenants_by_plan(self, db: Session, plan_type: str, *, skip: int = 0, limit: int = 100) -> List[Tenant]:
        """
        Get tenants filtered by plan type.
        
        Useful for billing operations and plan migration tasks.
        
        Args:
            db: Database session
            plan_type: Plan type to filter by (e.g., "trial", "basic", "premium")
            skip: Pagination offset
            limit: Maximum results to return
            
        Returns:
            List of tenants with the specified plan type
        """
        return db.query(Tenant).filter(
            and_(
                Tenant.plan_type == plan_type,
                Tenant.is_deleted == False
            )
        ).order_by(Tenant.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_expiring_trials(self, db: Session, *, days_ahead: int = 7) -> List[Tenant]:
        """
        Get trial tenants that will expire within the specified number of days.
        
        Used for automated trial expiration notifications and cleanup tasks.
        
        Args:
            db: Database session
            days_ahead: Number of days to look ahead for expiring trials
            
        Returns:
            List of tenants with trials expiring soon
        """
        from datetime import datetime, timezone, timedelta
        
        cutoff_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
        
        return db.query(Tenant).filter(
            and_(
                Tenant.plan_type == "trial",
                Tenant.status == "trial",
                Tenant.trial_expires_at <= cutoff_date,
                Tenant.trial_expires_at > datetime.now(timezone.utc),  # Not already expired
                Tenant.is_deleted == False
            )
        ).order_by(Tenant.trial_expires_at).all()
    
    def search_tenants(self, db: Session, *, search_term: str, skip: int = 0, limit: int = 100) -> List[Tenant]:
        """
        Search tenants by name, slug, or subdomain.
        
        Admin operation for finding tenants in the system.
        
        Args:
            db: Database session
            search_term: Term to search for
            skip: Pagination offset
            limit: Maximum results to return
            
        Returns:
            List of matching tenants
        """
        if not search_term.strip():
            return self.get_active_tenants(db, skip=skip, limit=limit)
        
        search_pattern = f"%{search_term}%"
        
        return db.query(Tenant).filter(
            and_(
                Tenant.is_deleted == False,
                or_(
                    Tenant.name.ilike(search_pattern),
                    Tenant.slug.ilike(search_pattern),
                    Tenant.subdomain.ilike(search_pattern)
                )
            )
        ).order_by(Tenant.created_at.desc()).offset(skip).limit(limit).all()


# Create singleton instance for dependency injection
tenant_repo = TenantRepository()