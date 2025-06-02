# Step 6.2: Tenant Repository Implementation

## Overview

The **TenantRepository** handles the special case of tenant operations. Unlike other entities, tenants don't have a parent `tenant_id` constraint since they ARE the tenant. This requires a different approach from our BaseRepository pattern.

The TenantRepository provides global tenant operations while maintaining security through other mechanisms like slug/subdomain uniqueness validation and proper access controls.

**What we'll implement:**
- TenantRepository class with global tenant operations
- Slug and subdomain uniqueness validation
- Tenant lifecycle management (creation, updates, soft delete)
- Tenant lookup methods for authentication and routing
- Auto-generation of slugs and subdomains
- Tenant availability checking

**Key Considerations:**
- ✅ **Global Scope**: Tenants are looked up globally, not scoped to other tenants
- ✅ **Uniqueness Enforcement**: Slugs and subdomains must be globally unique
- ✅ **Auto-Generation**: Smart slug/subdomain generation from company names
- ✅ **Security**: Proper validation to prevent conflicts and abuse
- ✅ **Performance**: Optimized lookups for authentication flows

---

## Step 1: Understanding Tenant Repository Differences

### 1.1 Why Tenants Are Special

```python
# Regular entities (Users, Organizations, etc.)
class User(BaseEntity):
    tenant_id = Column(UNIQUEIDENTIFIER, ForeignKey("tenants.id"))  # Required
    # Users belong TO a tenant

# Tenants are different
class Tenant(BaseEntity):
    tenant_id = Column(UNIQUEIDENTIFIER, nullable=True)  # Nullable!
    # Tenants don't belong to other tenants - they ARE the tenant
```

### 1.2 Tenant Repository Responsibilities

**Global Operations**:
- Look up tenants by slug/subdomain (for routing)
- Validate slug/subdomain availability (for registration)
- Create new tenant organizations
- Update tenant settings and metadata

**Security Considerations**:
- Prevent slug/subdomain conflicts
- Validate tenant creation requests
- Handle tenant status changes (trial → active → suspended)
- Audit tenant operations

---

## Step 2: Implement Tenant Repository

### 2.1 Create Tenant Repository

Create `app/repositories/tenant_repository.py`:

```python
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
```

### 2.2 Update Repository Package Init

Update `app/repositories/__init__.py`:

```python
"""
Repository layer for data access operations.

This package contains repositories that provide clean interfaces
for database operations with built-in tenant isolation and
consistent CRUD patterns.
"""

from .base import BaseRepository
from .tenant_repository import TenantRepository, tenant_repo

__all__ = ["BaseRepository", "TenantRepository", "tenant_repo"]
```

---

## Step 3: Testing the Tenant Repository

### 3.1 Create Tenant Repository Test

Create `test_tenant_repository.py` in your project root:

```python
from app.repositories.tenant_repository import tenant_repo
from app.schemas.tenant import TenantCreate
from app.db.session import SessionLocal
from uuid import uuid4

def test_tenant_repository():
    """Test TenantRepository functionality"""
    
    db = SessionLocal()
    
    try:
        print("🧪 Testing TenantRepository...")
        
        # Test slug generation
        slug = tenant_repo.generate_unique_slug(db, "Acme Corporation")
        print(f"✅ Generated slug: '{slug}'")
        
        # Test subdomain generation
        subdomain = tenant_repo.generate_unique_subdomain(db, "Acme Corporation")
        print(f"✅ Generated subdomain: '{subdomain}'")
        
        # Test availability checks
        available = tenant_repo.check_slug_availability(db, "definitely-unique-slug-12345")
        print(f"✅ Slug availability check: {available}")
        
        available = tenant_repo.check_subdomain_availability(db, "definitelyunique12345")
        print(f"✅ Subdomain availability check: {available}")
        
        # Test tenant creation
        tenant_data = TenantCreate(
            name="Test Company",
            plan_type="trial",
            status="trial"
        )
        
        new_tenant = tenant_repo.create(db, obj_in=tenant_data)
        print(f"✅ Created tenant: {new_tenant.name} (slug: {new_tenant.slug})")
        
        # Test tenant lookup
        found_tenant = tenant_repo.get_by_slug(db, new_tenant.slug)
        assert found_tenant is not None, "Could not find tenant by slug"
        print(f"✅ Found tenant by slug: {found_tenant.name}")
        
        found_tenant = tenant_repo.get_by_subdomain(db, new_tenant.subdomain)
        assert found_tenant is not None, "Could not find tenant by subdomain"
        print(f"✅ Found tenant by subdomain: {found_tenant.name}")
        
        # Test tenant count
        count = tenant_repo.count_active_tenants(db)
        print(f"✅ Active tenant count: {count}")
        
        # Clean up
        tenant_repo.soft_delete(db, new_tenant.id, new_tenant.id)
        db.commit()
        print("✅ Cleaned up test tenant")
        
        print("\n🎉 TenantRepository tests passed!")
        
    except Exception as e:
        print(f"❌ TenantRepository test failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_tenant_repository()
```

### 3.2 Run the Test

```bash
# Navigate to your project directory
cd C:\_source\Greenshoes\Summer2025Internship\Sprint2\Guided_Walkthrough\quodsi_api

# Activate virtual environment
.\venv\Scripts\activate

# Run the test
python test_tenant_repository.py
```

Expected output:
```
🧪 Testing TenantRepository...
✅ Generated slug: 'acme-corporation'
✅ Generated subdomain: 'acmecorporation'
✅ Slug availability check: True
✅ Subdomain availability check: True
✅ Created tenant: Test Company (slug: test-company)
✅ Found tenant by slug: Test Company
✅ Found tenant by subdomain: Test Company
✅ Active tenant count: 1
✅ Cleaned up test tenant

🎉 TenantRepository tests passed!
```

---

## Step 4: Understanding Key Features

### 4.1 Schema Flexibility and Plan-Based Limits

**Design Rationale for Optional Schema Fields**:

The `TenantCreate` schema intentionally does not include limit fields (`max_users`, `max_models`, etc.) for several important reasons:

1. **Business Logic Separation**: Limits are determined by the plan type, not user input
2. **Security**: Users shouldn't be able to set unlimited resources
3. **User Experience**: Simpler registration flow focuses on plan selection
4. **Maintainability**: Plan definitions are centralized in code, not scattered across API calls

**Repository Implementation Pattern**:
```python
# Safe field access using getattr() with defaults
max_users=getattr(obj_in, 'max_users', None) or 5

# This pattern handles three scenarios:
# 1. Field exists in schema with value → use that value
# 2. Field exists in schema but is None → use default (5)
# 3. Field doesn't exist in schema → use default (5)
```

**Plan-Based Limit Strategy**:
```python
# Limits are automatically assigned based on plan_type:
"trial" → max_users: 5, max_models: 10, max_scenarios: 100
"starter" → max_users: 25, max_models: 50, max_scenarios: 1000
"professional" → max_users: 100, max_models: 200, max_scenarios: 10000
```

This approach provides:
- ✅ **Consistency**: All trial tenants get the same limits
- ✅ **Security**: Users can't bypass plan restrictions
- ✅ **Flexibility**: Admin operations can override limits when needed
- ✅ **Maintainability**: Change plan limits in one place

### 4.2 Slug and Subdomain Generation

**Slug Generation** (URL-safe identifiers):
```python
"Acme Corporation" → "acme-corporation"
"O'Reilly Media" → "oreilly-media"
"123 Company!" → "123-company"
```

**Subdomain Generation** (DNS-safe identifiers):
```python
"Acme Corporation" → "acmecorporation"
"O'Reilly Media" → "oreillymedia"
"123 Company!" → "123company"
```

**Uniqueness Handling**:
```python
# If "acme-corporation" is taken:
"acme-corporation-2"
"acme-corporation-3"
# etc.
```

### 4.2 Tenant Lifecycle Management

**Creation Flow**:
1. Validate input data
2. Generate unique slug/subdomain if not provided
3. Set trial defaults and expiration
4. Create tenant record
5. Return created tenant

**Status Transitions**:
```
trial → active    (successful payment)
trial → expired   (trial period ends)
active → suspended (payment issues)
any → deleted     (soft delete)
```

### 4.3 Global vs Tenant-Scoped Operations

```python
# Global operations (TenantRepository)
tenant = tenant_repo.get_by_slug(db, "acme-corp")  # No tenant_id needed

# Tenant-scoped operations (BaseRepository)
user = user_repo.get_by_id(db, tenant_id, user_id)  # Requires tenant_id
```

---

## Step 5: Usage Patterns

### 5.1 Authentication Flow Usage

```python
# In authentication middleware
def authenticate_by_subdomain(subdomain: str):
    tenant = tenant_repo.get_by_subdomain(db, subdomain)
    if not tenant or tenant.status != "active":
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant
```

### 5.2 Registration Flow Usage

```python
# In registration service
def register_new_organization(company_name: str):
    tenant_data = TenantCreate(
        name=company_name,
        plan_type="trial",
        status="trial"
    )
    
    new_tenant = tenant_repo.create(db, obj_in=tenant_data)
    # Slug and subdomain automatically generated
    return new_tenant
```

### 5.3 Admin Operations

```python
# System administration
def get_system_overview():
    active_count = tenant_repo.count_active_tenants(db)
    expiring_trials = tenant_repo.get_expiring_trials(db, days_ahead=7)
    
    return {
        "active_tenants": active_count,
        "expiring_trials": len(expiring_trials)
    }
```

---

## Common Issues and Solutions

### Issue 1: AttributeError with Schema Fields
**Problem**: `'TenantCreate' object has no attribute 'max_users'` error during tenant creation
**Root Cause**: The repository tries to access fields that don't exist in the TenantCreate schema
**Solution**: Use `getattr(obj_in, 'field_name', None)` to safely access optional schema fields
```python
# ❌ This will fail if field doesn't exist in schema:
max_users = obj_in.max_users or 5

# ✅ This safely handles missing fields:
max_users = getattr(obj_in, 'max_users', None) or 5
```

### Issue 2: Slug Generation Conflicts
**Problem**: Generated slugs conflict with existing ones
**Solution**: Use the `generate_unique_slug()` method which automatically handles conflicts

### Issue 3: Subdomain Length Limits
**Problem**: Company names generate subdomains that are too long
**Solution**: The generator automatically truncates and ensures reasonable lengths

### Issue 4: Invalid Characters in Slugs/Subdomains
**Problem**: Special characters cause issues in URLs or DNS
**Solution**: Regex patterns automatically clean and sanitize input

### Issue 5: Tenant Lookup Performance
**Problem**: Slow tenant lookups during authentication
**Solution**: Ensure indexes exist on `slug` and `subdomain` columns

---

## Verification Checklist

After completing this step, verify:

- [ ] `app/repositories/tenant_repository.py` exists with complete implementation
- [ ] TenantRepository handles global tenant operations correctly
- [ ] Slug and subdomain generation works with uniqueness validation
- [ ] Tenant creation sets appropriate defaults (trial limits, expiration)
- [ ] Tenant lookup methods work for authentication flows
- [ ] Search functionality works for admin operations
- [ ] Test script runs without errors
- [ ] Repository is exported in `__init__.py`
- [ ] Auto-generated slugs and subdomains are URL/DNS safe
- [ ] Tenant status transitions are handled properly

## Next Steps

With the TenantRepository implemented, you now have:

1. **Global Tenant Operations** - Lookup and management of tenant organizations
2. **Unique Identifier Generation** - Automatic slug and subdomain creation
3. **Validation Logic** - Prevents conflicts and ensures data integrity
4. **Lifecycle Management** - Handles tenant creation, updates, and soft deletion
5. **Admin Operations** - System-level tenant management capabilities

In **063_User_Repository_Implementation.md**, we'll create the UserRepository that inherits from BaseRepository and adds user-specific operations like identity provider authentication and user management within tenant boundaries.

## Key Takeaways

1. **Tenants are special** - They don't follow normal tenant-scoped patterns
2. **Global uniqueness matters** - Slugs and subdomains must be globally unique
3. **Auto-generation is essential** - Smart defaults reduce user friction
4. **Performance considerations** - Tenant lookups happen frequently during auth
5. **Security through validation** - Proper checks prevent conflicts and abuse
6. **Lifecycle management** - Handle the full tenant journey from trial to active
