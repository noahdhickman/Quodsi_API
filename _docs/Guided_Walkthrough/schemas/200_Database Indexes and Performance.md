# Quodsi Database Indexes and Performance Optimization (Multi-Tenant with BaseEntity)

This document outlines additional database indexes and performance optimization considerations for the Quodsi database, complementing the standard indexes provided by the `BaseEntity` structure. Indexes are designed based on expected query patterns and access frequency in a multi-tenant environment. Regular monitoring and adjustment may be needed based on actual usage patterns.

**BaseEntity Standard Indexes Note:**
The `BaseEntity` structure already provides standard indexes for each table:
* A clustered index on `index_id`.
* A unique non-clustered primary key index on `id`.
* A non-clustered index `ix_{table}_tenant_active` on (`tenant_id`, `index_id`) WHERE `is_deleted = 0`.
* A non-clustered index `ix_{table}_tenant_id_lookup` on (`tenant_id`, `id`).

The indexes listed below are *additional* business-specific or query-optimization indexes, now made tenant-aware. All `WHERE is_deleted = 0` clauses are retained to optimize queries for active data.

## Core Model Table Indexes (`models`)

```sql
-- Additional indexes for the 'models' table
CREATE NONCLUSTERED INDEX idx_models_tenant_created_by_user_id 
ON models(tenant_id, created_by_user_id) 
INCLUDE (name, source, is_public, created_at) 
WHERE is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_models_tenant_organization_id 
ON models(tenant_id, organization_id) 
INCLUDE (name, created_by_user_id, created_at) 
WHERE organization_id IS NOT NULL AND is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_models_tenant_team_id 
ON models(tenant_id, team_id) 
INCLUDE (name, created_by_user_id, created_at) 
WHERE team_id IS NOT NULL AND is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_models_tenant_source 
ON models(tenant_id, source) 
INCLUDE (name, created_by_user_id, created_at) 
WHERE is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_models_tenant_is_public 
ON models(tenant_id, is_public) 
INCLUDE (name, description, created_at) 
WHERE is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_models_tenant_source_document_id 
ON models(tenant_id, source_document_id) 
INCLUDE (name, source) 
WHERE source_document_id IS NOT NULL AND is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_models_tenant_is_template 
ON models(tenant_id, is_template) 
INCLUDE (name, description, source) 
WHERE is_template = 1 AND is_deleted = 0;

-- Search and filtering for 'models' table
CREATE NONCLUSTERED INDEX idx_models_tenant_name_search 
ON models(tenant_id, name) 
WHERE is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_models_tenant_created_at 
ON models(tenant_id, created_at DESC) 
INCLUDE (name, created_by_user_id, source) 
WHERE is_deleted = 0;
Model Component Indexes
activities Table
SQL

CREATE NONCLUSTERED INDEX idx_activities_tenant_model_id 
ON activities(tenant_id, model_id) 
INCLUDE (name, capacity, created_at) 
WHERE is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_activities_tenant_model_name 
ON activities(tenant_id, model_id, name) 
WHERE is_deleted = 0;
entities Table
SQL

CREATE NONCLUSTERED INDEX idx_entities_tenant_model_id 
ON entities(tenant_id, model_id) 
INCLUDE (name, created_at) 
WHERE is_deleted = 0;
resources Table
SQL

CREATE NONCLUSTERED INDEX idx_resources_tenant_model_id 
ON resources(tenant_id, model_id) 
INCLUDE (name, capacity, created_at) 
WHERE is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_resources_tenant_capacity 
ON resources(tenant_id, capacity) 
INCLUDE (model_id, name) 
WHERE capacity > 1 AND is_deleted = 0;
generators Table
SQL

CREATE NONCLUSTERED INDEX idx_generators_tenant_model_id 
ON generators(tenant_id, model_id) 
INCLUDE (name, entity_id, target_activity_id) 
WHERE is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_generators_tenant_entity_id 
ON generators(tenant_id, entity_id) 
INCLUDE (model_id, name) 
WHERE is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_generators_tenant_target_activity_id 
ON generators(tenant_id, target_activity_id) 
INCLUDE (model_id, name) 
WHERE is_deleted = 0;
connectors Table
SQL

CREATE NONCLUSTERED INDEX idx_connectors_tenant_model_id 
ON connectors(tenant_id, model_id) 
INCLUDE (source_id, target_id, connect_type) 
WHERE is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_connectors_tenant_source_id 
ON connectors(tenant_id, source_id, source_type) 
INCLUDE (model_id, target_id, target_type) 
WHERE is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_connectors_tenant_target_id 
ON connectors(tenant_id, target_id, target_type) 
INCLUDE (model_id, source_id, source_type) 
WHERE is_deleted = 0;
operation_steps Indexes
SQL

CREATE NONCLUSTERED INDEX idx_operation_steps_tenant_activity_id_order 
ON operation_steps(tenant_id, activity_id, step_order) 
INCLUDE (name, duration_type, duration_value_1) 
WHERE is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_operation_steps_tenant_resource_requirement_id 
ON operation_steps(tenant_id, resource_requirement_id) 
INCLUDE (activity_id, name) 
WHERE resource_requirement_id IS NOT NULL AND is_deleted = 0;
Resource Requirements Indexes
resource_requirements Table
SQL

CREATE NONCLUSTERED INDEX idx_resource_requirements_tenant_model_id 
ON resource_requirements(tenant_id, model_id) 
INCLUDE (name, created_at) 
WHERE is_deleted = 0;
requirement_clauses Table
SQL

CREATE NONCLUSTERED INDEX idx_requirement_clauses_tenant_resource_requirement_id 
ON requirement_clauses(tenant_id, resource_requirement_id) 
INCLUDE (name, requirement_mode, clause_order) 
WHERE is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_requirement_clauses_tenant_parent_clause_id 
ON requirement_clauses(tenant_id, parent_clause_id) 
INCLUDE (resource_requirement_id, clause_order) 
WHERE parent_clause_id IS NOT NULL AND is_deleted = 0;
resource_requests Table
SQL

CREATE NONCLUSTERED INDEX idx_resource_requests_tenant_clause_id_order 
ON resource_requests(tenant_id, clause_id, request_order) 
INCLUDE (resource_id, quantity) 
WHERE is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_resource_requests_tenant_resource_id 
ON resource_requests(tenant_id, resource_id) 
INCLUDE (clause_id, quantity) 
WHERE is_deleted = 0;
Analysis and Scenario Indexes
analyses Table
SQL

CREATE NONCLUSTERED INDEX idx_analyses_tenant_model_id 
ON analyses(tenant_id, model_id) 
INCLUDE (name, created_by_user_id, created_at) 
WHERE is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_analyses_tenant_created_by_user_id 
ON analyses(tenant_id, created_by_user_id) 
INCLUDE (name, model_id, created_at) 
WHERE is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_analyses_tenant_created_at 
ON analyses(tenant_id, created_at DESC) 
INCLUDE (name, model_id, created_by_user_id) 
WHERE is_deleted = 0;
scenarios Table
SQL

CREATE NONCLUSTERED INDEX idx_scenarios_tenant_analysis_id 
ON scenarios(tenant_id, analysis_id) 
INCLUDE (name, state, created_by_user_id, created_at) 
WHERE is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_scenarios_tenant_state 
ON scenarios(tenant_id, state) 
INCLUDE (name, analysis_id, started_at, progress_percentage) 
WHERE is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_scenarios_tenant_created_by_user_id 
ON scenarios(tenant_id, created_by_user_id) 
INCLUDE (name, analysis_id, state, created_at) 
WHERE is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_scenarios_tenant_running 
ON scenarios(tenant_id, state, started_at) 
INCLUDE (name, analysis_id, progress_percentage, current_rep) 
WHERE state = 'is_running' AND is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_scenarios_tenant_execution_monitoring 
ON scenarios(tenant_id, started_at) 
INCLUDE (name, state, progress_percentage) 
WHERE state IN ('is_running', 'cancelling') AND is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_scenarios_tenant_execution_time 
ON scenarios(tenant_id, execution_time_ms) 
INCLUDE (analysis_id, reps, completed_at) 
WHERE state = 'ran_success' AND execution_time_ms IS NOT NULL AND is_deleted = 0;
scenario_item_profiles Table
SQL

CREATE NONCLUSTERED INDEX idx_scenario_item_profiles_tenant_scenario_id 
ON scenario_item_profiles(tenant_id, scenario_id) 
INCLUDE (target_object_id, target_object_type, property_name) 
WHERE is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_scenario_item_profiles_tenant_target_object 
ON scenario_item_profiles(tenant_id, target_object_id, target_object_type) 
INCLUDE (scenario_id, property_name, property_value) 
WHERE is_deleted = 0;
Permissions and Security Indexes
model_permissions Table
SQL

CREATE NONCLUSTERED INDEX idx_model_permissions_tenant_model_id 
ON model_permissions(tenant_id, model_id) 
INCLUDE (user_id, team_id, organization_id, permission_level, granted_at) 
WHERE is_active = 1 AND is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_model_permissions_tenant_user_id 
ON model_permissions(tenant_id, user_id) 
INCLUDE (model_id, permission_level, expires_at) 
WHERE user_id IS NOT NULL AND is_active = 1 AND is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_model_permissions_tenant_team_id 
ON model_permissions(tenant_id, team_id) 
INCLUDE (model_id, permission_level, expires_at) 
WHERE team_id IS NOT NULL AND is_active = 1 AND is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_model_permissions_tenant_organization_id 
ON model_permissions(tenant_id, organization_id) 
INCLUDE (model_id, permission_level, expires_at) 
WHERE organization_id IS NOT NULL AND is_active = 1 AND is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_model_permissions_tenant_expires_at 
ON model_permissions(tenant_id, expires_at) 
INCLUDE (id, model_id, is_active) 
WHERE expires_at IS NOT NULL AND is_deleted = 0;
model_access_logs Table
SQL

-- Expect frequent inserts, FILLFACTOR can be adjusted based on insert patterns
CREATE NONCLUSTERED INDEX idx_model_access_logs_tenant_model_id_accessed_at 
ON model_access_logs(tenant_id, model_id, created_at DESC) -- BaseEntity.created_at is used as accessed_at
INCLUDE (user_id, access_type, access_result) 
WHERE is_deleted = 0
WITH (FILLFACTOR = 90);

CREATE NONCLUSTERED INDEX idx_model_access_logs_tenant_user_id_accessed_at 
ON model_access_logs(tenant_id, user_id, created_at DESC) 
INCLUDE (model_id, access_type, access_result) 
WHERE is_deleted = 0
WITH (FILLFACTOR = 90);

CREATE NONCLUSTERED INDEX idx_model_access_logs_tenant_accessed_at 
ON model_access_logs(tenant_id, created_at DESC) 
INCLUDE (model_id, user_id, access_type) 
WHERE is_deleted = 0
WITH (FILLFACTOR = 90);
Composite Indexes for Complex Queries
These are examples and should be tailored to specific, frequent, and complex query patterns.

SQL

-- Model discovery and access control, ensuring tenant scoping
CREATE NONCLUSTERED INDEX idx_models_tenant_user_access 
ON models(tenant_id, created_by_user_id, is_public) 
INCLUDE (name, source, organization_id, team_id, created_at) 
WHERE is_deleted = 0;

-- Cross-model component analysis (tenant-scoped)
CREATE NONCLUSTERED INDEX idx_resources_tenant_cross_model 
ON resources(tenant_id, name, capacity) 
INCLUDE (model_id, description) 
WHERE is_deleted = 0;

CREATE NONCLUSTERED INDEX idx_activities_tenant_cross_model 
ON activities(tenant_id, name, capacity) 
INCLUDE (model_id, description) 
WHERE is_deleted = 0;

-- Scenario execution pipeline (tenant-scoped)
CREATE NONCLUSTERED INDEX idx_scenarios_tenant_execution_pipeline 
ON scenarios(tenant_id, state, created_at) 
INCLUDE (id, analysis_id, reps, created_by_user_id) 
WHERE is_deleted = 0;

-- Model usage analytics (tenant-scoped)
CREATE NONCLUSTERED INDEX idx_scenarios_tenant_model_usage 
ON scenarios(tenant_id, created_at DESC) 
INCLUDE (analysis_id, created_by_user_id, state, execution_time_ms) 
WHERE is_deleted = 0;
Full-Text Search Indexes (Optional Enhancement)
Full-text search capabilities should be implemented considering tenant isolation. If using SQL Server Full-Text Search, queries would need to incorporate tenant_id filters.

SQL

/*
-- Example: Enable full-text search on model descriptions and names (tenant-aware)
-- Assumes full-text search is enabled on the database.

CREATE FULLTEXT CATALOG quodsi_fulltext_catalog;

-- The index would be on the base table. Queries using CONTAINS/FREETEXT
-- must then be combined with a WHERE clause for tenant_id.
CREATE FULLTEXT INDEX ON models(name LANGUAGE 1033, description LANGUAGE 1033) 
    KEY INDEX ix_models_id -- PK on models.id should be used if available and unique
    ON quodsi_fulltext_catalog
    WITH CHANGE_TRACKING AUTO;

-- Usage example:
-- SELECT * FROM models 
-- WHERE tenant_id = @CurrentTenantId 
--   AND CONTAINS((name, description), '"process optimization" OR "workflow"')
--   AND is_deleted = 0;
*/
Statistics and Maintenance
Automatic statistics handling by SQL Server will generally apply. For optimal performance in a multi-tenant system, ensure statistics are up-to-date, especially for columns like tenant_id and other frequently filtered columns.

MAINTENANCE RECOMMENDATIONS:

Index Maintenance Schedule:
Rebuild indexes with fragmentation > 30%.
Reorganize indexes with fragmentation 5-30%.
Update statistics regularly, especially after large data modifications within tenants.
Monitor Query Performance:
Use Query Store to identify expensive queries (filter by tenant or analyze across tenants carefully).
Monitor index usage (sys.dm_db_index_usage_stats).
Identify missing indexes (sys.dm_db_missing_index_details).
Archive Strategy:
Consider partitioning large tables by tenant_id or a combination including tenant_id and date.
Archive completed scenarios or old audit logs, ensuring tenant data is handled according to agreements.
SQL

/*
-- Check index fragmentation (can be run per database)
SELECT 
    OBJECT_SCHEMA_NAME(ips.object_id) as schema_name,
    OBJECT_NAME(ips.object_id) as table_name,
    i.name as index_name,
    ips.avg_fragmentation_in_percent,
    ips.page_count
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'SAMPLED') ips -- Use 'SAMPLED' or 'LIMITED' for faster results on large DBs
JOIN sys.indexes i ON ips.object_id = i.object_id AND ips.index_id = i.index_id
WHERE ips.avg_fragmentation_in_percent > 5
  AND ips.page_count > 100 -- Only for larger indexes
ORDER BY ips.avg_fragmentation_in_percent DESC;

-- Check index usage (can be run per database)
SELECT 
    OBJECT_SCHEMA_NAME(ius.object_id) as schema_name,
    OBJECT_NAME(ius.object_id) as table_name,
    i.name as index_name,
    ius.user_seeks,
    ius.user_scans,
    ius.user_lookups,
    ius.user_updates as total_writes,
    last_user_seek,
    last_user_scan,
    last_user_lookup
FROM sys.dm_db_index_usage_stats ius
JOIN sys.indexes i ON ius.object_id = i.object_id AND ius.index_id = i.index_id
WHERE ius.database_id = DB_ID()
  AND OBJECTPROPERTY(ius.object_id, 'IsUserTable') = 1
ORDER BY (ius.user_seeks + ius.user_scans + ius.user_lookups) DESC;
*/
Performance Monitoring Views (Tenant-Aware)
The original views need to be adapted to consider multi-tenancy. Queries within these views should generally be filtered by tenant_id or aggregate tenant data carefully.

SQL

/*
-- View for monitoring scenario execution performance (can be filtered by tenant_id when queried)
CREATE VIEW vw_scenario_performance_by_tenant AS
SELECT 
    m.tenant_id,
    m.name as model_name,
    a.name as analysis_name,
    s.id as scenario_id,
    s.name as scenario_name,
    s.execution_time_ms,
    s.state as scenario_status,
    s.completed_at
FROM scenarios s
JOIN analyses a ON s.analysis_id = a.id
JOIN models m ON a.model_id = m.id
WHERE s.is_deleted = 0 AND a.is_deleted = 0 AND m.is_deleted = 0;
-- Query example: SELECT * FROM vw_scenario_performance_by_tenant WHERE tenant_id = @SpecificTenantId AND completed_at > DATEADD(day, -30, GETDATE());

-- View for model access patterns (can be filtered by tenant_id when queried)
CREATE VIEW vw_model_access_summary_by_tenant AS
SELECT 
    m.tenant_id,
    m.name as model_name,
    m.source,
    mal.user_id,
    mal.access_type,
    mal.created_at as accessed_at -- BaseEntity.created_at used as accessed_at
FROM models m
JOIN model_access_logs mal ON m.id = mal.model_id
WHERE m.is_deleted = 0 AND mal.is_deleted = 0; 
-- Query example: 
-- SELECT tenant_id, model_name, COUNT(DISTINCT user_id) as unique_users, MAX(accessed_at) as last_accessed 
-- FROM vw_model_access_summary_by_tenant 
-- WHERE tenant_id = @SpecificTenantId AND accessed_at > DATEADD(day, -30, GETDATE())
-- GROUP BY tenant_id, model_name;
*/