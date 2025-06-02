# Alembic SQL Server Migration Guide

This document outlines the specific requirements and patterns for creating database migrations in this project using SQL Server.

## Table Structure Requirements

All tables in this project follow a specific SQL Server indexing pattern for optimal performance:

### Required Column Structure
- **`id`** (UNIQUEIDENTIFIER) - **Primary Key, Non-Clustered**
- **`index_id`** (BIGINT IDENTITY) - **Clustered Index** (not primary key)
- **`tenant_id`** (UNIQUEIDENTIFIER) - **Multi-tenant isolation key**
- **`is_deleted`** (BIT) - **Soft delete flag**
- Standard audit fields: `created_at`, `updated_at`

### Why This Pattern?
- **Logical Primary Key**: `id` (GUID) provides globally unique identifiers for API operations
- **Physical Clustering**: `index_id` (auto-incrementing integer) provides optimal SQL Server performance
- **Best of Both Worlds**: Logical consistency + physical performance optimization

## Creating New Tables

### 1. Model Definition
When creating a new model, inherit from `BaseEntity`:

```python
from app.db.models.base_entity import BaseEntity

class YourNewModel(BaseEntity):
    __tablename__ = "your_table_name"
    
    # Your specific columns here
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    # etc.
```

The `BaseEntity` automatically provides:
- `id` (UNIQUEIDENTIFIER) 
- `index_id` (BIGINT IDENTITY)
- `tenant_id` (UNIQUEIDENTIFIER)
- `is_deleted` (BIT)
- `created_at` (DateTime)
- `updated_at` (DateTime)
- Proper clustering configuration and tenant-aware indexes

### 2. Generate Migration
```bash
alembic revision --autogenerate -m "Add your_table_name table"
```

### 3. Manual Edit Required
After generation, you **MUST** manually edit the migration file to add `mssql_clustered=False` to primary key constraints:

**Find lines like:**
```python
sa.PrimaryKeyConstraint('id'),
```

**Change to:**
```python
sa.PrimaryKeyConstraint('id', mssql_clustered=False),
```

This is required for **every table** in the migration.

### 4. Verify Migration Content
Your migration should contain:

```python
op.create_table('your_table_name',
    # Your columns...
    sa.Column('id', mssql.UNIQUEIDENTIFIER(), nullable=False),
    sa.Column('index_id', sa.BigInteger(), sa.Identity(always=False, start=1, increment=1), nullable=False),
    sa.Column('tenant_id', mssql.UNIQUEIDENTIFIER(), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('0')),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', mssql_clustered=False),  # ← Manual edit required
    sa.UniqueConstraint('index_id')
)
op.create_index('ix_your_table_name_index_id', 'your_table_name', ['index_id'], unique=True, mssql_clustered=True)
op.create_index('ix_your_table_name_tenant_active', 'your_table_name', ['tenant_id', 'is_deleted', 'index_id'])
```

### 5. Apply Migration
```bash
alembic upgrade head
```

## What This Creates in SQL Server

The above pattern generates SQL Server DDL equivalent to:

```sql
CREATE TABLE [your_table_name] (
    [id] UNIQUEIDENTIFIER NOT NULL,
    [index_id] BIGINT IDENTITY(1,1) NOT NULL,
    [tenant_id] UNIQUEIDENTIFIER NOT NULL,
    [is_deleted] BIT NOT NULL DEFAULT 0,
    [created_at] DATETIME NOT NULL,
    [updated_at] DATETIME NOT NULL,
    
    -- Non-clustered primary key on GUID
    CONSTRAINT [PK_your_table_name] PRIMARY KEY NONCLUSTERED ([id]),
    
    -- Unique constraint on identity column
    CONSTRAINT [UQ_your_table_name_index_id] UNIQUE ([index_id])
);

-- Clustered index on auto-incrementing identity
CREATE UNIQUE CLUSTERED INDEX [ix_your_table_name_index_id] 
ON [your_table_name] ([index_id]);

-- Tenant isolation index for common queries
CREATE INDEX [ix_your_table_name_tenant_active] 
ON [your_table_name] ([tenant_id], [is_deleted], [index_id]);
```

## Benefits of This Pattern

1. **Performance**: Clustered index on sequential integer provides optimal insert/scan performance
2. **API Consistency**: GUID primary keys provide stable, globally unique identifiers
3. **SQL Server Optimized**: Follows SQL Server best practices for OLTP workloads
4. **Replication Friendly**: GUIDs work well in distributed/replicated environments

## Common Mistakes to Avoid

❌ **Forgetting the manual edit** - Migration will fail with "Cannot create more than one clustered index"  
❌ **Making `index_id` the primary key** - Breaks the logical/physical separation pattern  
❌ **Using `autoincrement=True`** instead of `Identity()` - Won't generate proper SQL Server IDENTITY  
❌ **Not inheriting from BaseEntity** - Missing the required column structure  

## Troubleshooting

### "Cannot create more than one clustered index" Error
- You forgot to add `mssql_clustered=False` to the `PrimaryKeyConstraint`
- Edit the migration file and re-run

### Foreign Key References
- Always reference the `id` (GUID) column in foreign keys, not `index_id`
- Example: `organization_id = Column(UNIQUEIDENTIFIER, ForeignKey('organizations.id'))`
- Remember to include tenant isolation in multi-table queries

### Existing Tables
- If you have existing tables that don't follow this pattern, create a migration to add the missing `index_id` column and clustering