# Step 6.3: User Repository Implementation

## Overview

The **UserRepository** demonstrates how to extend the BaseRepository pattern with entity-specific operations. It inherits all the tenant-scoped CRUD functionality from BaseRepository while adding user-specific methods for authentication, identity provider integration, and user management.

This implementation shows how specialized repositories build upon the generic foundation while maintaining tenant isolation and adding domain-specific functionality.

**What we'll implement:**
- UserRepository class inheriting from BaseRepository[User]
- Identity provider authentication methods
- Email-based user lookups within tenants
- User creation and validation
- Basic activity tracking methods

**Key Features:**
- ✅ **Inherits BaseRepository**: Gets all standard CRUD operations automatically
- ✅ **Identity Provider Integration**: Supports multiple authentication providers
- ✅ **Tenant-Scoped Operations**: All user operations respect tenant boundaries
- ✅ **Authentication Support**: Methods for login and user verification
- ✅ **Email Validation**: Ensures uniqueness within tenant boundaries

---

## Step 1: Understanding Repository Inheritance

### 1.1 How UserRepository Extends BaseRepository

```python
# BaseRepository provides generic operations:
class BaseRepository(Generic[ModelType]):
    def get_by_id(self, db: Session, tenant_id: UUID, id: UUID) -> Optional[ModelType]
    def get_all(self, db: Session, tenant_id: UUID, *, skip: int = 0, limit: int = 100)
    def create(self, db: Session, *, obj_in: Dict[str, Any], tenant_id: UUID)
    # ... etc

# UserRepository inherits AND extends:
class UserRepository(BaseRepository[User]):
    # Gets all BaseRepository methods automatically
    # PLUS adds user-specific methods:
    def get_by_email(self, db: Session, tenant_id: UUID, email: str)
    def get_by_identity_provider_id(self, db: Session, provider: str, provider_id: str)
    def update_login_stats(self, db: Session, tenant_id: UUID, user_id: UUID)
    # ... etc
```

### 1.2 User-Specific Considerations

**Identity Provider Authentication**:
- Users can authenticate through multiple providers (Entra ID, Google, local dev)
- Identity provider IDs are globally unique (no tenant scoping needed for auth)
- Email addresses are unique within each tenant (not globally)

**Activity Tracking**:
- Login statistics (count, last login timestamp)
- Activity timestamps (last active time)
- Usage metrics (total usage minutes, session tracking)

---

## Step 2: Core User Repository Implementation

### 2.1 Create User Repository

Create `app/repositories/user_repository.py`:

```python
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc, func
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone, timedelta
from app.db.models.user import User
from app.db.models.tenant import Tenant
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate

class UserRepository(BaseRepository[User]):
    """
    Repository for user operations with tenant isolation.
    
    Inherits from BaseRepository to get standard CRUD operations
    and adds user-specific methods for authentication, activity tracking,
    and user management within tenant boundaries.
    
    Key Features:
    - Identity provider authentication
    - Email-based lookups within tenants
    - Activity and login statistics tracking
    - User search and filtering
    - Status management
    """
    
    def __init__(self):
        """Initialize with User model."""
        super().__init__(User)
    
    # === Authentication Methods ===
    
    def get_by_email(self, db: Session, tenant_id: UUID, email: str) -> Optional[User]:
        """
        Get user by email within a specific tenant.
        
        Email addresses are unique within each tenant but may be duplicated
        across different tenants, so tenant scoping is required.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            email: User email address
            
        Returns:
            User instance or None if not found
            
        Example:
            user = user_repo.get_by_email(db, tenant_id, "user@company.com")
        """
        return db.query(User).filter(
            and_(
                User.tenant_id == tenant_id,
                User.email == email,
                User.is_deleted == False
            )
        ).first()
    
    def get_by_identity_provider_id(self, db: Session, identity_provider: str, 
                                   identity_provider_id: str) -> Optional[User]:
        """
        Get user by identity provider information.
        
        This is used for authentication and doesn't require tenant_id
        since identity provider IDs are globally unique across the system.
        This method is typically called during the authentication process
        before we know which tenant the user belongs to.
        
        Args:
            db: Database session
            identity_provider: Provider name (e.g., "entra_id", "google", "local_dev_registration")
            identity_provider_id: Unique ID from the provider
            
        Returns:
            User instance or None if not found
            
        Example:
            user = user_repo.get_by_identity_provider_id(
                db, "entra_id", "12345-abcde-67890"
            )
        """
        return db.query(User).filter(
            and_(
                User.identity_provider == identity_provider,
                User.identity_provider_id == identity_provider_id,
                User.is_deleted == False
            )
        ).first()
    
    def check_email_availability(self, db: Session, tenant_id: UUID, email: str, 
                                exclude_user_id: Optional[UUID] = None) -> bool:
        """
        Check if an email address is available within a tenant.
        
        Used during user creation and email updates to prevent conflicts.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            email: Email address to check
            exclude_user_id: User ID to exclude from check (for updates)
            
        Returns:
            True if email is available, False if taken
        """
        query = db.query(User.id).filter(
            and_(
                User.tenant_id == tenant_id,
                User.email == email,
                User.is_deleted == False
            )
        )
        
        # Exclude specific user (useful for updates)
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        
        return query.first() is None
    
    # === User Creation and Management ===
    
    def create_user_for_tenant(self, db: Session, *, obj_in: UserCreate) -> User:
        """
        Create a new user with validation.
        
        Validates email uniqueness within the tenant and sets appropriate defaults.
        The tenant_id is included in the UserCreate schema.
        
        Args:
            db: Database session
            obj_in: User creation schema (includes tenant_id)
            
        Returns:
            Created user instance
            
        Raises:
            ValueError: If email is already taken within the tenant
            
        Example:
            user_data = UserCreate(
                email="user@company.com",
                display_name="John Doe",
                identity_provider="entra_id",
                identity_provider_id="12345",
                tenant_id=tenant_id
            )
            new_user = user_repo.create_user_for_tenant(db, obj_in=user_data)
        """
        # Check email availability
        if not self.check_email_availability(db, obj_in.tenant_id, obj_in.email):
            raise ValueError(f"Email '{obj_in.email}' is already taken in this organization")
        
        # Prepare user data
        user_data = {
            "email": obj_in.email,
            "display_name": obj_in.display_name,
            "identity_provider": obj_in.identity_provider,
            "identity_provider_id": obj_in.identity_provider_id,
            "status": getattr(obj_in, 'status', 'active'),
            "login_count": 0,
            "total_usage_minutes": 0
        }
        
        return self.create(db, obj_in=user_data, tenant_id=obj_in.tenant_id)
    
    # === Basic Activity Tracking ===
    
    def update_login_stats(self, db: Session, tenant_id: UUID, user_id: UUID) -> Optional[User]:
        """
        Update user login statistics when they authenticate.
        
        Increments login count and updates last login timestamp.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            user_id: User UUID to update
            
        Returns:
            Updated user instance or None if not found
            
        Example:
            updated_user = user_repo.update_login_stats(db, tenant_id, user_id)
        """
        user = self.get_by_id(db, tenant_id, user_id)
        if user:
            user.login_count = (user.login_count or 0) + 1
            user.last_login_at = datetime.now(timezone.utc)
            user.updated_at = datetime.now(timezone.utc)
            db.add(user)
            db.flush()
            db.refresh(user)
        return user
    
    def update_activity_timestamp(self, db: Session, tenant_id: UUID, user_id: UUID) -> Optional[User]:
        """
        Update user's last activity timestamp.
        
        Called periodically during user sessions to track engagement.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            user_id: User UUID to update
            
        Returns:
            Updated user instance or None if not found
        """
        user = self.get_by_id(db, tenant_id, user_id)
        if user:
            user.last_active_at = datetime.now(timezone.utc)
            user.updated_at = datetime.now(timezone.utc)
            db.add(user)
            db.flush()
            db.refresh(user)
        return user
    
    # === Basic User Queries ===
    
    def search_users(self, db: Session, tenant_id: UUID, *, search_term: str, 
                    skip: int = 0, limit: int = 100) -> List[User]:
        """
        Search users by email or display name within a tenant.
        
        Performs case-insensitive search across email and display_name fields.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            search_term: Term to search for
            skip: Pagination offset
            limit: Maximum results to return
            
        Returns:
            List of matching users
            
        Example:
            users = user_repo.search_users(db, tenant_id, search_term="john", limit=25)
        """
        return self.search(
            db=db,
            tenant_id=tenant_id,
            search_term=search_term,
            search_fields=["email", "display_name"],
            skip=skip,
            limit=limit
        )
    
    def get_users_by_status(self, db: Session, tenant_id: UUID, status: str, 
                           *, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get users filtered by status within a tenant.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            status: User status to filter by (e.g., "active", "inactive", "suspended")
            skip: Pagination offset
            limit: Maximum results to return
            
        Returns:
            List of users with the specified status
        """
        return db.query(User).filter(
            and_(
                User.tenant_id == tenant_id,
                User.status == status,
                User.is_deleted == False
            )
        ).order_by(User.created_at.desc()).offset(skip).limit(limit).all()


# Create singleton instance for dependency injection
user_repo = UserRepository()
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
from .user_repository import UserRepository, user_repo

__all__ = ["BaseRepository", "TenantRepository", "tenant_repo", "UserRepository", "user_repo"]
```

---

## Step 3: Understanding Key Features

### 3.1 Repository Inheritance Benefits

**Automatic CRUD Operations**:
```python
# UserRepository automatically gets these from BaseRepository:
user_repo.get_by_id(db, tenant_id, user_id)        # ✅ Inherited
user_repo.get_all(db, tenant_id, skip=0, limit=50) # ✅ Inherited
user_repo.create(db, obj_in=data, tenant_id=tid)   # ✅ Inherited
user_repo.update(db, db_obj=user, obj_in=updates)  # ✅ Inherited
user_repo.soft_delete(db, tenant_id, user_id)      # ✅ Inherited

# Plus user-specific methods:
user_repo.get_by_email(db, tenant_id, email)       # ✅ User-specific
user_repo.update_login_stats(db, tenant_id, uid)   # ✅ User-specific
```

### 3.2 Identity Provider Integration

**Authentication Flow**:
```python
# Step 1: Authenticate with identity provider (external)
# Step 2: Look up user by provider info (no tenant needed yet)
user = user_repo.get_by_identity_provider_id(db, "entra_id", "12345")

# Step 3: Now we know the tenant and can do tenant-scoped operations
if user:
    tenant_id = user.tenant_id
    user_repo.update_login_stats(db, tenant_id, user.id)
```

### 3.3 Email Uniqueness Within Tenants

**Why Tenant-Scoped**:
```python
# Same email can exist in different tenants:
# Tenant A: john@company.com
# Tenant B: john@company.com  ← This is allowed

# But not within the same tenant:
# Tenant A: john@company.com
# Tenant A: john@company.com  ← This would be rejected
```

---

## Step 4: Basic Testing

### 4.1 Create Simple Test

Create `test_user_repository_basic.py` in your project root:

```python
from app.repositories.user_repository import user_repo
from app.repositories.tenant_repository import tenant_repo
from app.schemas.user import UserCreate
from app.schemas.tenant import TenantCreate
from app.db.session import SessionLocal
from uuid import uuid4
import time

def test_user_repository_basic():
    """Test basic UserRepository functionality"""
    
    db = SessionLocal()
    
    try:
        print("🧪 Testing UserRepository - Basic Functions...")
        
        # Create a test tenant with unique name to avoid conflicts
        unique_suffix = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
        tenant_data = TenantCreate(
            name=f"Test Company {unique_suffix}",
            plan_type="trial",
            status="trial"
        )
        test_tenant = tenant_repo.create(db, obj_in=tenant_data)
        print(f"✅ Created test tenant: {test_tenant.name}")
        
        # Test email availability check
        test_email = f"test{unique_suffix}@example.com"
        available = user_repo.check_email_availability(db, test_tenant.id, test_email)
        assert available == True, "Email should be available"
        print("✅ Email availability check works")
        
        # Test user creation
        user_data = UserCreate(
            email=test_email,
            display_name="Test User",
            identity_provider="local_dev_registration",
            identity_provider_id=f"test-user-{unique_suffix}",
            tenant_id=test_tenant.id  # Include tenant_id as required by schema
        )
        
        new_user = user_repo.create_user_for_tenant(db, obj_in=user_data)
        print(f"✅ Created user: {new_user.email} in tenant {test_tenant.name}")
        
        # Test email no longer available
        available = user_repo.check_email_availability(db, test_tenant.id, test_email)
        assert available == False, "Email should no longer be available"
        print("✅ Email uniqueness enforcement works")
        
        # Test get by email
        found_user = user_repo.get_by_email(db, test_tenant.id, test_email)
        assert found_user is not None, "Should find user by email"
        assert found_user.id == new_user.id, "Should be the same user"
        print("✅ Get by email works")
        
        # Test get by identity provider
        found_user = user_repo.get_by_identity_provider_id(
            db, "local_dev_registration", f"test-user-{unique_suffix}"
        )
        assert found_user is not None, "Should find user by identity provider"
        assert found_user.id == new_user.id, "Should be the same user"
        print("✅ Identity provider lookup works")
        
        # Test login stats update
        original_count = new_user.login_count or 0
        updated_user = user_repo.update_login_stats(db, test_tenant.id, new_user.id)
        assert updated_user.login_count == original_count + 1, "Login count should increment"
        assert updated_user.last_login_at is not None, "Last login should be set"
        print("✅ Login stats update works")
        
        # Test user search
        search_results = user_repo.search_users(db, test_tenant.id, search_term="test", limit=10)
        assert len(search_results) >= 1, "Should find user in search"
        print("✅ User search works")
        
        # Clean up
        user_repo.soft_delete(db, test_tenant.id, new_user.id)
        tenant_repo.soft_delete(db, test_tenant.id, test_tenant.id)
        db.commit()
        print("✅ Cleaned up test data")
        
        print("\n🎉 UserRepository basic tests passed!")
        
    except Exception as e:
        print(f"❌ UserRepository test failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_user_repository_basic()
```

### 4.2 Run the Test

```bash
# Navigate to your project directory
cd C:\_source\Greenshoes\Summer2025Internship\Sprint2\Guided_Walkthrough\quodsi_api

# Activate virtual environment
.\venv\Scripts\activate

# Run the test
python test_user_repository_basic.py
```

---

## Common Issues and Solutions

### Issue 1: UserCreate Schema Alignment
**Problem**: `'UserCreate' object has no attribute 'tenant_id'` or validation errors about missing tenant_id
**Root Cause**: The `UserCreate` schema requires `tenant_id` as a field, but the repository method was designed to accept it as a separate parameter
**Solution**: Include `tenant_id` in the `UserCreate` schema and update the repository method to use `obj_in.tenant_id`

```python
# ❌ Old pattern - tenant_id as separate parameter:
user_data = UserCreate(
    email="user@company.com",
    display_name="John Doe",
    identity_provider="entra_id",
    identity_provider_id="12345"
)
new_user = user_repo.create_user_for_tenant(db, obj_in=user_data, tenant_id=tenant_id)

# ✅ New pattern - tenant_id included in schema:
user_data = UserCreate(
    email="user@company.com",
    display_name="John Doe",
    identity_provider="entra_id",
    identity_provider_id="12345",
    tenant_id=tenant_id  # Include in schema
)
new_user = user_repo.create_user_for_tenant(db, obj_in=user_data)  # No separate tenant_id
```

### Issue 2: Email Uniqueness Across Tenants
**Problem**: Confusion about email uniqueness scope
**Solution**: Emails are unique within each tenant, not globally

### Issue 3: Identity Provider vs Email Lookup
**Problem**: When to use which lookup method
**Solution**: 
- Use `get_by_identity_provider_id()` for authentication (global)
- Use `get_by_email()` for tenant-scoped user management

### Issue 4: Missing Required Fields
**Problem**: UserCreate schema missing required fields
**Solution**: Ensure your UserCreate schema includes all required fields

---

## Verification Checklist

After completing this step, verify:

- [ ] `app/repositories/user_repository.py` exists with core implementation
- [ ] UserRepository inherits from BaseRepository[User]
- [ ] Identity provider authentication methods work
- [ ] Email-based lookups are tenant-scoped
- [ ] User creation validates email uniqueness within tenants
- [ ] Basic activity tracking methods work
- [ ] Basic test script runs without errors
- [ ] Repository is exported in `__init__.py`

## Next Steps

Continue with **063a_User_Repository_Advanced_Features.md** for:
- Advanced analytics and statistics methods
- Usage tracking and engagement metrics
- Tenant-level user summaries
- Recently active user queries
- Comprehensive testing suite
- User-tenant relationship setup

## Key Takeaways

1. **Repository inheritance** provides code reuse while maintaining type safety
2. **Identity provider integration** requires both global and tenant-scoped lookups
3. **Email uniqueness** is enforced within tenant boundaries, not globally
4. **Basic activity tracking** is essential for authentication flows
5. **Validation methods** prevent data conflicts and ensure consistency
