# Quodsi Resource Requirements Database Schema (Multi-Tenant with BaseEntity)

This document outlines the database schema design for Quodsi's resource requirements system, which supports complex resource allocation rules for simulation models. All tables derive from a `BaseEntity` structure.

**BaseEntity Standard Fields**:
Each table listed below, unless otherwise specified, includes the following fields from `BaseEntity`:
* `id` (UNIQUEIDENTIFIER, PK NONCLUSTERED, DEFAULT NEWID())
* `index_id` (BIGINT, IDENTITY(1,1) NOT NULL, CLUSTERED INDEX)
* `tenant_id` (UNIQUEIDENTIFIER, NOT NULL, FK to `tenants.id`)
* `created_at` (DATETIME2, NOT NULL, DEFAULT GETDATE())
* `updated_at` (DATETIME2, NOT NULL, DEFAULT GETDATE())
* `is_deleted` (BIT, NOT NULL, DEFAULT 0)

The `tenants` table (defined separately) is the parent for `tenant_id` foreign keys. The `models` and `resources` tables are assumed to be defined as per their updated multi-tenant, BaseEntity-derived schemas.

## Resource Requirements System Tables

### `resource_requirements`
Top-level container for resource requirement definitions, belonging to a model.

| Column         | Type              | Constraints                               | Description                                          |
| :------------- | :---------------- | :---------------------------------------- | :--------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Primary identifier for the requirement (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context from parent model (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Creation timestamp (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `model_id`     | UNIQUEIDENTIFIER  | NOT NULL, FK to `models.id` ON DELETE CASCADE | Parent model this requirement belongs to               |
| `name`         | NVARCHAR(255)     | NOT NULL                                  | Name of the resource requirement                       |
| `description`  | NVARCHAR(MAX)     | NULL                                      | Description of the resource requirement                |

**Indexes:**
* `ix_resource_requirements_index_id` CLUSTERED on `index_id` (from BaseEntity)
* `ix_resource_requirements_id` UNIQUE NONCLUSTERED on `id` (PK from BaseEntity)
* `ix_resource_requirements_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0 (from BaseEntity)
* `ix_resource_requirements_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`) (from BaseEntity)
* `ix_resource_requirements_tenant_model` NONCLUSTERED on (`tenant_id`, `model_id`) WHERE `is_deleted` = 0

**Constraints:**
* `fk_resource_requirements_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_resource_requirements_model` FOREIGN KEY (`model_id`) REFERENCES `models`(`id`) ON DELETE CASCADE
* `ck_resource_requirements_tenant_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `models` WHERE `id` = `model_id`))
* `uq_resource_requirements_tenant_model_name` UNIQUE (`tenant_id`, `model_id`, `name`) WHERE `is_deleted` = 0

### `requirement_clauses`
Represents logical groupings (AND/OR) of resource requests within a `resource_requirement`.

| Column                  | Type              | Constraints                               | Description                                          |
| :---------------------- | :---------------- | :---------------------------------------- | :--------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Primary identifier for the clause (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context from parent requirement (BaseEntity)*|
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Creation timestamp (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `resource_requirement_id` | UNIQUEIDENTIFIER  | NOT NULL, FK to `resource_requirements.id` ON DELETE CASCADE | Parent resource requirement                          |
| `name`                  | NVARCHAR(255)     | NULL                                      | Optional name for the clause                           |
| `parent_clause_id`      | UNIQUEIDENTIFIER  | NULL, FK to `requirement_clauses.id`      | For nested clause structures (self-referencing)      |
| `clause_order`          | INT               | NOT NULL, DEFAULT 0                       | Order of this clause within its parent               |
| `requirement_mode`      | NVARCHAR(20)      | NOT NULL, DEFAULT 'require_all'           | Logical mode ('require_all' for AND, 'require_any' for OR) |

**Indexes:**
* `ix_requirement_clauses_index_id` CLUSTERED on `index_id`
* `ix_requirement_clauses_id` UNIQUE NONCLUSTERED on `id`
* `ix_requirement_clauses_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_requirement_clauses_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_requirement_clauses_tenant_req_id` NONCLUSTERED on (`tenant_id`, `resource_requirement_id`) WHERE `is_deleted` = 0
* `ix_requirement_clauses_tenant_parent_clause` NONCLUSTERED on (`tenant_id`, `parent_clause_id`) WHERE `parent_clause_id` IS NOT NULL AND `is_deleted` = 0

**Constraints:**
* `fk_requirement_clauses_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_requirement_clauses_resource_requirement` FOREIGN KEY (`resource_requirement_id`) REFERENCES `resource_requirements`(`id`) ON DELETE CASCADE
* `fk_requirement_clauses_parent` FOREIGN KEY (`parent_clause_id`) REFERENCES `requirement_clauses`(`id`)
* `ck_requirement_clauses_mode` CHECK (`requirement_mode` IN ('require_all', 'require_any'))
* `ck_reqclauses_tenant_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `resource_requirements` WHERE `id` = `resource_requirement_id`))
* `ck_reqclauses_parent_tenant_consistency` CHECK (`parent_clause_id` IS NULL OR `tenant_id` = (SELECT `tenant_id` FROM `requirement_clauses` WHERE `id` = `parent_clause_id`))

### `resource_requests`
Individual resource requests within clauses, specifying the type and quantity of a resource needed.

| Column         | Type              | Constraints                               | Description                                          |
| :------------- | :---------------- | :---------------------------------------- | :--------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Primary identifier for the request (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context from parent clause (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Creation timestamp (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `clause_id`    | UNIQUEIDENTIFIER  | NOT NULL, FK to `requirement_clauses.id` ON DELETE CASCADE | Parent requirement clause this request belongs to    |
| `resource_id`  | UNIQUEIDENTIFIER  | NOT NULL, FK to `resources.id`            | The specific resource being requested                  |
| `quantity`     | INT               | NOT NULL, DEFAULT 1                       | Number of units of this resource required            |
| `request_order`| INT               | NOT NULL, DEFAULT 0                       | Order of this request within the clause for evaluation |

**Indexes:**
* `ix_resource_requests_index_id` CLUSTERED on `index_id`
* `ix_resource_requests_id` UNIQUE NONCLUSTERED on `id`
* `ix_resource_requests_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_resource_requests_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_resource_requests_tenant_clause_id` NONCLUSTERED on (`tenant_id`, `clause_id`) WHERE `is_deleted` = 0
* `ix_resource_requests_tenant_resource_id` NONCLUSTERED on (`tenant_id`, `resource_id`) WHERE `is_deleted` = 0

**Constraints:**
* `fk_resource_requests_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_resource_requests_clause` FOREIGN KEY (`clause_id`) REFERENCES `requirement_clauses`(`id`) ON DELETE CASCADE
* `fk_resource_requests_resource` FOREIGN KEY (`resource_id`) REFERENCES `resources`(`id`)
* `ck_resourcereq_tenant_consistency_clause` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `requirement_clauses` WHERE `id` = `clause_id`))
* `ck_resourcereq_tenant_consistency_resource` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `resources` WHERE `id` = `resource_id`))