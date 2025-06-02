# User Team Management Database Schema (Multi-Tenant with BaseEntity)

This document outlines the team management database schema for Quodsi's user management system. These tables provide team collaboration capabilities within organizations, building upon both core user management and organization management foundations.

**Prerequisites**: This schema depends on the tables defined in:
- `000_User_Core_Management_Tables.md`
- `001_User_Organization_Management.md`

**BaseEntity Standard Fields**:
Each table includes the following fields from `BaseEntity` (see `000_User_Core_Management_Tables.md` for details):
* `id`, `index_id`, `tenant_id`, `created_at`, `updated_at`, `is_deleted`

## Implementation Priority

These tables should be implemented **after** the organization management tables:

1. **`teams`** - Sub-groups within organizations
2. **`team_memberships`** - Links users to teams with roles

## Team Management Tables

### `teams`
Sub-groups within organizations for project collaboration and access control.

| Column                 | Type              | Constraints                               | Description                                     |
| :--------------------- | :---------------- | :---------------------------------------- | :---------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Team identifier (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant owning this team (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Creation timestamp (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `organization_id`      | UNIQUEIDENTIFIER  | NOT NULL, FK to `organizations.id`        | Reference to parent organization                |
| `name`                 | VARCHAR(255)      | NOT NULL                                  | Team name                                       |
| `description`          | NVARCHAR(MAX)     | NULL                                      | Team description and purpose                    |
| `created_by_user_id`   | UNIQUEIDENTIFIER  | NULL, FK to `users.id`                    | User who created the team                       |
| `is_default`           | BIT               | NOT NULL, DEFAULT 0                       | Whether this is the default team for the org   |
| `metadata`             | NVARCHAR(MAX)     | NULL                                      | Additional team information (JSON data)         |

**Indexes:**
* `ix_teams_index_id` CLUSTERED on `index_id`
* `ix_teams_id` UNIQUE NONCLUSTERED on `id`
* `ix_teams_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_teams_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_teams_tenant_org` NONCLUSTERED on (`tenant_id`, `organization_id`) WHERE `is_deleted` = 0
* `ix_teams_tenant_org_name` UNIQUE NONCLUSTERED on (`tenant_id`, `organization_id`, `name`) WHERE `is_deleted` = 0

**Constraints:**
* `fk_teams_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_teams_organization` FOREIGN KEY (`organization_id`) REFERENCES `organizations`(`id`)
* `fk_teams_created_by` FOREIGN KEY (`created_by_user_id`) REFERENCES `users`(`id`)
* `ck_teams_tenant_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `organizations` WHERE `id` = `organization_id`))

### `team_memberships`
Links users to teams with specific roles and permissions.

| Column             | Type              | Constraints                               | Description                                         |
| :----------------- | :---------------- | :---------------------------------------- | :-------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Membership identifier (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context of membership (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *When user was added (BaseEntity `created_at`)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `team_id`          | UNIQUEIDENTIFIER  | NOT NULL, FK to `teams.id`                | Reference to team                                   |
| `user_id`          | UNIQUEIDENTIFIER  | NOT NULL, FK to `users.id`                | Reference to user                                   |
| `role`             | VARCHAR(50)       | NOT NULL, DEFAULT 'member'                | Role (leader, member)                               |
| `status`           | VARCHAR(20)       | NOT NULL, DEFAULT 'active'                | Status (active, invited, inactive)                  |
| `invited_by_user_id`| UNIQUEIDENTIFIER | NULL, FK to `users.id`                    | User who invited this member                        |
| `last_active_at`   | DATETIME2         | NULL                                      | Last activity in this team                          |

**Indexes:**
* `ix_team_memberships_index_id` CLUSTERED on `index_id`
* `ix_team_memberships_id` UNIQUE NONCLUSTERED on `id`
* `ix_team_memberships_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_team_memberships_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_team_memberships_tenant_team` NONCLUSTERED on (`tenant_id`, `team_id`) WHERE `is_deleted` = 0
* `ix_team_memberships_tenant_user` NONCLUSTERED on (`tenant_id`, `user_id`) WHERE `is_deleted` = 0
* `uq_team_memberships_tenant_team_user` UNIQUE NONCLUSTERED on (`tenant_id`, `team_id`, `user_id`) WHERE `is_deleted` = 0 AND `status` <> 'invited'

**Constraints:**
* `fk_team_memberships_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_team_memberships_team` FOREIGN KEY (`team_id`) REFERENCES `teams`(`id`)
* `fk_team_memberships_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
* `fk_team_memberships_invited_by` FOREIGN KEY (`invited_by_user_id`) REFERENCES `users`(`id`)
* `ck_team_memberships_role` CHECK (`role` IN ('leader', 'member'))
* `ck_team_memberships_status` CHECK (`status` IN ('active', 'invited', 'inactive'))
* `ck_teammembers_tenant_consistency` CHECK (
    `tenant_id` = (SELECT `tenant_id` FROM `users` WHERE `id` = `user_id`) AND
    `tenant_id` = (SELECT `tenant_id` FROM `teams` WHERE `id` = `team_id`)
)

## Hierarchical Relationship Patterns

### Team Hierarchy
```
Tenant
└── Organizations
    └── Teams (multiple per organization)
        └── Team Memberships (users with roles)
```

### Role-Based Access Control

#### Team Roles
1. **leader** - Can manage team members, team settings, and team resources
2. **member** - Standard team member with access to team resources

## Repository Pattern Examples

```python
# app/repositories/team_repository.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.db.models.teams import Team, TeamMembership
from app.repositories.base_repository import BaseRepository

class TeamRepository(BaseRepository[Team]):
    def __init__(self, db: Session):
        super().__init__(db, Team)
    
    def get_organization_teams(self, tenant_id: UUID, org_id: UUID) -> List[Team]:
        """Get all teams for an organization"""
        return self.db.query(Team).filter(
            Team.tenant_id == tenant_id,
            Team.organization_id == org_id,
            Team.is_deleted == False
        ).order_by(Team.name).all()
    
    def get_user_teams(self, tenant_id: UUID, user_id: UUID) -> List[Team]:
        """Get all teams for a user within tenant"""
        return self.db.query(Team).join(TeamMembership).filter(
            Team.tenant_id == tenant_id,
            TeamMembership.user_id == user_id,
            TeamMembership.status == 'active',
            Team.is_deleted == False,
            TeamMembership.is_deleted == False
        ).order_by(Team.name).all()
    
    def get_user_role_in_team(self, tenant_id: UUID, user_id: UUID, team_id: UUID) -> Optional[str]:
        """Get user's role in specific team"""
        membership = self.db.query(TeamMembership).filter(
            TeamMembership.tenant_id == tenant_id,
            TeamMembership.user_id == user_id,
            TeamMembership.team_id == team_id,
            TeamMembership.status == 'active',
            TeamMembership.is_deleted == False
        ).first()
        return membership.role if membership else None
    
    def user_can_manage_team(self, tenant_id: UUID, user_id: UUID, team_id: UUID) -> bool:
        """Check if user can manage team"""
        role = self.get_user_role_in_team(tenant_id, user_id, team_id)
        return role == 'leader'
    
    def get_team_members(self, tenant_id: UUID, team_id: UUID) -> List[dict]:
        """Get all members of a team with their roles"""
        memberships = self.db.query(TeamMembership).filter(
            TeamMembership.tenant_id == tenant_id,
            TeamMembership.team_id == team_id,
            TeamMembership.status == 'active',
            TeamMembership.is_deleted == False
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
    
    def get_default_team_for_organization(self, tenant_id: UUID, org_id: UUID) -> Optional[Team]:
        """Get the default team for an organization"""
        return self.db.query(Team).filter(
            Team.tenant_id == tenant_id,
            Team.organization_id == org_id,
            Team.is_default == True,
            Team.is_deleted == False
        ).first()
```

## Business Logic Patterns

### Team Creation
```python
def create_team_with_leader(db: Session, tenant_id: UUID, org_id: UUID, creator_id: UUID, team_data: dict) -> Team:
    """Create team and assign creator as leader"""
    # Create team
    team = Team(
        tenant_id=tenant_id,
        organization_id=org_id,
        name=team_data['name'],
        description=team_data.get('description'),
        created_by_user_id=creator_id,
        is_default=team_data.get('is_default', False)
    )
    db.add(team)
    db.flush()  # Get ID without committing
    
    # Create leader membership
    membership = TeamMembership(
        tenant_id=tenant_id,
        team_id=team.id,
        user_id=creator_id,
        role='leader',
        status='active'
    )
    db.add(membership)
    
    return team
```

### Default Team Management
```python
def ensure_default_team_for_organization(db: Session, tenant_id: UUID, org_id: UUID) -> Team:
    """Ensure organization has a default team"""
    default_team = db.query(Team).filter(
        Team.tenant_id == tenant_id,
        Team.organization_id == org_id,
        Team.is_default == True,
        Team.is_deleted == False
    ).first()
    
    if not default_team:
        # Create default team
        default_team = Team(
            tenant_id=tenant_id,
            organization_id=org_id,
            name="General",
            description="Default team for organization members",
            is_default=True
        )
        db.add(default_team)
    
    return default_team
```

## Related Schema Files

This team management schema works with:
- **000_User_Core_Management_Tables.md**: Contains the `users` table referenced by memberships
- **001_User_Organization_Management.md**: Contains organization tables that teams belong to
- **003_User_Auditing_Security.md**: Contains audit logs that can track team events

## Next Implementation Steps

1. **Create Alembic migrations** for these two tables
2. **Implement SQLAlchemy models** following the BaseEntity pattern
3. **Build team repository** with proper tenant and organization scoping
4. **Add team management endpoints** for CRUD operations
5. **Implement default team creation** for new organizations
6. **Create team invitation system** for collaborative workflows

These team tables complete the hierarchical user management structure, providing the foundation for collaborative features in the Quodsi platform.
