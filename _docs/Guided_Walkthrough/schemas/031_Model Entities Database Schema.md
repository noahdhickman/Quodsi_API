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

## Core Model Entity Tables

### `entities`
Represents objects that flow through the simulation system, belonging to a model.

| Column         | Type              | Constraints                               | Description                                     |
| :------------- | :---------------- | :---------------------------------------- | :---------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Primary identifier for the entity (BaseEntity)*|
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context from parent model (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Creation timestamp (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `model_id`     | UNIQUEIDENTIFIER  | NOT NULL, FK to `models.id` ON DELETE CASCADE | Parent model [cite: 766]                                    |
| `name`         | NVARCHAR(255)     | NOT NULL                                  | Name of the entity [cite: 766]                              |
| `description`  | NVARCHAR(MAX)     | NULL                                      | Description of the entity [cite: 766]                       |
| `color`        | NVARCHAR(7)       | NULL                                      | Hex color code for UI display [cite: 766]                   |
| `icon`         | NVARCHAR(100)     | NULL                                      | Icon identifier for UI [cite: 767]                          |

**Indexes:**
* `ix_entities_index_id` CLUSTERED on `index_id`
* `ix_entities_id` UNIQUE NONCLUSTERED on `id`
* `ix_entities_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_entities_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_entities_tenant_model` NONCLUSTERED on (`tenant_id`, `model_id`) WHERE `is_deleted` = 0

**Constraints:**
* `fk_entities_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_entities_model` FOREIGN KEY (`model_id`) REFERENCES `models`(`id`) ON DELETE CASCADE [cite: 767]
* `ck_entities_tenant_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `models` WHERE `id` = `model_id`))
* `uq_entities_tenant_model_name` UNIQUE (`tenant_id`, `model_id`, `name`) WHERE `is_deleted` = 0

### `resources`
Represents constrained items required by activities, belonging to a model.

| Column         | Type              | Constraints                               | Description                                     |
| :------------- | :---------------- | :---------------------------------------- | :---------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Primary identifier for the resource (BaseEntity)*|
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context from parent model (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Creation timestamp (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `model_id`     | UNIQUEIDENTIFIER  | NOT NULL, FK to `models.id` ON DELETE CASCADE | Parent model [cite: 768]                                    |
| `name`         | NVARCHAR(255)     | NOT NULL                                  | Name of the resource [cite: 768]                            |
| `description`  | NVARCHAR(MAX)     | NULL                                      | Description of the resource [cite: 768]                     |
| `capacity`     | INT               | NOT NULL, DEFAULT 1                       | Number of available units [cite: 768]                       |
| `cost_per_hour`| DECIMAL(10,2)     | NULL                                      | Cost for using the resource per hour [cite: 769]            |
| `color`        | NVARCHAR(7)       | NULL                                      | Hex color code for UI display [cite: 769]                   |
| `icon`         | NVARCHAR(100)     | NULL                                      | Icon identifier for UI [cite: 769]                          |

**Indexes:**
* `ix_resources_index_id` CLUSTERED on `index_id`
* `ix_resources_id` UNIQUE NONCLUSTERED on `id`
* `ix_resources_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_resources_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_resources_tenant_model` NONCLUSTERED on (`tenant_id`, `model_id`) WHERE `is_deleted` = 0

**Constraints:**
* `fk_resources_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_resources_model` FOREIGN KEY (`model_id`) REFERENCES `models`(`id`) ON DELETE CASCADE [cite: 769]
* `ck_resources_tenant_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `models` WHERE `id` = `model_id`))
* `uq_resources_tenant_model_name` UNIQUE (`tenant_id`, `model_id`, `name`) WHERE `is_deleted` = 0

### `activities`
Represents processing nodes where entities spend time and consume resources, belonging to a model.

| Column                  | Type              | Constraints                               | Description                                     |
| :---------------------- | :---------------- | :---------------------------------------- | :---------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Primary identifier for the activity (BaseEntity)*|
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context from parent model (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Creation timestamp (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `model_id`              | UNIQUEIDENTIFIER  | NOT NULL, FK to `models.id` ON DELETE CASCADE | Parent model [cite: 770]                                    |
| `name`                  | NVARCHAR(255)     | NOT NULL                                  | Name of the activity [cite: 771]                            |
| `description`           | NVARCHAR(MAX)     | NULL                                      | Description of the activity [cite: 771]                     |
| `capacity`              | INT               | NOT NULL, DEFAULT 1                       | Concurrent processing capacity [cite: 771]                  |
| `input_buffer_capacity` | INT               | NOT NULL, DEFAULT 1                       | Queue size before processing [cite: 771]                    |
| `output_buffer_capacity`| INT               | NOT NULL, DEFAULT 1                       | Queue size after processing [cite: 771]                     |
| `position_x`            | DECIMAL(10,2)     | NULL                                      | X-coordinate for visual layout [cite: 772]                  |
| `position_y`            | DECIMAL(10,2)     | NULL                                      | Y-coordinate for visual layout [cite: 772]                  |
| `color`                 | NVARCHAR(7)       | NULL                                      | Hex color code for UI display [cite: 772]                   |
| `icon`                  | NVARCHAR(100)     | NULL                                      | Icon identifier for UI [cite: 773]                          |

**Indexes:**
* `ix_activities_index_id` CLUSTERED on `index_id`
* `ix_activities_id` UNIQUE NONCLUSTERED on `id`
* `ix_activities_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_activities_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_activities_tenant_model` NONCLUSTERED on (`tenant_id`, `model_id`) WHERE `is_deleted` = 0

**Constraints:**
* `fk_activities_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_activities_model` FOREIGN KEY (`model_id`) REFERENCES `models`(`id`) ON DELETE CASCADE [cite: 773]
* `ck_activities_tenant_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `models` WHERE `id` = `model_id`))
* `uq_activities_tenant_model_name` UNIQUE (`tenant_id`, `model_id`, `name`) WHERE `is_deleted` = 0

### `operation_steps`
Represents individual processing steps within activities.

| Column                     | Type              | Constraints                               | Description                                     |
| :------------------------- | :---------------- | :---------------------------------------- | :---------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Primary identifier for the step (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context from parent activity (BaseEntity)*|
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Creation timestamp (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `activity_id`              | UNIQUEIDENTIFIER  | NOT NULL, FK to `activities.id` ON DELETE CASCADE | Parent activity [cite: 774]                                 |
| `step_order`               | INT               | NOT NULL                                  | Execution order within the activity [cite: 774]             |
| `name`                     | NVARCHAR(255)     | NOT NULL                                  | Name of the operation step [cite: 775]                      |
| `duration_type`            | NVARCHAR(20)      | NOT NULL, DEFAULT 'constant'              | Type of duration distribution [cite: 775]                   |
| `duration_value_1`         | DECIMAL(18,6)     | NOT NULL                                  | Primary duration value (constant, mean, min) [cite: 776]    |
| `duration_value_2`         | DECIMAL(18,6)     | NULL                                      | Secondary duration value (max, std dev) [cite: 776]         |
| `duration_value_3`         | DECIMAL(18,6)     | NULL                                      | Tertiary duration value (mode for triangular) [cite: 776]   |
| `duration_unit`            | NVARCHAR(20)      | NOT NULL, DEFAULT 'minutes'               | Unit of duration [cite: 776]                                |
| `resource_requirement_id`  | UNIQUEIDENTIFIER  | NULL, FK to `resource_requirements.id`    | Required resources (defined in another table) [cite: 777]   |

**Indexes:**
* `ix_operation_steps_index_id` CLUSTERED on `index_id`
* `ix_operation_steps_id` UNIQUE NONCLUSTERED on `id`
* `ix_operation_steps_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_operation_steps_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_operation_steps_tenant_activity_order` NONCLUSTERED on (`tenant_id`, `activity_id`, `step_order`) WHERE `is_deleted` = 0

**Constraints:**
* `fk_operation_steps_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_operation_steps_activity` FOREIGN KEY (`activity_id`) REFERENCES `activities`(`id`) ON DELETE CASCADE [cite: 778]
* `fk_operation_steps_resource_requirement` FOREIGN KEY (`resource_requirement_id`) REFERENCES `resource_requirements`(`id`) [cite: 778] (*`resource_requirements` table also needs `BaseEntity` and tenant-awareness*)
* `ck_operation_steps_duration_type` CHECK (`duration_type` IN ('constant', 'triangular', 'normal', 'exponential', 'uniform')) [cite: 775]
* `ck_operation_steps_duration_unit` CHECK (`duration_unit` IN ('seconds', 'minutes', 'hours', 'days')) [cite: 777]
* `ck_opsteps_tenant_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `activities` WHERE `id` = `activity_id`))
* `uq_operation_steps_tenant_activity_name` UNIQUE (`tenant_id`, `activity_id`, `name`) WHERE `is_deleted` = 0
* `uq_operation_steps_tenant_activity_order` UNIQUE (`tenant_id`, `activity_id`, `step_order`) WHERE `is_deleted` = 0

### `generators`
Controls entity creation and introduction into the simulation, belonging to a model.

| Column                     | Type              | Constraints                               | Description                                     |
| :------------------------- | :---------------- | :---------------------------------------- | :---------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Primary identifier for the generator (BaseEntity)*|
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context from parent model (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Creation timestamp (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `model_id`                 | UNIQUEIDENTIFIER  | NOT NULL, FK to `models.id` ON DELETE CASCADE | Parent model [cite: 779]                                    |
| `name`                     | NVARCHAR(255)     | NOT NULL                                  | Name of the generator [cite: 779]                           |
| `description`              | NVARCHAR(MAX)     | NULL                                      | Description of the generator [cite: 780]                    |
| `entity_id`                | UNIQUEIDENTIFIER  | NOT NULL, FK to `entities.id`             | Type of entity to generate [cite: 780]                      |
| `target_activity_id`       | UNIQUEIDENTIFIER  | NOT NULL, FK to `activities.id`           | Where generated entities are sent [cite: 780]               |
| `periodic_occurrences`     | INT               | NOT NULL, DEFAULT 1                       | Number of creation cycles [cite: 780]                       |
| `period_interval_duration` | DECIMAL(18,6)     | NOT NULL, DEFAULT 1                       | Time between cycles [cite: 781]                             |
| `period_interval_unit`     | NVARCHAR(20)      | NOT NULL, DEFAULT 'minutes'               | Unit for period interval [cite: 781]                        |
| `entities_per_creation`    | INT               | NOT NULL, DEFAULT 1                       | Entities created per cycle [cite: 781]                      |
| `periodic_start_duration`  | DECIMAL(18,6)     | NOT NULL, DEFAULT 0                       | Delay before first creation [cite: 781]                     |
| `max_entities`             | INT               | NULL                                      | Maximum entities to generate (NULL = unlimited) [cite: 781] |
| `position_x`               | DECIMAL(10,2)     | NULL                                      | X-coordinate for visual layout [cite: 782]                  |
| `position_y`               | DECIMAL(10,2)     | NULL                                      | Y-coordinate for visual layout [cite: 782]                  |
| `color`                    | NVARCHAR(7)       | NULL                                      | Hex color code for UI display [cite: 782]                   |
| `icon`                     | NVARCHAR(100)     | NULL                                      | Icon identifier for UI [cite: 783]                          |

**Indexes:**
* `ix_generators_index_id` CLUSTERED on `index_id`
* `ix_generators_id` UNIQUE NONCLUSTERED on `id`
* `ix_generators_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_generators_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_generators_tenant_model` NONCLUSTERED on (`tenant_id`, `model_id`) WHERE `is_deleted` = 0

**Constraints:**
* `fk_generators_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_generators_model` FOREIGN KEY (`model_id`) REFERENCES `models`(`id`) ON DELETE CASCADE [cite: 784]
* `fk_generators_entity` FOREIGN KEY (`entity_id`) REFERENCES `entities`(`id`) [cite: 784]
* `fk_generators_target_activity` FOREIGN KEY (`target_activity_id`) REFERENCES `activities`(`id`) [cite: 784]
* `ck_generators_tenant_consistency` CHECK (
    `tenant_id` = (SELECT `tenant_id` FROM `models` WHERE `id` = `model_id`) AND
    `tenant_id` = (SELECT `tenant_id` FROM `entities` WHERE `id` = `entity_id`) AND
    `tenant_id` = (SELECT `tenant_id` FROM `activities` WHERE `id` = `target_activity_id`)
)
* `uq_generators_tenant_model_name` UNIQUE (`tenant_id`, `model_id`, `name`) WHERE `is_deleted` = 0

### `connectors`
Defines flow relationships between simulation objects, belonging to a model.

| Column          | Type              | Constraints                               | Description                                     |
| :-------------- | :---------------- | :---------------------------------------- | :---------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Primary identifier for the connector (BaseEntity)*|
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context from parent model (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Creation timestamp (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `model_id`      | UNIQUEIDENTIFIER  | NOT NULL, FK to `models.id` ON DELETE CASCADE | Parent model [cite: 785]                                    |
| `name`          | NVARCHAR(255)     | NULL                                      | Name of the connector [cite: 785]                           |
| `source_id`     | UNIQUEIDENTIFIER  | NOT NULL                                  | Source object ID (activity or generator) [cite: 785]        |
| `source_type`   | NVARCHAR(20)      | NOT NULL                                  | Type of source object ('activity', 'generator') [cite: 786] |
| `target_id`     | UNIQUEIDENTIFIER  | NOT NULL                                  | Target object ID (typically activity) [cite: 786]           |
| `target_type`   | NVARCHAR(20)      | NOT NULL                                  | Type of target object ('activity') [cite: 786]              |
| `connect_type`  | NVARCHAR(20)      | NOT NULL, DEFAULT 'probability'           | Routing logic type ('probability', 'attribute_value') [cite: 786] |
| `probability`   | DECIMAL(5,4)      | NOT NULL, DEFAULT 1.0                     | Probability for routing (0.0 to 1.0) [cite: 787]            |
| `attribute_name`| NVARCHAR(100)     | NULL                                      | For attribute-based routing: attribute name [cite: 787]     |
| `attribute_value`|NVARCHAR(255)     | NULL                                      | For attribute-based routing: attribute value [cite: 787]    |
| `route_points`  | NVARCHAR(MAX)     | NULL                                      | JSON array of coordinates for line paths [cite: 787]        |

**Indexes:**
* `ix_connectors_index_id` CLUSTERED on `index_id`
* `ix_connectors_id` UNIQUE NONCLUSTERED on `id`
* `ix_connectors_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_connectors_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_connectors_tenant_model` NONCLUSTERED on (`tenant_id`, `model_id`) WHERE `is_deleted` = 0
* `ix_connectors_tenant_source` NONCLUSTERED on (`tenant_id`, `source_id`, `source_type`) WHERE `is_deleted` = 0
* `ix_connectors_tenant_target` NONCLUSTERED on (`tenant_id`, `target_id`, `target_type`) WHERE `is_deleted` = 0

**Constraints:**
* `fk_connectors_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_connectors_model` FOREIGN KEY (`model_id`) REFERENCES `models`(`id`) ON DELETE CASCADE [cite: 788]
* `ck_connectors_source_type` CHECK (`source_type` IN ('activity', 'generator')) [cite: 786]
* `ck_connectors_target_type` CHECK (`target_type` IN ('activity')) [cite: 786]
* `ck_connectors_connect_type` CHECK (`connect_type` IN ('probability', 'attribute_value')) [cite: 786]
* `ck_connectors_tenant_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `models` WHERE `id` = `model_id`))
 (*Further checks could ensure `source_id` and `target_id` entities also share the same `tenant_id`*)