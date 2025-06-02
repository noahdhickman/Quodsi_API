# Quodsi Analysis Tables Database Schema (Multi-Tenant with BaseEntity)

This document outlines the database schema design for Quodsi's analysis management tables. These tables support hierarchical simulation studies: Models → Analyses → Scenarios, enabling parameter sweeps and what-if analyses. All tables derive from a `BaseEntity` structure.

**BaseEntity Standard Fields**:
Each table listed below, unless otherwise specified, includes the following fields from `BaseEntity`:
* `id` (UNIQUEIDENTIFIER, PK NONCLUSTERED, DEFAULT NEWID())
* `index_id` (BIGINT, IDENTITY(1,1) NOT NULL, CLUSTERED INDEX)
* `tenant_id` (UNIQUEIDENTIFIER, NOT NULL, FK to `tenants.id`)
* `created_at` (DATETIME2, NOT NULL, DEFAULT GETDATE())
* `updated_at` (DATETIME2, NOT NULL, DEFAULT GETDATE())
* `is_deleted` (BIT, NOT NULL, DEFAULT 0)

The `tenants` table (defined separately) is the parent for `tenant_id` foreign keys. The `models` and `users` tables are also assumed to be defined as per their updated multi-tenant, BaseEntity-derived schemas.

## Analysis Management Tables

### `analyses`
Top-level container for grouping related scenarios, representing a study or experiment using a specific model.

| Column                 | Type              | Constraints                               | Description                                          |
| :--------------------- | :---------------- | :---------------------------------------- | :--------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Primary identifier for the analysis (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context from parent model (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Creation timestamp (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `model_id`             | UNIQUEIDENTIFIER  | NOT NULL, FK to `models.id` ON DELETE CASCADE | Parent model this analysis belongs to                  |
| `name`                 | NVARCHAR(255)     | NOT NULL                                  | Name of the analysis study                           |
| `description`          | NVARCHAR(MAX)     | NULL                                      | Description of the analysis study                    |
| `default_reps`         | INT               | NOT NULL, DEFAULT 1                       | Default number of replications for child scenarios   |
| `default_time_period`  | NVARCHAR(50)      | NOT NULL, DEFAULT 'daily'                 | Default time period for child scenarios              |
| `created_by_user_id`   | UNIQUEIDENTIFIER  | NOT NULL, FK to `users.id`                | User who created the analysis                        |

**Indexes:**
* `ix_analyses_index_id` CLUSTERED on `index_id` (from BaseEntity)
* `ix_analyses_id` UNIQUE NONCLUSTERED on `id` (PK from BaseEntity)
* `ix_analyses_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0 (from BaseEntity)
* `ix_analyses_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`) (from BaseEntity)
* `ix_analyses_tenant_model` NONCLUSTERED on (`tenant_id`, `model_id`) WHERE `is_deleted` = 0
* `ix_analyses_tenant_created_by` NONCLUSTERED on (`tenant_id`, `created_by_user_id`) WHERE `is_deleted` = 0

**Constraints:**
* `fk_analyses_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_analyses_model` FOREIGN KEY (`model_id`) REFERENCES `models`(`id`) ON DELETE CASCADE
* `fk_analyses_created_by_user` FOREIGN KEY (`created_by_user_id`) REFERENCES `users`(`id`)
* `ck_analyses_default_time_period` CHECK (`default_time_period` IN ('hourly', 'daily', 'monthly'))
* `ck_analyses_tenant_consistency_model` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `models` WHERE `id` = `model_id`))
* `ck_analyses_tenant_consistency_user` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `users` WHERE `id` = `created_by_user_id`))
* `uq_analyses_tenant_model_name` UNIQUE (`tenant_id`, `model_id`, `name`) WHERE `is_deleted` = 0
