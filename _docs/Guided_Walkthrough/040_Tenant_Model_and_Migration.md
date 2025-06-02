# Module 4: Tenant Model & Migration

**Duration:** 30-45 minutes  
**Objective:** Create the Tenant SQLAlchemy model, Pydantic schemas, and first real Alembic migration to establish the foundation table for multi-tenancy.

**Prerequisites:** Module 3 completed - BaseEntity implemented and tested

---

## Understanding the Tenant Model

### What is a Tenant?
In Quodsi's multi-tenant architecture, a Tenant represents:
- A customer organization (company, team, or individual)
- The top-level container for data isolation
- Subscription and billing context
- The foundation that all other entities reference

### Tenant Properties
- **Identity**: Name, subdomain, slug for URL-friendly access
- **Plan**: Trial, starter, professional, enterprise
- **Limits**: Maximum users, models, scenarios per month
- **Status**: Trial, active, suspended, cancelled
- **Billing**: Stripe integration fields for payments

---

## Step 1: Create Tenant SQLAlchemy Model

### 1.1 Implement Tenant Model
Create `app/db/models/tenant.py`:

```python
"""
Tenant model - represents a customer organization in the multi-tenant system.

Each tenant is isolated and contains:
- Users, models, analyses, scenarios
- Subscription and billing information  
- Usage limits and current consumption
- Settings and configuration
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, DECIMAL, UniqueConstraint
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from app.db.models.base_entity import BaseEntity

class Tenant(BaseEntity):
    __tablename__ = "tenants"

    # tenant_id is handled by @declared_attr in BaseEntity 
    # For tenants table, it's nullable (for system tenants or special cases)

    # Basic Identity
    name = Column(
        String(255), 
        nullable=False,
        comment="Display name of the tenant organization"
    )
    
    subdomain = Column(
        String(100), 
        nullable=False,
        comment="Unique subdomain for tenant (e.g., 'acme' in acme.quodsi.com)"
    )
    
    slug = Column(
        String(100), 
        nullable=False,
        comment="URL-friendly identifier for tenant (e.g., 'acme-corp')"
    )

    # Subscription Information
    plan_type = Column(
        String(50), 
        nullable=False, 
        default='trial',
        comment="Subscription plan: trial, starter, professional, enterprise"
    )
    
    status = Column(
        String(20), 
        nullable=False, 
        default='trial',
        comment="Tenant status: trial, active, suspended, cancelled, deleted"
    )

    # Usage Limits (based on subscription plan)
    max_users = Column(
        Integer, 
        nullable=False, 
        default=5,
        comment="Maximum number of users allowed"
    )
    
    max_models = Column(
        Integer, 
        nullable=False, 
        default=10,
        comment="Maximum number of models allowed"
    )
    
    max_scenarios_per_month = Column(
        Integer, 
        nullable=False, 
        default=100,
        comment="Maximum scenarios that can be run per month"
    )
    
    max_storage_gb = Column(
        DECIMAL(10, 2), 
        nullable=False, 
        default=1.0,
        comment="Maximum storage allowed in GB"
    )

    # Lifecycle Timestamps
    trial_expires_at = Column(
        DateTime, 
        nullable=True,
        comment="When trial period expires (null for paid plans)"
    )
    
    activated_at = Column(
        DateTime, 
        nullable=True,
        comment="When tenant was activated (upgraded from trial)"
    )

    # Billing Integration (Stripe)
    stripe_customer_id = Column(
        String(255), 
        nullable=True,
        comment="Stripe customer ID for billing integration"
    )
    
    billing_email = Column(
        String(255), 
        nullable=True,
        comment="Primary email for billing communications"
    )

    # Database constraints
    __table_args__ = (
        # Unique constraints for tenant identification
        UniqueConstraint('subdomain', name='uq_tenants_subdomain'),
        UniqueConstraint('slug', name='uq_tenants_slug'),
        
        # BaseEntity indexes are added automatically via @declared_attr
        # Additional tenant-specific indexes can be added here if needed
    )

    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}', subdomain='{self.subdomain}', status='{self.status}')>"

    @property
    def is_trial(self) -> bool:
        """Check if tenant is on trial plan"""
        return self.plan_type == 'trial' or self.status == 'trial'

    @property
    def is_active(self) -> bool:
        """Check if tenant is active and can use the platform"""
        return self.status == 'active' and not self.is_deleted

    @property
    def full_domain(self) -> str:
        """Get full domain for this tenant (e.g., acme.quodsi.com)"""
        return f"{self.subdomain}.quodsi.com"

    def can_add_user(self, current_user_count: int) -> bool:
        """Check if tenant can add another user"""
        return current_user_count < self.max_users

    def can_create_model(self, current_model_count: int) -> bool:
        """Check if tenant can create another model"""
        return current_model_count < self.max_models

    def can_run_scenario(self, scenarios_this_month: int) -> bool:
        """Check if tenant can run another scenario this month"""
        return scenarios_this_month < self.max_scenarios_per_month
```

### 1.2 Update Models Package
Update `app/db/models/__init__.py`:

```python
"""
Database models package.

All models inherit from BaseEntity which provides multi-tenant architecture,
performance optimization, audit fields, and consistent patterns.
"""

from .base_entity import BaseEntity
from .tenant import Tenant

__all__ = ["BaseEntity", "Tenant"]
```
