# Module 3.5: Database Structure Verification

**Duration:** 10-15 minutes  
**Objective:** Verify that the database structure matches BaseEntity specifications.

**Prerequisites:** Step 4 completed - BaseEntity functionality tests passed

---

## Step 5: Verify Database Structure

### 5.1 Check Table Structure in SQL Server
Connect to your SQL Server and run:

```sql
-- Check table structure
SELECT 
    c.COLUMN_NAME,
    c.DATA_TYPE,
    c.IS_NULLABLE,
    c.COLUMN_DEFAULT,
    c.CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS c
WHERE c.TABLE_NAME = 'test_models'
ORDER BY c.ORDINAL_POSITION;

-- Check indexes
SELECT 
    i.name AS index_name,
    i.type_desc,
    i.is_unique,
    i.is_primary_key,
    STRING_AGG(c.name, ', ') AS columns
FROM sys.indexes i
INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
INNER JOIN sys.tables t ON i.object_id = t.object_id
WHERE t.name = 'test_models'
GROUP BY i.name, i.type_desc, i.is_unique, i.is_primary_key
ORDER BY i.name;

-- Check foreign keys
SELECT 
    fk.name AS foreign_key_name,
    tp.name AS parent_table,
    cp.name AS parent_column,
    tr.name AS referenced_table,
    cr.name AS referenced_column
FROM sys.foreign_keys fk
INNER JOIN sys.tables tp ON fk.parent_object_id = tp.object_id
INNER JOIN sys.tables tr ON fk.referenced_object_id = tr.object_id
INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
INNER JOIN sys.columns cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
INNER JOIN sys.columns cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
WHERE tp.name = 'test_models';
```

### 5.2 Expected Results
You should see:
- **Columns:** `id`, `index_id`, `tenant_id`, `created_at`, `updated_at`, `is_deleted`, `name`, `description`
- **Indexes:** Clustered index on `index_id`, various filtered indexes for tenant queries
- **Foreign Key:** `tenant_id` referencing `tenants.id` (will fail until tenants table exists)

---

**✅ Checkpoint:** Database structure matches BaseEntity specifications.

**Next Step:** [035_Cleanup_and_Documentation.md](./035_Cleanup_and_Documentation.md)
