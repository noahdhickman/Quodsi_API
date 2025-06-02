# Module 5: User Model and Migration

## Learning Objectives
By the end of this module, you will:
- Implement the User SQLAlchemy model with multi-tenant BaseEntity inheritance
- Create comprehensive User Pydantic schemas for API validation
- Generate and run the User migration with proper foreign key relationships
- Validate the database schema and relationships
- Understand user-tenant data consistency patterns

## Prerequisites
- Completed Module 4 (Tenant Model and Migration)
- Working database with `tenants` table
- Understanding of foreign key relationships
- BaseEntity pattern knowledge

## Overview
The User model represents individual users within the Quodsi platform. Each user belongs to exactly one tenant, establishing the foundation for multi-tenant data isolation. The User model inherits from BaseEntity, providing standard fields like `id`, `index_id`, `tenant_id`, timestamps, and soft delete functionality.

## Step 1: Create User SQLAlchemy Model

### 1.1 Create the User Model File
Create `app/db/models/user.py`:

```python
# app/db/models/user.py
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from app.db.models.base_entity import BaseEntity
from datetime import datetime


class User(BaseEntity):
    """
    User model representing individual users within tenants.
    
    Each user belongs to exactly one tenant, establishing the foundation
    for multi-tenant data isolation. Users authenticate through various
    identity providers and maintain session and usage statistics.
    """
    __tablename__ = "users"
    
    # Identity and authentication fields
    identity_provider = Column(String(50), nullable=False, comment="Provider type ('entra_id', 'google', etc.)")
    identity_provider_id = Column(String(255), nullable=False, comment="Unique identifier from the provider")
    email = Column(String(255), nullable=False, comment="User's email address")
    display_name = Column(String(255), nullable=False, comment="User's display name")
    
    # Session and activity tracking
    last_login_at = Column(DateTime, nullable=True, comment="Most recent login timestamp")
    login_count = Column(Integer, nullable=False, default=0, comment="Count of user logins")
    total_usage_minutes = Column(Integer, nullable=False, default=0, comment="Cumulative time spent using Quodsi")
    last_session_start = Column(DateTime, nullable=True, comment="When current/last session started")
    last_active_at = Column(DateTime, nullable=True, comment="Last user activity timestamp")
    
    # Account status and metadata
    status = Column(String(20), nullable=False, default='active', comment="User status (active, invited, suspended)")
    user_metadata = Column(String(4000), nullable=True, comment="Additional profile information (JSON data)")
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    
    # Additional indexes for user-specific queries
    @declared_attr
    def __table_args__(cls):
        """Define indexes and constraints specific to users table"""
        base_args = super().__table_args__
        user_args = (
            # Unique email per tenant
            UniqueConstraint('tenant_id', 'email', name='uq_users_tenant_email'),
            
            # Identity provider lookup (global uniqueness across tenants)
            UniqueConstraint('identity_provider', 'identity_provider_id', name='uq_users_identity_provider'),
        )
        return base_args + user_args
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, tenant_id={self.tenant_id})>"
    
    def update_login_stats(self):
        """Update login statistics when user signs in"""
        self.login_count += 1
        self.last_login_at = datetime.utcnow()
        self.last_active_at = datetime.utcnow()
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_active_at = datetime.utcnow()
```

### 1.2 Update Tenant Model for Relationship
Modify `app/db/models/tenant.py` to add the users relationship:

```python
# Add this import at the top if not already there
from sqlalchemy.orm import relationship

# Add this relationship inside the Tenant class
class Tenant(BaseEntity):
    # ... existing fields ...
    
    # Relationships
    users = relationship("User", back_populates="tenant")
    
    # ... rest of the class ...
```

### 1.3 Update Models __init__.py
Update `app/db/models/__init__.py` to include the User model:

```python
# app/db/models/__init__.py
from .base_entity import BaseEntity
from .tenant import Tenant
from .user import User

__all__ = ["Tenant", "User"]
```

## Troubleshooting Common Issues

### Issue 1: SQLAlchemy "metadata" Reserved Attribute Error
**Error**: `Attribute name 'metadata' is reserved when using the Declarative API`

**Solution**: The field name `metadata` conflicts with SQLAlchemy's internal metadata attribute. Rename it to `user_metadata`:
```python
# Instead of:
metadata = Column(String(4000), nullable=True, comment="Additional profile information (JSON data)")

# Use:
user_metadata = Column(String(4000), nullable=True, comment="Additional profile information (JSON data)")
```

### Issue 2: BaseEntity __table_args__ Access Error
**Error**: Issues with accessing BaseEntity's `__table_args__` method

**Solution**: Use `super().__table_args__` instead of `BaseEntity.__table_args__.fget(cls)`:
```python
@declared_attr
def __table_args__(cls):
    base_args = super().__table_args__  # Correct approach
    # ... rest of method
```

### Issue 3: BaseEntity Import Issues with Alembic
**Error**: Alembic treating BaseEntity as a concrete model

**Solution**: Remove BaseEntity from the `__all__` list in models `__init__.py` since it's an abstract base class:
```python
# Only export concrete models
__all__ = ["Tenant", "User"]
```

