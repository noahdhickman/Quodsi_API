# Step 4: Apply Migration and Verify

## 4.1 Apply Migration
```bash
# Apply the migration to create tenants table
alembic upgrade head
```

**✅ Checkpoint:** Migration should complete without errors.

## 4.2 Verify Database Structure
Connect to your SQL Server and check:

```sql
-- Check table exists and structure
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'tenants'
ORDER BY ORDINAL_POSITION;

-- Check indexes
SELECT 
    name AS index_name,
    type_desc,
    is_unique
FROM sys.indexes 
WHERE object_id = OBJECT_ID('tenants')
ORDER BY name;

-- Check constraints
SELECT 
    name AS constraint_name,
    type_desc
FROM sys.objects 
WHERE parent_object_id = OBJECT_ID('tenants')
AND type IN ('UQ', 'C', 'F')
ORDER BY name;
```

**✅ Checkpoint:** Verify all fields, indexes, and constraints exist.
