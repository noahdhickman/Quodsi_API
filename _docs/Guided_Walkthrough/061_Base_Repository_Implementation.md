# Step 6.1: Base Repository Implementation

## Overview

The **BaseRepository** is the foundation of our data access layer. It provides generic CRUD (Create, Read, Update, Delete) operations with built-in tenant isolation for all entities that inherit from `BaseEntity`.

This implementation ensures that all database operations are automatically scoped to the correct tenant, preventing accidental cross-tenant data access - a critical security requirement for multi-tenant SaaS applications.

**What we'll implement:**
- Generic repository class using Python generics
- Tenant-scoped CRUD operations
- Search and pagination functionality
- Soft delete support
- Performance-optimized queries
- Consistent error handling patterns

**Key Benefits:**
- ✅ **Multi-Tenant Safety**: All operations automatically enforce tenant isolation
- ✅ **Code Reuse**: Single implementation serves all entities
- ✅ **Consistency**: Standardized patterns across all data operations
- ✅ **Performance**: Optimized queries with proper indexing utilization
- ✅ **Testability**: Clean interface for mocking in unit tests

---

## Step 1: Understanding the Generic Repository Pattern

### 1.1 Why Use Generics?

Python's `Generic` and `TypeVar` allow us to create a single repository class that works with any SQLAlchemy model while maintaining type safety:

```python
# Instead of creating separate repositories for each model...
class UserRepository:
    def get_by_id(self, db: Session, tenant_id: UUID, id: UUID) -> Optional[User]:
        # User-specific implementation

class OrganizationRepository:
    def get_by_id(self, db: Session, tenant_id: UUID, id: UUID) -> Optional[Organization]:
        # Organization-specific implementation

# We create one generic repository that works for all models
class BaseRepository(Generic[ModelType]):
    def get_by_id(self, db: Session, tenant_id: UUID, id: UUID) -> Optional[ModelType]:
        # Generic implementation that works for any model
```

### 1.2 Tenant Isolation Strategy

Every operation in our BaseRepository automatically includes tenant filtering:

```python
# All queries include these filters automatically:
- model.tenant_id == tenant_id    # Tenant isolation
- model.is_deleted == False       # Exclude soft-deleted records
```

This ensures that users can never accidentally access data from other tenants, even if they somehow obtain another tenant's record IDs.

---

## Step 2: Create the Base Repository

### 2.1 Create Base Repository File

Create the file `app/repositories/base.py`:

```python
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from uuid import UUID
from app.db.models.base_entity import BaseEntity

# Generic type for SQLAlchemy models that inherit from BaseEntity
ModelType = TypeVar("ModelType", bound=BaseEntity)

class BaseRepository(Generic[ModelType]):
    """
    Base repository providing tenant-scoped CRUD operations.
    
    This generic repository automatically enforces tenant isolation
    for all database operations, ensuring multi-tenant data security.
    
    Type Parameters:
        ModelType: SQLAlchemy model class that inherits from BaseEntity
    
    Usage:
        class UserRepository(BaseRepository[User]):
            def __init__(self):
                super().__init__(User)
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        Initialize repository with a specific model type.
        
        Args:
            model: SQLAlchemy model class that inherits from BaseEntity
        """
        self.model = model
    
    def get_by_id(self, db: Session, tenant_id: UUID, id: UUID) -> Optional[ModelType]:
        """
        Get a single entity by UUID, scoped to tenant.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            id: Entity UUID to retrieve
            
        Returns:
            Entity instance or None if not found
            
        Example:
            user = user_repo.get_by_id(db, tenant_id, user_id)
        """
        return db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.id == id,
                self.model.is_deleted == False
            )
        ).first()
    
    def get_by_index_id(self, db: Session, tenant_id: UUID, index_id: int) -> Optional[ModelType]:
        """
        Get a single entity by index_id (clustered primary key), scoped to tenant.
        
        This is often more performant than UUID lookups due to clustered indexing.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            index_id: Entity index_id (auto-increment integer)
            
        Returns:
            Entity instance or None if not found
        """
        return db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.index_id == index_id,
                self.model.is_deleted == False
            )
        ).first()
    
    def get_all(self, db: Session, tenant_id: UUID, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get all entities for a tenant with pagination.
        
        Results are ordered by index_id (creation order) for consistent pagination.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            skip: Number of records to skip (pagination offset)
            limit: Maximum number of records to return
            
        Returns:
            List of entity instances
            
        Example:
            users = user_repo.get_all(db, tenant_id, skip=0, limit=50)
        """
        return db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.is_deleted == False
            )
        ).order_by(self.model.index_id).offset(skip).limit(limit).all()
    
    def count(self, db: Session, tenant_id: UUID) -> int:
        """
        Count all non-deleted entities for a tenant.
        
        Useful for pagination metadata and analytics.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            
        Returns:
            Number of entities
        """
        return db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.is_deleted == False
            )
        ).count()
    
    def create(self, db: Session, *, obj_in: Dict[str, Any], tenant_id: UUID) -> ModelType:
        """
        Create a new entity with automatic tenant assignment.
        
        The tenant_id is automatically set and cannot be overridden for security.
        Uses flush() instead of commit() to allow service-level transaction management.
        
        Args:
            db: Database session
            obj_in: Dictionary of field values for the new entity
            tenant_id: Tenant UUID (automatically assigned)
            
        Returns:
            Created entity instance
            
        Example:
            user_data = {"email": "user@example.com", "display_name": "User"}
            new_user = user_repo.create(db, obj_in=user_data, tenant_id=tenant_id)
        """
        # Ensure tenant_id is set and cannot be overridden
        obj_in = obj_in.copy()  # Don't mutate the original dict
        obj_in["tenant_id"] = tenant_id
        
        # Create the entity instance
        db_obj = self.model(**obj_in)
        
        # Add to session and flush to get the generated ID
        db.add(db_obj)
        db.flush()  # Flush to database without committing transaction
        db.refresh(db_obj)  # Refresh to get auto-generated fields
        
        return db_obj
    
    def update(self, db: Session, *, db_obj: ModelType, obj_in: Dict[str, Any]) -> ModelType:
        """
        Update an existing entity with new data.
        
        Automatically updates the updated_at timestamp and prevents
        modification of protected fields like id and tenant_id.
        
        Args:
            db: Database session
            db_obj: Existing entity instance to update
            obj_in: Dictionary of field values to update
            
        Returns:
            Updated entity instance
            
        Example:
            updated_user = user_repo.update(
                db, db_obj=user, obj_in={"display_name": "New Name"}
            )
        """
        from datetime import datetime, timezone
        
        # Update fields (excluding protected fields)
        protected_fields = {"id", "tenant_id", "index_id", "created_at"}
        
        for field, value in obj_in.items():
            if field not in protected_fields and hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        # Automatically update the timestamp
        db_obj.updated_at = datetime.now(timezone.utc)
        
        # Save changes
        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        
        return db_obj
    
    def soft_delete(self, db: Session, tenant_id: UUID, id: UUID) -> bool:
        """
        Soft delete an entity by setting is_deleted=True.
        
        Soft deletes preserve data for audit trails and potential recovery
        while removing entities from normal query results.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            id: Entity UUID to delete
            
        Returns:
            True if entity was found and deleted, False otherwise
            
        Example:
            deleted = user_repo.soft_delete(db, tenant_id, user_id)
        """
        from datetime import datetime, timezone
        
        db_obj = self.get_by_id(db, tenant_id, id)
        if db_obj:
            db_obj.is_deleted = True
            db_obj.updated_at = datetime.now(timezone.utc)
            db.add(db_obj)
            db.flush()
            return True
        return False
    
    def hard_delete(self, db: Session, tenant_id: UUID, id: UUID) -> bool:
        """
        Permanently delete an entity from the database.
        
        ⚠️  WARNING: This permanently removes data. Use with extreme caution.
        Typically only used for GDPR compliance or data cleanup operations.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            id: Entity UUID to delete
            
        Returns:
            True if entity was found and deleted, False otherwise
        """
        db_obj = self.get_by_id(db, tenant_id, id)
        if db_obj:
            db.delete(db_obj)
            db.flush()
            return True
        return False
    
    def search(self, db: Session, tenant_id: UUID, *, search_term: str, 
               search_fields: List[str], skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Search entities by term across specified fields.
        
        Performs case-insensitive LIKE searches across multiple fields
        using OR conditions (matches any field).
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            search_term: Term to search for
            search_fields: List of model field names to search in
            skip: Pagination offset
            limit: Maximum results to return
            
        Returns:
            List of matching entities
            
        Example:
            users = user_repo.search(
                db, tenant_id, 
                search_term="john", 
                search_fields=["email", "display_name"],
                limit=25
            )
        """
        # Handle empty search term
        if not search_term.strip():
            return self.get_all(db, tenant_id, skip=skip, limit=limit)
        
        # Build search conditions for each field
        search_conditions = []
        for field_name in search_fields:
            if hasattr(self.model, field_name):
                field_attr = getattr(self.model, field_name)
                # Use ilike for case-insensitive search
                search_conditions.append(field_attr.ilike(f"%{search_term}%"))
        
        # Return empty list if no valid fields found
        if not search_conditions:
            return []
        
        # Execute search query
        return db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.is_deleted == False,
                or_(*search_conditions)  # Match any of the search conditions
            )
        ).order_by(self.model.index_id).offset(skip).limit(limit).all()
    
    def get_recent(self, db: Session, tenant_id: UUID, *, days: int = 7, limit: int = 100) -> List[ModelType]:
        """
        Get recently created entities within the specified number of days.
        
        Useful for activity feeds, recent items lists, and analytics.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            days: Number of days back to search (default: 7)
            limit: Maximum results to return
            
        Returns:
            List of recent entities ordered by creation date (newest first)
        """
        from datetime import datetime, timezone, timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        return db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.is_deleted == False,
                self.model.created_at >= cutoff_date
            )
        ).order_by(self.model.created_at.desc()).limit(limit).all()
    
    def exists(self, db: Session, tenant_id: UUID, id: UUID) -> bool:
        """
        Check if an entity exists without loading the full object.
        
        More efficient than get_by_id() when you only need to verify existence.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            id: Entity UUID to check
            
        Returns:
            True if entity exists, False otherwise
        """
        return db.query(self.model.id).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.id == id,
                self.model.is_deleted == False
            )
        ).first() is not None
```

### 2.2 Create Repository Package Init File

Create `app/repositories/__init__.py`:

```python
"""
Repository layer for data access operations.

This package contains repositories that provide clean interfaces
for database operations with built-in tenant isolation and
consistent CRUD patterns.
"""

from .base import BaseRepository

__all__ = ["BaseRepository"]
```

---

## Step 3: Understanding the Implementation

### 3.1 Key Design Decisions

**Generic Type Safety**
```python
ModelType = TypeVar("ModelType", bound=BaseEntity)
class BaseRepository(Generic[ModelType]):
```
- Ensures type safety while allowing reuse across different models
- IDE autocompletion and type checking work correctly
- Prevents runtime type errors

**Automatic Tenant Isolation**
```python
and_(
    self.model.tenant_id == tenant_id,
    self.model.id == id,
    self.model.is_deleted == False
)
```
- Every query automatically includes tenant_id filtering
- Impossible to accidentally access cross-tenant data
- Soft-deleted records are excluded by default

**Transaction Management**
```python
db.flush()  # Write to database without committing
db.refresh(db_obj)  # Reload from database
```
- Uses `flush()` instead of `commit()` to allow service-level transaction control
- Services coordinate multiple repository operations in single transactions

### 3.2 Performance Considerations

**Clustered Index Optimization**
```python
.order_by(self.model.index_id)  # Use clustered index for sorting
```
- Results are ordered by `index_id` (clustered primary key) for optimal performance
- More efficient than ordering by UUID fields

**Query Optimization**
```python
.filter(and_(...))  # Explicit AND conditions for query planner
```
- Uses explicit AND conditions to help SQL Server's query optimizer
- Leverages multi-column indexes effectively

**Efficient Existence Checks**
```python
db.query(self.model.id).filter(...).first() is not None
```
- Only selects the ID field instead of loading entire records
- Faster than loading full objects just to check existence

---

## Step 4: Testing the Base Repository

### 4.1 Create a Simple Test

Create `test_base_repository.py` in your project root to verify the implementation:

```python
from app.repositories.base import BaseRepository
from app.db.models.user import User
from app.db.session import SessionLocal, get_db
from uuid import uuid4

def test_base_repository():
    """Simple test to verify BaseRepository functionality"""
    
    # Create a User repository using BaseRepository
    user_repo = BaseRepository(User)
    db = SessionLocal()
    
    try:
        # Test that we can instantiate the repository
        print("✅ BaseRepository instantiated successfully")
        
        # Test that methods exist and have correct signatures
        tenant_id = uuid4()
        user_id = uuid4()
        
        # These should not raise AttributeError
        result = user_repo.get_by_id(db, tenant_id, user_id)
        print("✅ get_by_id method works (returned None as expected)")
        
        count = user_repo.count(db, tenant_id)
        print(f"✅ count method works (returned {count})")
        
        users = user_repo.get_all(db, tenant_id, limit=10)
        print(f"✅ get_all method works (returned {len(users)} users)")
        
        print("\n🎉 BaseRepository implementation is working correctly!")
        
    except Exception as e:
        print(f"❌ BaseRepository test failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_base_repository()
```

### 4.2 Run the Test

```bash
# Navigate to your project directory
cd C:\_source\Greenshoes\Summer2025Internship\Sprint2\Guided_Walkthrough\quodsi_api

# Activate virtual environment
.\venv\Scripts\activate

# Run the test
python test_base_repository.py
```

Expected output:
```
✅ BaseRepository instantiated successfully
✅ get_by_id method works (returned None as expected)
✅ count method works (returned 0)
✅ get_all method works (returned 0 users)

🎉 BaseRepository implementation is working correctly!
```

---

## Step 5: Usage Patterns

### 5.1 Creating Specialized Repositories

```python
# Example: UserRepository inheriting from BaseRepository
from app.repositories.base import BaseRepository
from app.db.models.user import User

class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)
    
    # Add user-specific methods
    def get_by_email(self, db: Session, tenant_id: UUID, email: str) -> Optional[User]:
        return db.query(User).filter(
            and_(
                User.tenant_id == tenant_id,
                User.email == email,
                User.is_deleted == False
            )
        ).first()
```

### 5.2 Service Layer Integration

```python
# Example: Service using repository
class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository()
    
    def create_user(self, tenant_id: UUID, user_data: dict) -> User:
        try:
            # Use repository for data access
            new_user = self.user_repo.create(
                self.db, 
                obj_in=user_data, 
                tenant_id=tenant_id
            )
            # Service handles the commit
            self.db.commit()
            return new_user
        except Exception:
            # Service handles rollback
            self.db.rollback()
            raise
```

---

## Common Issues and Solutions

### Issue 1: Type Hints Not Working
**Problem**: IDE doesn't recognize the return types
**Solution**: Ensure proper import of `Generic` and `TypeVar`

### Issue 2: Tenant ID Bypass Attempts
**Problem**: Trying to query without tenant_id
**Solution**: All BaseRepository methods require tenant_id - this is by design

### Issue 3: Transaction Management Confusion
**Problem**: When to use flush() vs commit()
**Solution**: 
- Repositories use `flush()` (write without committing)
- Services use `commit()` and `rollback()` (transaction boundaries)

### Issue 4: Search Performance
**Problem**: Search queries are slow
**Solution**: Ensure appropriate indexes exist on searchable fields

---

## Verification Checklist

After completing this step, verify:

- [ ] `app/repositories/base.py` exists with complete BaseRepository implementation
- [ ] `app/repositories/__init__.py` exports BaseRepository
- [ ] Test script runs without errors
- [ ] All methods include tenant_id parameter (except hard_delete)
- [ ] All queries include tenant isolation filters
- [ ] Methods use flush() instead of commit()
- [ ] Type hints work correctly in your IDE
- [ ] Search functionality handles empty terms gracefully
- [ ] Soft delete updates updated_at timestamp

## Next Steps

With the BaseRepository implemented, you now have:

1. **Generic CRUD Operations** - Reusable across all entities
2. **Automatic Tenant Isolation** - Security built into every query
3. **Performance Optimization** - Efficient queries and indexing
4. **Consistent Patterns** - Standardized approach to data access
5. **Transaction Safety** - Proper flush/commit separation

In **062_Tenant_Repository_Implementation.md**, we'll create the TenantRepository that handles the special case of tenant operations (which don't have a parent tenant_id constraint).

## Key Takeaways

1. **Generic repositories** provide code reuse while maintaining type safety
2. **Tenant isolation** must be automatic and impossible to bypass
3. **Transaction management** separation between repositories (flush) and services (commit)
4. **Performance considerations** matter - use clustered indexes and efficient queries
5. **Error handling** should be consistent and predictable
6. **Testing** validates both functionality and security constraints
