# Quodsi Permissions and Security Database Schema (Multi-Tenant with BaseEntity)

This document outlines the database schema design for Quodsi's model audit logs and security access logs. These tables manage access control for models and provide an audit trail for model-related operations. All tables derive from a `BaseEntity` structure.

**BaseEntity Standard Fields**:
Each table listed below, unless otherwise specified, includes the following fields from `BaseEntity`:
* `id` (UNIQUEIDENTIFIER, PK NONCLUSTERED, DEFAULT NEWID())
* `index_id` (BIGINT, IDENTITY(1,1) NOT NULL, CLUSTERED INDEX)
* `tenant_id` (UNIQUEIDENTIFIER, NOT NULL, FK to `tenants.id`)
* `created_at` (DATETIME2, NOT NULL, DEFAULT GETDATE())
* `updated_at` (DATETIME2, NOT NULL, DEFAULT GETDATE())
* `is_deleted` (BIT, NOT NULL, DEFAULT 0)

The `tenants` table (defined separately) is the parent for `tenant_id` foreign keys. The `models`, `users`, `organizations`, and `teams` tables are also assumed to be defined as per their updated multi-tenant, BaseEntity-derived schemas.

## Tables
### `model_access_logs`
Audit trail for model access and operations, extending the existing general audit system with model-specific tracking.

| Column                 | Type              | Constraints                               | Description                                                       |
| :--------------------- | :---------------- | :---------------------------------------- | :---------------------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Primary identifier for the access log (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context from the model and user (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Timestamp of access (BaseEntity `created_at` as `accessed_at`)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity, usually same as created_at)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity, usually audit logs are not deleted)* |
| `model_id`             | UNIQUEIDENTIFIER  | NOT NULL, FK to `models.id`               | The model that was accessed/actioned                               |
| `user_id`              | UNIQUEIDENTIFIER  | NOT NULL, FK to `users.id`                | The user who performed the action                                 |
| `access_type`          | NVARCHAR(50)      | NOT NULL                                  | Type of access or operation (e.g., 'view', 'edit', 'execute')   |
| `access_result`        | NVARCHAR(20)      | NOT NULL                                  | Outcome of the access attempt ('granted', 'denied')             |
| `permission_source`    | NVARCHAR(50)      | NULL                                      | Source of permission (e.g., 'owner', 'user_permission', 'public') |
| `permission_id`        | UNIQUEIDENTIFIER  | NULL, FK to `model_permissions.id`        | Specific permission record that allowed/denied access             |
| `session_id`           | UNIQUEIDENTIFIER  | NULL                                      | User session ID, if available                                   |
| `ip_address`           | NVARCHAR(45)      | NULL                                      | IP address of the user                                          |
| `user_agent`           | NVARCHAR(500)     | NULL                                      | User agent string of the client                                 |
| `details`              | NVARCHAR(MAX)     | NULL                                      | Additional context or details about the access (JSON)             |

**Indexes:**
* `ix_model_access_logs_index_id` CLUSTERED on `index_id`
* `ix_model_access_logs_id` UNIQUE NONCLUSTERED on `id`
* `ix_model_access_logs_tenant_created` NONCLUSTERED on (`tenant_id`, `created_at` DESC)
* `ix_model_access_logs_tenant_model_user` NONCLUSTERED on (`tenant_id`, `model_id`, `user_id`, `created_at` DESC)
* `ix_model_access_logs_tenant_user_created` NONCLUSTERED on (`tenant_id`, `user_id`, `created_at` DESC)

**Constraints:**
* `fk_model_access_logs_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_model_access_logs_model` FOREIGN KEY (`model_id`) REFERENCES `models`(`id`)
* `fk_model_access_logs_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
* `fk_model_access_logs_permission` FOREIGN KEY (`permission_id`) REFERENCES `model_permissions`(`id`)
* `ck_model_access_logs_access_type` CHECK (`access_type` IN ('view', 'edit', 'execute', 'share', 'delete', 'permission_change'))
* `ck_model_access_logs_access_result` CHECK (`access_result` IN ('granted', 'denied', 'success', 'failure'))
* `ck_modelaccesslogs_tenant_model_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `models` WHERE `id` = `model_id`))
* `ck_modelaccesslogs_tenant_user_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `users` WHERE `id` = `user_id`))