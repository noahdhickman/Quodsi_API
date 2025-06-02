# User Organization Management Database Schema (Multi-Tenant with BaseEntity)

This document outlines the organization management database schema for Quodsi's user management system. These tables provide B2B organizational structure that builds upon the core user management foundation.

**Prerequisites**: This schema depends on the tables defined in `000_User_Core_Management_Tables.md`.

**BaseEntity Standard Fields**:
Each table includes the following fields from `BaseEntity` (see `000_User_Core_Management_Tables.md` for details):
* `id`, `index_id`, `tenant_id`, `created_at`, `updated_at`, `is_deleted`

## Implementation Priority

These tables should be implemented **after** the core user management tables:

1. **`organizations`** - Customer organizations for B2B subscriptions
2. **`organization_memberships`** - Links users to organizations with roles

## Organization Management Tables

### `organizations`
Represents customer organizations for B2B subscriptions.

| Column                 | Type              | Constraints                               | Description                                       |
| :--------------------- | :---------------- | :---------------------------------------- | :------------------------------------------------ |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Organization identifier (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant owning this organization (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Creation timestamp (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `name`                 | VARCHAR(255)      | NOT NULL                                  | Organization name                                 |
| `domain`               | VARCHAR(255)      | NULL                                      | Primary email domain                              |
| `billing_email`        | VARCHAR(255)      | NULL                                      | Billing contact email                             |
| `billing_address`      | NVARCHAR(MAX)     | NULL                                      | Billing address details                           |
| `stripe_customer_id`   | VARCHAR(255)      | NULL                                      | Stripe customer identifier                        |
| `metadata`             | NVARCHAR(MAX)     | NULL                                      | Additional org information (JSON data)            |

**Indexes:**
* `ix_organizations_index_id` CLUSTERED on `index_id`
* `ix_organizations_id` UNIQUE NONCLUSTERED on `id`
* `ix_organizations_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_organizations_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_organizations_tenant_name` UNIQUE NONCLUSTERED on (`tenant_id`, `name`) WHERE `is_deleted` = 0
* `ix_organizations_tenant_domain` NONCLUSTERED on (`tenant_id`, `domain`) WHERE `domain` IS NOT NULL AND `is_deleted` = 0
* `ix_organizations_stripe_customer_id` NONCLUSTERED on (`stripe_customer_id`) WHERE `stripe_customer_id` IS NOT NULL

**Constraints:**
* `fk_organizations_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `ck_organizations_domain_format` CHECK (`domain` IS NULL OR `domain` LIKE '%.%')

### `organization_memberships`
Links users to organizations with roles.

| Column                 | Type              | Constraints                               | Description                                        |
| :--------------------- | :---------------- | :---------------------------------------- | :------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Membership identifier (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context of membership (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *When user was added/invited (BaseEntity `created_at`)*|
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `organization_id`      | UNIQUEIDENTIFIER  | NOT NULL, FK to `organizations.id`        | Reference to organization                          |
| `user_id`              | UNIQUEIDENTIFIER  | NOT NULL, FK to `users.id`                | Reference to user                                  |
| `role`                 | VARCHAR(50)       | NOT NULL, DEFAULT 'member'                | Role (owner, admin, manager, member, readonly)    |
| `invited_by_user_id`   | UNIQUEIDENTIFIER  | NULL, FK to `users.id`                    | User who sent invitation                           |
| `status`               | VARCHAR(20)       | NOT NULL, DEFAULT 'active'                | Status (active, invited, suspended)                |
| `last_active_at`       | DATETIME2         | NULL                                      | Last activity in this organization                 |

**Indexes:**
* `ix_organization_memberships_index_id` CLUSTERED on `index_id`
* `ix_organization_memberships_id` UNIQUE NONCLUSTERED on `id`
* `ix_organization_memberships_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_organization_memberships_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_organization_memberships_tenant_org_user` NONCLUSTERED on (`tenant_id`, `organization_id`, `user_id`) WHERE `is_deleted` = 0
* `ix_organization_memberships_tenant_user_role` NONCLUSTERED on (`tenant_id`, `user_id`, `role`) WHERE `is_deleted` = 0 AND `status` = 'active'
* `uq_organization_memberships_tenant_org_user` UNIQUE NONCLUSTERED on (`tenant_id`, `organization_id`, `user_id`) WHERE `is_deleted` = 0 AND `status` <> 'invited'

**Constraints:**
* `fk_organization_memberships_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_organization_memberships_organization` FOREIGN KEY (`organization_id`) REFERENCES `organizations`(`id`)
* `fk_organization_memberships_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
* `fk_organization_memberships_invited_by` FOREIGN KEY (`invited_by_user_id`) REFERENCES `users`(`id`)
* `ck_organization_memberships_role` CHECK (`role` IN ('owner', 'admin', 'manager', 'member', 'readonly'))
* `ck_organization_memberships_status` CHECK (`status` IN ('active', 'invited', 'suspended'))
* `ck_orgmembers_tenant_consistency` CHECK (
    `tenant_id` = (SELECT `tenant_id` FROM `users` WHERE `id` = `user_id`) AND
    `tenant_id` = (SELECT `tenant_id` FROM `organizations` WHERE `id` = `organization_id`)
)

## Role-Based Access Control

### Organization Roles (in order of privilege)
1. **owner** - Full control, can delete organization, manage billing
2. **admin** - Can manage users, teams, and most settings
3. **manager** - Can manage teams and team members
4. **member** - Standard user with access to organization resources
5. **readonly** - View-only access to organization resources

## Repository Pattern Examples

```python
# app/repositories/organization_repository.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.db.models.organizations import Organization, OrganizationMembership
from app.repositories.base_repository import BaseRepository

class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self, db: Session):
        super().__init__(db, Organization)
    
    def get_user_organizations(self, tenant_id: UUID, user_id: UUID) -> List[Organization]:
        """Get all organizations for a user within tenant"""
        return self.db.query(Organization).join(OrganizationMembership).filter(
            Organization.tenant_id == tenant_id,
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.status == 'active',
            Organization.is_deleted == False,
            OrganizationMembership.is_deleted == False
        ).all()
    
    def get_user_role_in_organization(self, tenant_id: UUID, user_id: UUID, org_id: UUID) -> Optional[str]:
        """Get user's role in specific organization"""
        membership = self.db.query(OrganizationMembership).filter(
            OrganizationMembership.tenant_id == tenant_id,
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.status == 'active',
            OrganizationMembership.is_deleted == False
        ).first()
        return membership.role if membership else None
    
    def user_can_manage_organization(self, tenant_id: UUID, user_id: UUID, org_id: UUID) -> bool:
        """Check if user can manage organization"""
        role = self.get_user_role_in_organization(tenant_id, user_id, org_id)
        return role in ['owner', 'admin', 'manager']
    
    def get_organization_members(self, tenant_id: UUID, org_id: UUID) -> List[dict]:
        """Get all members of an organization with their roles"""
        memberships = self.db.query(OrganizationMembership).filter(
            OrganizationMembership.tenant_id == tenant_id,
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.status == 'active',
            OrganizationMembership.is_deleted == False
        ).all()
        
        return [
            {
                'user': membership.user,
                'role': membership.role,
                'joined_at': membership.created_at,
                'last_active': membership.last_active_at
            }
            for membership in memberships
        ]
```

## Query Patterns and Best Practices

### Organization Access Patterns
```python
def get_user_accessible_organizations(db: Session, tenant_id: UUID, user_id: UUID):
    """Get all organizations accessible to a user"""
    memberships = db.query(OrganizationMembership).filter(
        OrganizationMembership.tenant_id == tenant_id,
        OrganizationMembership.user_id == user_id,
        OrganizationMembership.status == 'active',
        OrganizationMembership.is_deleted == False
    ).all()
    
    return {
        'organizations': [m.organization for m in memberships],
        'roles': {m.organization_id: m.role for m in memberships}
    }
```

### Permission Checking
```python
def check_organization_permission(db: Session, tenant_id: UUID, user_id: UUID, org_id: UUID, required_role: str = 'member') -> bool:
    """Check if user has required role in organization"""
    role_hierarchy = {
        'readonly': 1,
        'member': 2,
        'manager': 3,
        'admin': 4,
        'owner': 5
    }
    
    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.tenant_id == tenant_id,
        OrganizationMembership.user_id == user_id,
        OrganizationMembership.organization_id == org_id,
        OrganizationMembership.status == 'active',
        OrganizationMembership.is_deleted == False
    ).first()
    
    if not membership:
        return False
    
    user_level = role_hierarchy.get(membership.role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level
```

## Security Considerations

### Data Protection
- **Organization Name Uniqueness**: Enforced within tenant boundaries only
- **Email Domain Tracking**: For automatic organization assignment
- **Billing Integration**: Secure Stripe customer ID storage
- **Invitation System**: Track who invited whom for audit purposes

### Performance Optimization
- **Tenant Scoping**: All queries optimized for tenant-specific access patterns
- **Role-based Indexing**: Optimize for permission checking queries
- **Membership Lookups**: Efficient user-organization relationship queries

## Business Logic Patterns

### Organization Creation
```python
def create_organization_with_owner(db: Session, tenant_id: UUID, creator_id: UUID, org_data: dict) -> Organization:
    """Create organization and assign creator as owner"""
    # Create organization
    org = Organization(
        tenant_id=tenant_id,
        name=org_data['name'],
        domain=org_data.get('domain'),
        billing_email=org_data.get('billing_email')
    )
    db.add(org)
    db.flush()  # Get ID without committing
    
    # Create owner membership
    membership = OrganizationMembership(
        tenant_id=tenant_id,
        organization_id=org.id,
        user_id=creator_id,
        role='owner',
        status='active'
    )
    db.add(membership)
    
    return org
```

### User Invitation
```python
def invite_user_to_organization(db: Session, tenant_id: UUID, org_id: UUID, inviter_id: UUID, invitee_email: str, role: str = 'member') -> OrganizationMembership:
    """Invite user to organization"""
    # Find or create user
    user = find_or_create_user_by_email(db, tenant_id, invitee_email)
    
    # Create invitation membership
    invitation = OrganizationMembership(
        tenant_id=tenant_id,
        organization_id=org_id,
        user_id=user.id,
        role=role,
        status='invited',
        invited_by_user_id=inviter_id
    )
    db.add(invitation)
    
    return invitation
```

## Related Schema Files

This organization management schema works with:
- **000_User_Core_Management_Tables.md**: Contains the `users` table referenced by memberships
- **002_User_Team_Management.md**: Contains team tables that reference organizations
- **002_User_Auditing_Security.md**: Contains audit logs that can track organization events

## Next Implementation Steps

1. **Create Alembic migrations** for these two tables
2. **Implement SQLAlchemy models** following the BaseEntity pattern
3. **Build organization repository** with proper tenant scoping
4. **Add organization management endpoints** for CRUD operations
5. **Implement invitation system** for user onboarding

These organization tables provide the foundation for B2B functionality in the Quodsi platform.
