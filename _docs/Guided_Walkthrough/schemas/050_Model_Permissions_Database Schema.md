# Quodsi Permissions and Security Database Schema (Multi-Tenant with BaseEntity)

This document outlines the database schema design for Quodsi's model permissions. THis table manages access control for models and provide an audit trail for model-related operations. All tables derive from a `BaseEntity` structure.

**BaseEntity Standard Fields**:
Each table listed below, unless otherwise specified, includes the following fields from `BaseEntity`:
* `id` (UNIQUEIDENTIFIER, PK NONCLUSTERED, DEFAULT NEWID())
* `index_id` (BIGINT, IDENTITY(1,1) NOT NULL, CLUSTERED INDEX)
* `tenant_id` (UNIQUEIDENTIFIER, NOT NULL, FK to `tenants.id`)
* `created_at` (DATETIME2, NOT NULL, DEFAULT GETDATE())
* `updated_at` (DATETIME2, NOT NULL, DEFAULT GETDATE())
* `is_deleted` (BIT, NOT NULL, DEFAULT 0)

The `tenants` table (defined separately) is the parent for `tenant_id` foreign keys. The `models`, `users`, `organizations`, and `teams` tables are also assumed to be defined as per their updated multi-tenant, BaseEntity-derived schemas.

## Permissions and Security Tables

### `model_permissions`
Granular access control for models with role-based permissions, supporting user, team, and organization-level access grants.

| Column                 | Type              | Constraints                               | Description                                                       |
| :--------------------- | :---------------- | :---------------------------------------- | :---------------------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Primary identifier for the permission (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context from the model and target entity (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Timestamp when permission was granted (BaseEntity `created_at`)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (used if permissions are archived instead of hard deleted) (BaseEntity)* |
| `model_id`             | UNIQUEIDENTIFIER  | NOT NULL, FK to `models.id` ON DELETE CASCADE | The model to which this permission applies                        |
| `user_id`              | UNIQUEIDENTIFIER  | NULL, FK to `users.id`                    | Target user for this permission (if applicable)                 |
| `organization_id`      | UNIQUEIDENTIFIER  | NULL, FK to `organizations.id`            | Target organization for this permission (if applicable)           |
| `team_id`              | UNIQUEIDENTIFIER  | NULL, FK to `teams.id`                    | Target team for this permission (if applicable)                 |
| `permission_level`     | NVARCHAR(20)      | NOT NULL, DEFAULT 'read'                  | Access level ('read', 'write', 'execute', 'admin')                |
| `granted_by_user_id`   | UNIQUEIDENTIFIER  | NOT NULL, FK to `users.id`                | User who granted this permission                                  |
| `expires_at`           | DATETIME2         | NULL                                      | Optional expiration date for temporary access                     |
| `is_active`            | BIT               | NOT NULL, DEFAULT 1                       | Whether the permission is currently active (distinct from `is_deleted`) |
| `revoked_at`           | DATETIME2         | NULL                                      | Timestamp when permission was revoked                             |
| `revoked_by_user_id`   | UNIQUEIDENTIFIER  | NULL, FK to `users.id`                    | User who revoked the permission                                   |
| `grant_reason`         | NVARCHAR(500)     | NULL                                      | Reason why the permission was granted                             |
| `revoke_reason`        | NVARCHAR(500)     | NULL                                      | Reason why the permission was revoked                             |

**Indexes:**
* `ix_model_permissions_index_id` CLUSTERED on `index_id`
* `ix_model_permissions_id` UNIQUE NONCLUSTERED on `id`
* `ix_model_permissions_tenant_active_status` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_active` = 1 AND `is_deleted` = 0
* `ix_model_permissions_tenant_model` NONCLUSTERED on (`tenant_id`, `model_id`, `is_active`)
* `ix_model_permissions_tenant_user` NONCLUSTERED on (`tenant_id`, `user_id`, `model_id`, `is_active`) WHERE `user_id` IS NOT NULL
* `ix_model_permissions_tenant_organization` NONCLUSTERED on (`tenant_id`, `organization_id`, `model_id`, `is_active`) WHERE `organization_id` IS NOT NULL
* `ix_model_permissions_tenant_team` NONCLUSTERED on (`tenant_id`, `team_id`, `model_id`, `is_active`) WHERE `team_id` IS NOT NULL
* `ix_model_permissions_expires_at` NONCLUSTERED on (`expires_at`) WHERE `expires_at` IS NOT NULL AND `is_active` = 1

**Constraints:**
* `fk_model_permissions_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_model_permissions_model` FOREIGN KEY (`model_id`) REFERENCES `models`(`id`) ON DELETE CASCADE
* `fk_model_permissions_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
* `fk_model_permissions_organization` FOREIGN KEY (`organization_id`) REFERENCES `organizations`(`id`)
* `fk_model_permissions_team` FOREIGN KEY (`team_id`) REFERENCES `teams`(`id`)
* `fk_model_permissions_granted_by_user` FOREIGN KEY (`granted_by_user_id`) REFERENCES `users`(`id`)
* `fk_model_permissions_revoked_by_user` FOREIGN KEY (`revoked_by_user_id`) REFERENCES `users`(`id`)
* `ck_model_permissions_single_target` CHECK (
    (`user_id` IS NOT NULL AND `organization_id` IS NULL AND `team_id` IS NULL) OR
    (`user_id` IS NULL AND `organization_id` IS NOT NULL AND `team_id` IS NULL) OR
    (`user_id` IS NULL AND `organization_id` IS NULL AND `team_id` IS NOT NULL)
)
* `ck_model_permissions_level` CHECK (`permission_level` IN ('read', 'write', 'execute', 'admin'))
* `ck_modelpermissions_tenant_model_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `models` WHERE `id` = `model_id`))
* `ck_modelpermissions_tenant_user_consistency` CHECK (`user_id` IS NULL OR `tenant_id` = (SELECT `tenant_id` FROM `users` WHERE `id` = `user_id`))
* `ck_modelpermissions_tenant_org_consistency` CHECK (`organization_id` IS NULL OR `tenant_id` = (SELECT `tenant_id` FROM `organizations` WHERE `id` = `organization_id`))
* `ck_modelpermissions_tenant_team_consistency` CHECK (`team_id` IS NULL OR `tenant_id` = (SELECT `tenant_id` FROM `teams` WHERE `id` = `team_id`))
* `ck_modelpermissions_tenant_grantedby_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `users` WHERE `id` = `granted_by_user_id`))
