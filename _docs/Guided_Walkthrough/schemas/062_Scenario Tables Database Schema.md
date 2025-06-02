# Quodsi Scenario Tables Database Schema (Multi-Tenant with BaseEntity)

This document outlines the database schema design for Quodsi's scenario management tables. These tables support individual simulation runs with specific parameter configurations, belonging to an analysis. All tables derive from a `BaseEntity` structure.

**BaseEntity Standard Fields**:
Each table listed below, unless otherwise specified, includes the following fields from `BaseEntity`:
* `id` (UNIQUEIDENTIFIER, PK NONCLUSTERED, DEFAULT NEWID())
* `index_id` (BIGINT, IDENTITY(1,1) NOT NULL, CLUSTERED INDEX)
* `tenant_id` (UNIQUEIDENTIFIER, NOT NULL, FK to `tenants.id`)
* `created_at` (DATETIME2, NOT NULL, DEFAULT GETDATE())
* `updated_at` (DATETIME2, NOT NULL, DEFAULT GETDATE())
* `is_deleted` (BIT, NOT NULL, DEFAULT 0)

The `tenants` table (defined separately) is the parent for `tenant_id` foreign keys. The `analyses` and `users` tables are also assumed to be defined as per their updated multi-tenant, BaseEntity-derived schemas.

## Scenario Management Tables

### `scenarios`
Individual simulation runs with specific parameter configurations, belonging to an analysis.

| Column                 | Type              | Constraints                               | Description                                          |
| :--------------------- | :---------------- | :---------------------------------------- | :--------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Primary identifier for the scenario (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context from parent analysis (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Creation timestamp (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `analysis_id`          | UNIQUEIDENTIFIER  | NOT NULL, FK to `analyses.id` ON DELETE CASCADE | Parent analysis this scenario belongs to               |
| `name`                 | NVARCHAR(255)     | NOT NULL                                  | Name of the scenario                                 |
| `description`          | NVARCHAR(MAX)     | NULL                                      | Description of the scenario                          |
| `reps`                 | INT               | NOT NULL, DEFAULT 1                       | Number of simulation replications for this scenario  |
| `time_period`          | NVARCHAR(50)      | NOT NULL, DEFAULT 'daily'                 | Time period for this scenario                        |
| `state`                | NVARCHAR(50)      | NOT NULL, DEFAULT 'not_ready_to_run'      | Execution state of the scenario                      |
| `current_rep`          | INT               | NULL                                      | Current replication number during execution          |
| `total_reps`           | INT               | NULL                                      | Total replications to run (matches `reps`)           |
| `progress_percentage`  | DECIMAL(5,2)      | NULL                                      | Execution progress (0.00 to 100.00)                  |
| `started_at`           | DATETIME2         | NULL                                      | Timestamp when execution started                     |
| `completed_at`         | DATETIME2         | NULL                                      | Timestamp when execution completed                   |
| `execution_time_ms`    | BIGINT            | NULL                                      | Total execution time in milliseconds                 |
| `error_message`        | NVARCHAR(MAX)     | NULL                                      | User-friendly error message if execution failed      |
| `error_details`        | NVARCHAR(MAX)     | NULL                                      | Technical error details if execution failed          |
| `error_stack_trace`    | NVARCHAR(MAX)     | NULL                                      | Full stack trace for debugging if execution failed   |
| `blob_storage_path`    | NVARCHAR(500)     | NULL                                      | Path to detailed results in Azure Blob Storage       |
| `created_by_user_id`   | UNIQUEIDENTIFIER  | NOT NULL, FK to `users.id`                | User who created the scenario                        |

**Indexes:**
* `ix_scenarios_index_id` CLUSTERED on `index_id`
* `ix_scenarios_id` UNIQUE NONCLUSTERED on `id`
* `ix_scenarios_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_scenarios_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_scenarios_tenant_analysis` NONCLUSTERED on (`tenant_id`, `analysis_id`) WHERE `is_deleted` = 0
* `ix_scenarios_tenant_state` NONCLUSTERED on (`tenant_id`, `state`) WHERE `is_deleted` = 0
* `ix_scenarios_tenant_created_by` NONCLUSTERED on (`tenant_id`, `created_by_user_id`) WHERE `is_deleted` = 0

**Constraints:**
* `fk_scenarios_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_scenarios_analysis` FOREIGN KEY (`analysis_id`) REFERENCES `analyses`(`id`) ON DELETE CASCADE
* `fk_scenarios_created_by_user` FOREIGN KEY (`created_by_user_id`) REFERENCES `users`(`id`)
* `ck_scenarios_time_period` CHECK (`time_period` IN ('hourly', 'daily', 'monthly'))
* `ck_scenarios_state` CHECK (`state` IN ('not_ready_to_run', 'ready_to_run', 'is_running', 'cancelling', 'ran_success', 'ran_with_errors'))
* `ck_scenarios_tenant_consistency_analysis` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `analyses` WHERE `id` = `analysis_id`))
* `ck_scenarios_tenant_consistency_user` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `users` WHERE `id` = `created_by_user_id`))
* `uq_scenarios_tenant_analysis_name` UNIQUE (`tenant_id`, `analysis_id`, `name`) WHERE `is_deleted` = 0

### `scenario_item_profiles`
Stores parameter overrides for specific model components within a scenario.

| Column                | Type              | Constraints                               | Description                                                 |
| :-------------------- | :---------------- | :---------------------------------------- | :---------------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Primary identifier for the profile (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context from parent scenario (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Creation timestamp (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `scenario_id`         | UNIQUEIDENTIFIER  | NOT NULL, FK to `scenarios.id` ON DELETE CASCADE | Parent scenario this profile belongs to                     |
| `target_object_id`    | UNIQUEIDENTIFIER  | NOT NULL                                  | ID of the model component being overridden                  |
| `target_object_type`  | NVARCHAR(50)      | NOT NULL                                  | Type of model component (e.g., 'activity', 'resource')      |
| `property_name`       | NVARCHAR(255)     | NOT NULL                                  | Name of the property being overridden                     |
| `property_value`      | NVARCHAR(MAX)     | NOT NULL                                  | New value for the property (stored as string)               |
| `original_value`      | NVARCHAR(MAX)     | NULL                                      | Original value of the property for comparison/rollback      |
| `description`         | NVARCHAR(500)     | NULL                                      | Human-readable description of the change                  |
| `change_reason`       | NVARCHAR(255)     | NULL                                      | Reason why this change was made                           |

**Indexes:**
* `ix_scenario_item_profiles_index_id` CLUSTERED on `index_id`
* `ix_scenario_item_profiles_id` UNIQUE NONCLUSTERED on `id`
* `ix_scenario_item_profiles_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_scenario_item_profiles_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_scenario_item_profiles_tenant_scenario` NONCLUSTERED on (`tenant_id`, `scenario_id`) WHERE `is_deleted` = 0
* `ix_scenario_item_profiles_tenant_target` NONCLUSTERED on (`tenant_id`, `target_object_id`, `target_object_type`) WHERE `is_deleted` = 0

**Constraints:**
* `fk_scenario_item_profiles_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_scenario_item_profiles_scenario` FOREIGN KEY (`scenario_id`) REFERENCES `scenarios`(`id`) ON DELETE CASCADE
* `ck_scenario_item_profiles_target_type` CHECK (`target_object_type` IN ('model', 'activity', 'resource', 'generator', 'entity', 'connector', 'operation_step'))
* `ck_scenprofiles_tenant_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `scenarios` WHERE `id` = `scenario_id`))
* `uq_scenprofiles_tenant_scenario_target_prop` UNIQUE (`tenant_id`, `scenario_id`, `target_object_id`, `property_name`) WHERE `is_deleted` = 0
