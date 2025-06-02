# Quodsi Core Model Entities Database Schema (Multi-Tenant with BaseEntity)

This document outlines the database schema design for Quodsi's core model entities, supporting simulation model definitions. All tables derive from a `BaseEntity` structure.

**BaseEntity Standard Fields**:
Each table listed below, unless otherwise specified, includes the following fields from `BaseEntity`:
* `id` (UNIQUEIDENTIFIER, PK NONCLUSTERED, DEFAULT NEWID())
* `index_id` (BIGINT, IDENTITY(1,1) NOT NULL, CLUSTERED INDEX)
* `tenant_id` (UNIQUEIDENTIFIER, NOT NULL, FK to `tenants.id`)
* `created_at` (DATETIME2, NOT NULL, DEFAULT GETDATE())
* `updated_at` (DATETIME2, NOT NULL, DEFAULT GETDATE())
* `is_deleted` (BIT, NOT NULL, DEFAULT 0)

The `tenants` table (defined separately, e.g., in `01a3_MultiTenant_Tables.md`) is the parent for `tenant_id` foreign keys. The `users`, `organizations`, and `teams` tables are also assumed to be defined as per the updated User Management schema.

## Core Model Tables

### `models`
Central table containing all simulation models across platforms.

| Column                 | Type              | Constraints                               | Description                                                     |
| :--------------------- | :---------------- | :---------------------------------------- | :-------------------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Primary identifier for the model (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant owning this model (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *When model record was created (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update to model record (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `name`                 | NVARCHAR(255)     | NOT NULL                                  | Name of the model                                               |
| `description`          | NVARCHAR(MAX)     | NULL                                      | Description of the model                                        |
| `source`               | NVARCHAR(50)      | NOT NULL                                  | Source of the model ('lucidchart', 'standalone', 'miro') [cite: 761]      |
| `source_document_id`   | NVARCHAR(255)     | NULL                                      | LucidChart document ID, MIRO board ID, etc. [cite: 761]                 |
| `source_url`           | NVARCHAR(500)     | NULL                                      | URL to the source document/board                                |
| `reps`                 | INT               | NOT NULL, DEFAULT 1                       | Default number of simulation replications [cite: 761]                       |
| `forecast_days`        | INT               | NOT NULL, DEFAULT 30                      | Default forecast period in days [cite: 761]                                 |
| `random_seed`          | INT               | NULL                                      | Default random seed for simulations [cite: 762]                             |
| `time_type`            | NVARCHAR(20)      | NOT NULL, DEFAULT 'clock'                 | Time mode ('clock', 'calendar') [cite: 762]                                 |
| `one_clock_unit`       | NVARCHAR(20)      | NULL                                      | For clock mode: ('seconds', 'minutes', 'hours', 'days') [cite: 762]   |
| `warmup_clock_period`  | DECIMAL(18,6)     | NULL                                      | For clock mode: Warmup duration [cite: 762]                                 |
| `run_clock_period`     | DECIMAL(18,6)     | NULL                                      | For clock mode: Run duration [cite: 762]                                    |
| `warmup_date_time`     | DATETIME2         | NULL                                      | For calendar mode: Warmup start date/time [cite: 763]                   |
| `start_date_time`      | DATETIME2         | NULL                                      | For calendar mode: Run start date/time [cite: 763]                      |
| `finish_date_time`     | DATETIME2         | NULL                                      | For calendar mode: Run finish date/time [cite: 763]                     |
| `created_by_user_id`   | UNIQUEIDENTIFIER  | NOT NULL, FK to `users.id`                | User who created the model [cite: 763]                                      |
| `organization_id`      | UNIQUEIDENTIFIER  | NULL, FK to `organizations.id`            | Organization associated with the model (must share `tenant_id`) [cite: 763] |
| `team_id`              | UNIQUEIDENTIFIER  | NULL, FK to `teams.id`                    | Team associated with the model (must share `tenant_id`) [cite: 763]         |
| `is_public`            | BIT               | NOT NULL, DEFAULT 0                       | Whether the model is publicly accessible (within tenant or globally, TBD) [cite: 764] |
| `is_template`          | BIT               | NOT NULL, DEFAULT 0                       | Whether the model can be used as a template [cite: 764]                     |
| `version`              | INT               | NOT NULL, DEFAULT 1                       | Model version number [cite: 765]                                            |
| `blob_storage_url`     | NVARCHAR(500)     | NULL                                      | For legacy models: URL to model definition in blob storage [cite: 765]    |

**Indexes:**
* `ix_models_index_id` CLUSTERED on `index_id` (from BaseEntity)
* `ix_models_id` UNIQUE NONCLUSTERED on `id` (PK from BaseEntity)
* `ix_models_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0 (from BaseEntity)
* `ix_models_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`) (from BaseEntity)
* `ix_models_tenant_name` NONCLUSTERED on (`tenant_id`, `name`) WHERE `is_deleted` = 0
* `ix_models_tenant_created_by_user` NONCLUSTERED on (`tenant_id`, `created_by_user_id`) WHERE `is_deleted` = 0
* `ix_models_tenant_source` NONCLUSTERED on (`tenant_id`, `source`) WHERE `is_deleted` = 0
* `ix_models_tenant_organization` NONCLUSTERED on (`tenant_id`, `organization_id`) WHERE `organization_id` IS NOT NULL AND `is_deleted` = 0
* `ix_models_tenant_team` NONCLUSTERED on (`tenant_id`, `team_id`) WHERE `team_id` IS NOT NULL AND `is_deleted` = 0

**Constraints:**
* `fk_models_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_models_created_by_user` FOREIGN KEY (`created_by_user_id`) REFERENCES `users`(`id`) [cite: 765]
* `fk_models_organization` FOREIGN KEY (`organization_id`) REFERENCES `organizations`(`id`) [cite: 765]
* `fk_models_team` FOREIGN KEY (`team_id`) REFERENCES `teams`(`id`) [cite: 765]
* `ck_models_source` CHECK (`source` IN ('lucidchart', 'standalone', 'miro')) [cite: 761]
* `ck_models_time_type` CHECK (`time_type` IN ('clock', 'calendar')) [cite: 762]
* `ck_models_one_clock_unit` CHECK (`one_clock_unit` IN ('seconds', 'minutes', 'hours', 'days') OR `one_clock_unit` IS NULL) [cite: 762]
* `ck_models_tenant_org_consistency` CHECK (`organization_id` IS NULL OR `tenant_id` = (SELECT `tenant_id` FROM `organizations` WHERE `id` = `organization_id`))
* `ck_models_tenant_team_consistency` CHECK (`team_id` IS NULL OR `tenant_id` = (SELECT `tenant_id` FROM `teams` WHERE `id` = `team_id`))
* `ck_models_tenant_user_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `users` WHERE `id` = `created_by_user_id`))