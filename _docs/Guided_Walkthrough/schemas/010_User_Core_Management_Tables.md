# User Core Management Database Schema (Multi-Tenant with BaseEntity)

This document outlines the foundational database schema for Quodsi's core user management system. These tables form the absolute foundation that all other user-related functionality depends upon.

**BaseEntity Standard Fields**:
Each table listed below includes the following fields from `BaseEntity`:
* `id` (UNIQUEIDENTIFIER, PK NONCLUSTERED, DEFAULT NEWID())
* `index_id` (BIGINT, IDENTITY(1,1) NOT NULL, CLUSTERED INDEX)
* `tenant_id` (UNIQUEIDENTIFIER, NOT NULL, FK to `tenants.id`)
* `created_at` (DATETIME2, NOT NULL, DEFAULT GETDATE())
* `updated_at` (DATETIME2, NOT NULL, DEFAULT GETDATE())
* `is_deleted` (BIT, NOT NULL, DEFAULT 0)

The `tenants` table (defined separately, e.g., in `000_Multi-Tenant Management Tables.md`) is the parent for `tenant_id` foreign keys.

## Implementation Priority

These are the **first tables** that must be implemented in the user management system:

1. **`users`** - Core user identity and authentication information
2. **`user_sessions`** - Session tracking for authentication and security
3. **`user_usage_stats`** - Daily usage aggregation for reporting and analytics

Without these foundational tables, no other user management functionality can exist.

## Core User Management Tables

### `users`
Stores core user information synchronized from identity providers.

| Column                 | Type              | Constraints                               | Description                                     |
| :--------------------- | :---------------- | :---------------------------------------- | :---------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Primary identifier for the user (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *User's primary tenant context (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *When user record was created (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update to user record (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `identity_provider`    | VARCHAR(50)       | NOT NULL                                  | Provider type ('entra_id', 'google', etc.)      |
| `identity_provider_id` | VARCHAR(255)      | NOT NULL                                  | Unique identifier from the provider             |
| `email`                | VARCHAR(255)      | NOT NULL                                  | User's email address                            |
| `display_name`         | VARCHAR(255)      | NOT NULL                                  | User's display name                             |
| `last_login_at`        | DATETIME2         | NULL                                      | Most recent login timestamp                     |
| `login_count`          | INT               | NOT NULL, DEFAULT 0                       | Count of user logins                            |
| `total_usage_minutes`  | INT               | NOT NULL, DEFAULT 0                       | Cumulative time spent using Quodsi              |
| `last_session_start`   | DATETIME2         | NULL                                      | When current/last session started               |
| `last_active_at`       | DATETIME2         | NULL                                      | Last user activity timestamp                    |
| `status`               | VARCHAR(20)       | NOT NULL, DEFAULT 'active'                | User status (active, invited, suspended)        |
| `metadata`             | NVARCHAR(MAX)     | NULL                                      | Additional profile information (JSON data)      |

**Indexes:**
* `ix_users_index_id` CLUSTERED on `index_id` (from BaseEntity)
* `ix_users_id` UNIQUE NONCLUSTERED on `id` (PK from BaseEntity)
* `ix_users_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0 (from BaseEntity)
* `ix_users_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`) (from BaseEntity)
* `ix_users_tenant_email` UNIQUE NONCLUSTERED on (`tenant_id`, `email`) WHERE `is_deleted` = 0
* `ix_users_identity_provider` NONCLUSTERED on (`identity_provider`, `identity_provider_id`) WHERE `is_deleted` = 0

**Constraints:**
* `fk_users_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `ck_users_status` CHECK (`status` IN ('active', 'invited', 'suspended', 'pending_verification'))
* `ck_users_identity_provider` CHECK (`identity_provider` IN ('entra_id', 'google', 'email', 'github'))

### `user_sessions`
Tracks user session information for analytics and auditing.

| Column             | Type              | Constraints                               | Description                                         |
| :----------------- | :---------------- | :---------------------------------------- | :-------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Session identifier (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context of the session (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Session start time (BaseEntity `created_at`)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update to session record (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity, typically not used)* |
| `user_id`          | UNIQUEIDENTIFIER  | NOT NULL, FK to `users.id`                | Reference to user                                   |
| `ended_at`         | DATETIME2         | NULL                                      | Session end time (null if active)                   |
| `duration_minutes` | INT               | NULL                                      | Session duration (calculated on end)                |
| `session_type`     | VARCHAR(20)       | NOT NULL, DEFAULT 'normal'                | Session type (normal, idle)                         |
| `client_type`      | VARCHAR(50)       | NOT NULL, DEFAULT 'unknown'               | Client application type (lucidchart, standalone, miro, api) |
| `client_info`      | VARCHAR(255)      | NULL                                      | Browser/device information                          |
| `ip_address`       | VARCHAR(45)       | NULL                                      | User's IP address                                   |

**Indexes:**
* `ix_user_sessions_index_id` CLUSTERED on `index_id`
* `ix_user_sessions_id` UNIQUE NONCLUSTERED on `id`
* `ix_user_sessions_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_user_sessions_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_user_sessions_tenant_user_created` NONCLUSTERED on (`tenant_id`, `user_id`, `created_at` DESC)
* `ix_user_sessions_tenant_client_type` NONCLUSTERED on (`tenant_id`, `client_type`) WHERE `is_deleted` = 0

**Constraints:**
* `fk_user_sessions_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_user_sessions_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
* `ck_user_sessions_client_type` CHECK (`client_type` IN ('lucidchart', 'standalone', 'miro', 'api', 'web', 'mobile', 'unknown'))
* `ck_user_sessions_tenant_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `users` WHERE `id` = `user_id`))

### `user_usage_stats`
Aggregated daily usage statistics for reporting.

| Column                 | Type              | Constraints                               | Description                                     |
| :--------------------- | :---------------- | :---------------------------------------- | :---------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Stat record identifier (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context of the stats (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *When stat record was created (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update to stat record (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `user_id`              | UNIQUEIDENTIFIER  | NOT NULL, FK to `users.id`                | Reference to user                               |
| `date`                 | DATE              | NOT NULL                                  | Date of statistics                              |
| `login_count`          | INT               | NOT NULL, DEFAULT 0                       | Number of logins on this date                   |
| `active_minutes`       | INT               | NOT NULL, DEFAULT 0                       | Minutes of activity on this date                |
| `simulation_runs`      | INT               | NOT NULL, DEFAULT 0                       | Number of simulations run                       |
| `documents_accessed`   | INT               | NOT NULL, DEFAULT 0                       | Number of documents accessed                    |
| `feature_usage`        | NVARCHAR(MAX)     | NULL                                      | Detailed feature usage stats (JSON data)        |

**Indexes:**
* `ix_user_usage_stats_index_id` CLUSTERED on `index_id`
* `ix_user_usage_stats_id` UNIQUE NONCLUSTERED on `id`
* `ix_user_usage_stats_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_user_usage_stats_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `uq_user_usage_stats_tenant_user_date` UNIQUE NONCLUSTERED on (`tenant_id`, `user_id`, `date`) WHERE `is_deleted` = 0

**Constraints:**
* `fk_user_usage_stats_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_user_usage_stats_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
* `ck_user_usage_stats_tenant_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `users` WHERE `id` = `user_id`))

## Repository Pattern Integration

### BaseRepository for User Management
Your BaseRepository must enforce tenant_id scoping for all user-related operations:

```python
# app/repositories/user_repository.py
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from app.db.models.users import User
from app.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(db, User)
    
    def get_by_email(self, tenant_id: UUID, email: str) -> Optional[User]:
        """Get user by email within tenant"""
        return self.db.query(User).filter(
            User.tenant_id == tenant_id,
            User.email == email,
            User.is_deleted == False
        ).first()
    
    def get_by_identity_provider(self, identity_provider: str, provider_id: str) -> Optional[User]:
        """Get user by identity provider credentials"""
        return self.db.query(User).filter(
            User.identity_provider == identity_provider,
            User.identity_provider_id == provider_id,
            User.is_deleted == False
        ).first()
    
    def update_login_stats(self, tenant_id: UUID, user_id: UUID) -> bool:
        """Update user login statistics"""
        user = self.get_by_id(tenant_id, user_id)
        if user:
            user.login_count += 1
            user.last_login_at = datetime.utcnow()
            user.last_active_at = datetime.utcnow()
            return True
        return False
```

## Query Patterns and Best Practices

### Critical Rule: Always Filter by tenant_id
```python
# GOOD: Tenant-scoped user query
def get_tenant_users(db: Session, current_tenant_id: UUID):
    return db.query(User).filter(
        User.tenant_id == current_tenant_id,
        User.is_deleted == False,
        User.status == 'active'
    ).all()

# BAD: Missing tenant_id filter - DANGEROUS DATA LEAK RISK
# def get_all_users(db: Session):
#     return db.query(User).filter(User.is_deleted == False).all()
```

### User Authentication Pattern
```python
def authenticate_user(db: Session, identity_provider: str, provider_id: str, email: str) -> Optional[User]:
    # First try to find by identity provider
    user = db.query(User).filter(
        User.identity_provider == identity_provider,
        User.identity_provider_id == provider_id,
        User.is_deleted == False
    ).first()
    
    # Fallback to email within same tenant if user exists
    if not user:
        user = db.query(User).filter(
            User.email == email,
            User.is_deleted == False
        ).first()
    
    return user
```

## Security Considerations

### Data Protection
- **Email Uniqueness**: Enforced within tenant boundaries only
- **Identity Provider Mapping**: Global uniqueness across all tenants
- **Session Security**: Track IP addresses and client information for security auditing
- **Soft Deletes**: Preserve user data for audit trails and compliance

### Performance Optimization
- **Clustered Index**: `index_id` for optimal insert performance
- **Tenant Scoping**: All queries optimized for tenant-specific access patterns
- **Usage Stats**: Pre-aggregated daily statistics to avoid real-time calculations

## Data Consistency Rules

### Tenant Consistency
- Every user belongs to exactly one primary tenant
- All user sessions must match the user's tenant
- Usage statistics must match the user's tenant
- Check constraints enforce referential integrity

### Session Management
- Active sessions have `ended_at` = NULL
- Ended sessions have calculated `duration_minutes`
- Session types: 'normal', 'idle', 'timeout', 'logout'
- Client types track the application source

## Related Schema Files

This core user management schema works with:
- **Multi-Tenant Management Tables**: Contains the `tenants` table referenced by `tenant_id`
- **User Organization Team Management**: Contains organizational hierarchy (requires these core tables)
- **User Auditing Security**: Contains audit logs (references these core tables)

## Next Implementation Steps

1. **Create Alembic migrations** for these three tables
2. **Implement SQLAlchemy models** following the BaseEntity pattern
3. **Build repository classes** with proper tenant scoping
4. **Add authentication services** that use these tables
5. **Create basic CRUD endpoints** for user management

These core tables provide the foundation for all user-related functionality in the Quodsi platform.
