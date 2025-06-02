# Quodsi Multi-Tenant Management Tables - Part 1

This document outlines the database schema design for core tenant management tables in Quodsi. All tables derive from or align with the `BaseEntity` structure.

**BaseEntity Standard Fields Reminder**:
Unless otherwise specified, tables include:
* `id` (UNIQUEIDENTIFIER, PK NONCLUSTERED, DEFAULT NEWID())
* `index_id` (BIGINT, IDENTITY(1,1) NOT NULL, CLUSTERED INDEX)
* `tenant_id` (UNIQUEIDENTIFIER, NOT NULL, FK to `tenants.id`) (Omitted for `tenants` table itself)
* `created_at` (DATETIME2, NOT NULL, DEFAULT GETDATE())
* `updated_at` (DATETIME2, NOT NULL, DEFAULT GETDATE())
* `is_deleted` (BIT, NOT NULL, DEFAULT 0)

---

### `tenants` Table
The master registry of all tenants in the system. This table aligns with BaseEntity principles but does not have a `tenant_id` foreign key itself.

| Column                      | Type              | Constraints                               | Description                                                     |
| :-------------------------- | :---------------- | :---------------------------------------- | :-------------------------------------------------------------- |
| `id`                        | UNIQUEIDENTIFIER  | PK NONCLUSTERED, DEFAULT NEWID()            | Primary identifier for the tenant                               |
| `index_id`                  | BIGINT            | IDENTITY(1,1), NOT NULL, CLUSTERED INDEX  | Physical ordering key                                           |
| `created_at`                | DATETIME2         | NOT NULL, DEFAULT GETDATE()               | When tenant record was created                                  |
| `updated_at`                | DATETIME2         | NOT NULL, DEFAULT GETDATE()               | Last update to tenant record                                    |
| `is_deleted`                | BIT               | NOT NULL, DEFAULT 0                       | Soft delete flag                                                |
| `name`                      | NVARCHAR(255)     | NOT NULL                                  | Name of the tenant                                              |
| `subdomain`                 | NVARCHAR(100)     | UNIQUE, NOT NULL                          | Tenant's unique subdomain (e.g., `acme`.quodsi.com)             |
| `slug`                      | NVARCHAR(100)     | UNIQUE, NOT NULL                          | URL-friendly tenant identifier (e.g., `acme-corp`)              |
| `plan_type`                 | NVARCHAR(50)      | NOT NULL, DEFAULT 'trial'                 | Subscription plan type (trial, starter, professional, enterprise) |
| `max_users`                 | INT               | NOT NULL, DEFAULT 5                       | Maximum number of users allowed for the tenant                  |
| `max_models`                | INT               | NOT NULL, DEFAULT 10                      | Maximum number of models allowed for the tenant                 |
| `max_scenarios_per_month`   | INT               | NOT NULL, DEFAULT 100                     | Maximum scenarios per month allowed for the tenant              |
| `max_storage_gb`            | DECIMAL(10,2)     | NOT NULL, DEFAULT 1.0                     | Maximum storage in GB allowed for the tenant                    |
| `status`                    | NVARCHAR(20)      | NOT NULL, DEFAULT 'trial'                 | Tenant status (trial, active, suspended, cancelled, deleted)    |
| `trial_expires_at`          | DATETIME2         | NULL                                      | Timestamp when the trial period expires                         |
| `activated_at`              | DATETIME2         | NULL                                      | Timestamp when the tenant was activated (e.g., after trial)     |
| `stripe_customer_id`        | NVARCHAR(255)     | NULL                                      | Stripe customer identifier for billing                          |
| `billing_email`             | NVARCHAR(255)     | NULL                                      | Primary email for billing correspondence                        |

**Indexes:**
* `ix_tenants_index_id` CLUSTERED on `index_id`
* `ix_tenants_id` UNIQUE NONCLUSTERED on `id` (PK)
* `ix_tenants_subdomain` UNIQUE NONCLUSTERED on (`subdomain`) WHERE `is_deleted` = 0
* `ix_tenants_slug` UNIQUE NONCLUSTERED on (`slug`) WHERE `is_deleted` = 0
* `ix_tenants_status` NONCLUSTERED on (`status`) WHERE `is_deleted` = 0
* `ix_tenants_stripe_customer_id` NONCLUSTERED on (`stripe_customer_id`) WHERE `stripe_customer_id` IS NOT NULL AND `is_deleted` = 0

**Constraints:**
* `ck_tenants_plan_type` CHECK (`plan_type` IN ('trial', 'starter', 'professional', 'enterprise'))
* `ck_tenants_status` CHECK (`status` IN ('trial', 'active', 'suspended', 'cancelled', 'deleted'))

---

### `tenant_settings` Table
Configuration and branding settings for each tenant. Inherits from `BaseEntity`.

| Column                 | Type              | Constraints                               | Description                                               |
| :--------------------- | :---------------- | :---------------------------------------- | :-------------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Setting record identifier (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Parent tenant for these settings (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Creation timestamp (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `company_name`         | NVARCHAR(255)     | NOT NULL                                  | Official company name for the tenant                      |
| `logo_url`             | NVARCHAR(500)     | NULL                                      | URL to the tenant's logo                                  |
| `favicon_url`          | NVARCHAR(500)     | NULL                                      | URL to the tenant's favicon                               |
| `primary_color`        | NVARCHAR(7)       | NULL                                      | Primary branding color (hex, e.g., `#3498DB`)             |
| `secondary_color`      | NVARCHAR(7)       | NULL                                      | Secondary branding color (hex)                            |
| `features`             | NVARCHAR(MAX)     | NOT NULL, DEFAULT '{}'                    | JSON configuration for enabled features                   |
| `lucidchart_app_id`    | NVARCHAR(255)     | NULL                                      | LucidChart App ID for integration                         |
| `miro_app_id`          | NVARCHAR(255)     | NULL                                      | Miro App ID for integration                               |
| `webhook_url`          | NVARCHAR(500)     | NULL                                      | Webhook URL for tenant-specific notifications             |
| `default_timezone`     | NVARCHAR(100)     | NULL, DEFAULT 'UTC'                       | Default timezone for the tenant                           |
| `default_locale`       | NVARCHAR(10)      | NULL, DEFAULT 'en-US'                     | Default locale for the tenant (e.g., date formats)        |

**Indexes:**
* `ix_tenant_settings_index_id` CLUSTERED on `index_id`
* `ix_tenant_settings_id` UNIQUE NONCLUSTERED on `id`
* `ix_tenant_settings_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_tenant_settings_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `uq_tenant_settings_tenant_id` UNIQUE NONCLUSTERED on (`tenant_id`) WHERE `is_deleted` = 0 (*Ensures one active settings record per tenant*)

**Constraints:**
* `fk_tenant_settings_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`) ON DELETE CASCADE

### `tenant_usage` Table
Tracks current resource usage and enforces limits for each tenant. Inherits from `BaseEntity`.

| Column                 | Type              | Constraints                               | Description                                          |
| :--------------------- | :---------------- | :---------------------------------------- | :--------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Usage record identifier (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Parent tenant for this usage record (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Timestamp record was created (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Timestamp record was last updated (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `current_users`        | INT               | NOT NULL, DEFAULT 0                       | Current number of active users in the tenant         |
| `current_models`       | INT               | NOT NULL, DEFAULT 0                       | Current number of active models in the tenant        |
| `scenarios_this_month` | INT               | NOT NULL, DEFAULT 0                       | Number of scenarios run in the current billing month |
| `storage_used_gb`      | DECIMAL(10,3)     | NOT NULL, DEFAULT 0                       | Current storage used by the tenant in GB             |
| `usage_month`          | INT               | NOT NULL                                  | Month of usage tracking (1-12)                       |
| `usage_year`           | INT               | NOT NULL                                  | Year of usage tracking (e.g., 2025)                  |
| `last_calculated_at`   | DATETIME2         | NOT NULL, DEFAULT GETDATE()               | Timestamp when usage was last calculated/updated     |

**Indexes:**
* `ix_tenant_usage_index_id` CLUSTERED on `index_id`
* `ix_tenant_usage_id` UNIQUE NONCLUSTERED on `id`
* `ix_tenant_usage_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_tenant_usage_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `uq_tenant_usage_period` UNIQUE NONCLUSTERED on (`tenant_id`, `usage_year`, `usage_month`) WHERE `is_deleted` = 0

**Constraints:**
* `fk_tenant_usage_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`) ON DELETE CASCADE

---

### `tenant_user_roles` Table
Manages roles and granular permissions for users within each tenant. Inherits from `BaseEntity`.

| Column                 | Type              | Constraints                               | Description                                            |
| :--------------------- | :---------------- | :---------------------------------------- | :----------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Role assignment identifier (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context of this role assignment (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Timestamp role was granted (BaseEntity `created_at`)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update to role assignment (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `user_id`              | UNIQUEIDENTIFIER  | NOT NULL, FK to `users.id`                | The user assigned the role                             |
| `role`                 | NVARCHAR(50)      | NOT NULL, DEFAULT 'user'                  | Role name (e.g., 'owner', 'admin', 'manager', 'user', 'readonly') |
| `can_invite_users`     | BIT               | NOT NULL, DEFAULT 0                       | Permission flag                                        |
| `can_manage_billing`   | BIT               | NOT NULL, DEFAULT 0                       | Permission flag                                        |
| `can_manage_settings`  | BIT               | NOT NULL, DEFAULT 0                       | Permission flag                                        |
| `can_access_api`       | BIT               | NOT NULL, DEFAULT 0                       | Permission flag                                        |
| `can_export_data`      | BIT               | NOT NULL, DEFAULT 0                       | Permission flag                                        |
| `can_delete_models`    | BIT               | NOT NULL, DEFAULT 0                       | Permission flag                                        |
| `can_manage_users`     | BIT               | NOT NULL, DEFAULT 0                       | Permission flag for managing other users in the tenant |
| `granted_by_user_id`   | UNIQUEIDENTIFIER  | NULL, FK to `users.id`                    | User who granted this role (if applicable)             |
| `is_active`            | BIT               | NOT NULL, DEFAULT 1                       | Whether this role assignment is currently active       |
| `expires_at`           | DATETIME2         | NULL                                      | Optional expiration for temporary role assignments     |

**Indexes:**
* `ix_tenant_user_roles_index_id` CLUSTERED on `index_id`
* `ix_tenant_user_roles_id` UNIQUE NONCLUSTERED on `id`
* `ix_tenant_user_roles_tenant_active_status` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_active` = 1 AND `is_deleted` = 0
* `ix_tenant_user_roles_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `uq_tenant_user_roles_active` UNIQUE NONCLUSTERED on (`tenant_id`, `user_id`) WHERE `is_active` = 1 AND `is_deleted` = 0 (*Ensures one active role per user per tenant*)
* `ix_tenant_user_roles_user` NONCLUSTERED on (`user_id`) WHERE `is_active` = 1 AND `is_deleted` = 0
* `ix_tenant_user_roles_expires` NONCLUSTERED on (`expires_at`) WHERE `expires_at` IS NOT NULL AND `is_active` = 1

**Constraints:**
* `fk_tenant_user_roles_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_tenant_user_roles_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
* `fk_tenant_user_roles_granted_by` FOREIGN KEY (`granted_by_user_id`) REFERENCES `users`(`id`)
* `ck_tenant_user_roles_role` CHECK (`role` IN ('owner', 'admin', 'manager', 'user', 'readonly'))
* `ck_tenant_user_roles_tenant_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `users` WHERE `id` = `user_id`))
* `ck_tenant_user_roles_granted_by_consistency` CHECK (`granted_by_user_id` IS NULL OR `tenant_id` = (SELECT `tenant_id` FROM `users` WHERE `id` = `granted_by_user_id`))