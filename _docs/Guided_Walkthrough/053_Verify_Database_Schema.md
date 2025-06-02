# Step 4: Verify Database Schema

## 4.1 Check Database Structure
Connect to your SQL Server database and verify the users table was created correctly:

```sql
-- Check table structure
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'users'
ORDER BY ORDINAL_POSITION;

-- Check indexes
SELECT 
    i.name AS index_name,
    i.type_desc AS index_type,
    i.is_unique,
    i.is_primary_key,
    STRING_AGG(c.name, ', ') AS columns
FROM sys.indexes i
INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE i.object_id = OBJECT_ID('users')
GROUP BY i.name, i.type_desc, i.is_unique, i.is_primary_key
ORDER BY i.name;

-- Check foreign key constraints
SELECT 
    fk.name AS constraint_name,
    OBJECT_NAME(fk.parent_object_id) AS table_name,
    c1.name AS column_name,
    OBJECT_NAME(fk.referenced_object_id) AS referenced_table,
    c2.name AS referenced_column
FROM sys.foreign_keys fk
INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
INNER JOIN sys.columns c1 ON fkc.parent_object_id = c1.object_id AND fkc.parent_column_id = c1.column_id
INNER JOIN sys.columns c2 ON fkc.referenced_object_id = c2.object_id AND fkc.referenced_column_id = c2.column_id
WHERE OBJECT_NAME(fk.parent_object_id) = 'users';

-- Check constraints (like check constraints)
SELECT 
    cc.name AS constraint_name,
    cc.definition
FROM sys.check_constraints cc
INNER JOIN sys.objects o ON cc.parent_object_id = o.object_id
WHERE o.name = 'users';
```

## 4.3 Expected Schema Verification Results

When you run the above SQL queries, you should see the following results:

### Table Structure (Expected Columns)
```
COLUMN_NAME              DATA_TYPE       IS_NULLABLE  COLUMN_DEFAULT
id                       uniqueidentifier NO          (newid())
index_id                 bigint          NO          NULL
tenant_id                uniqueidentifier NO          NULL
created_at              datetime        NO          (getdate())
updated_at              datetime        NO          (getdate())
is_deleted              bit             NO          ((0))
identity_provider       nvarchar        NO          NULL
identity_provider_id    nvarchar        NO          NULL
email                   nvarchar        NO          NULL
display_name            nvarchar        NO          NULL
last_login_at           datetime        YES         NULL
login_count             int             NO          ((0))
total_usage_minutes     int             NO          ((0))
last_session_start      datetime        YES         NULL
last_active_at          datetime        YES         NULL
status                  nvarchar        NO          ('active')
user_metadata           nvarchar        YES         NULL
```

### Indexes (Expected Results)
```
index_name                      index_type       is_unique  is_primary_key  columns
PK__users__[hash]              CLUSTERED        1          1               id
ix_users_index_id              CLUSTERED        1          0               index_id
ix_users_active                NONCLUSTERED     0          0               is_deleted
ix_users_tenant_active         NONCLUSTERED     0          0               tenant_id,is_deleted,index_id
ix_users_tenant_id_lookup      NONCLUSTERED     0          0               tenant_id,id
ix_users_tenant_email          NONCLUSTERED     1          0               tenant_id,email
ix_users_identity_provider     NONCLUSTERED     1          0               identity_provider,identity_provider_id
ix_users_tenant_status         NONCLUSTERED     0          0               tenant_id,status
ix_users_tenant_last_login     NONCLUSTERED     0          0               tenant_id,last_login_at
```

### Foreign Keys (Expected Results)
```
constraint_name        table_name  column_name  referenced_table  referenced_column
fk_users_tenant_id     users       tenant_id    tenants           id
```

### Check Constraints (Expected Results)
```
constraint_name              definition
ck_users_status             ([status]='active' OR [status]='invited' OR [status]='suspended' OR [status]='pending_verification')
ck_users_identity_provider  ([identity_provider]='entra_id' OR [identity_provider]='google' OR [identity_provider]='email' OR [identity_provider]='github')
```

## 4.4 SQL Server Performance Verification

Run these additional queries to verify SQL Server specific optimizations:

```sql
-- Verify clustered indexes (should show index_id as clustered, not id)
SELECT 
    i.name,
    i.type_desc,
    STRING_AGG(c.name, ', ') AS columns
FROM sys.indexes i
INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE i.object_id = OBJECT_ID('users') 
  AND i.type_desc IN ('CLUSTERED', 'NONCLUSTERED')
GROUP BY i.name, i.type_desc
ORDER BY i.type_desc, i.name;

-- Verify filtered indexes (indexes with WHERE clauses)
SELECT 
    i.name,
    i.has_filter,
    i.filter_definition
FROM sys.indexes i
WHERE i.object_id = OBJECT_ID('users')
  AND i.has_filter = 1;

-- Check execution plan for common query pattern
SET STATISTICS IO ON;
SELECT COUNT(*) 
FROM users 
WHERE tenant_id = NEWID() -- Use a random GUID
  AND is_deleted = 0;
SET STATISTICS IO OFF;
```

## 4.5 Test Data Relationships
Create a test script in the project root directory to verify the user-tenant relationship:

```python
# test_user_tenant_relationship.py
from app.db.session import SessionLocal
from app.db.models import Tenant, User
from uuid import uuid4
from datetime import datetime

def test_user_tenant_relationship():
    """Test User-Tenant relationship and verify database schema works correctly"""
    db = SessionLocal()
    try:
        print("🧪 Testing User-Tenant relationship...")
        
        # Create a test tenant
        test_tenant = Tenant(
            name="Test Company",
            subdomain="test-company",
            slug="test-company",
            plan_type="trial",
            status="trial"
        )
        db.add(test_tenant)
        db.flush()  # Get the ID without committing
        print(f"✅ Created test tenant: {test_tenant.name} (ID: {test_tenant.id})")
        
        # Create a test user
        test_user = User(
            tenant_id=test_tenant.id,
            identity_provider="entra_id",
            identity_provider_id=str(uuid4()),
            email="test@testcompany.com",
            display_name="Test User",
            status="active",
            user_metadata='{"department": "IT", "role": "admin"}'
        )
        db.add(test_user)
        db.commit()
        print(f"✅ Created test user: {test_user.email} (ID: {test_user.id})")
        
        # Test the relationship - user to tenant
        print(f"✅ User's tenant: {test_user.tenant.name}")
        assert test_user.tenant.id == test_tenant.id, "User-tenant relationship failed"
        
        # Test the relationship - tenant to users
        tenant_user_emails = [user.email for user in test_tenant.users]
        print(f"✅ Tenant's users: {tenant_user_emails}")
        assert test_user.email in tenant_user_emails, "Tenant-users relationship failed"
        
        # Test login stats update
        original_login_count = test_user.login_count
        test_user.update_login_stats()
        db.commit()
        
        print(f"✅ Login count: {original_login_count} → {test_user.login_count}")
        print(f"✅ Last login: {test_user.last_login_at}")
        print(f"✅ Last active: {test_user.last_active_at}")
        
        # Test activity update
        test_user.update_activity()
        db.commit()
        print(f"✅ Activity updated: {test_user.last_active_at}")
        
        # Test user metadata
        print(f"✅ User metadata: {test_user.user_metadata}")
        
        # Test BaseEntity fields
        print(f"✅ BaseEntity fields:")
        print(f"   - ID: {test_user.id}")
        print(f"   - Index ID: {test_user.index_id}")
        print(f"   - Tenant ID: {test_user.tenant_id}")
        print(f"   - Created: {test_user.created_at}")
        print(f"   - Updated: {test_user.updated_at}")
        print(f"   - Deleted: {test_user.is_deleted}")
        
        # Clean up
        db.delete(test_user)
        db.delete(test_tenant)
        db.commit()
        print("🧹 Cleaned up test data")
        
        print("\n🎉 All User-Tenant relationship tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_user_tenant_relationship()
    if not success:
        exit(1)
```

## 4.6 Troubleshooting Common Issues

### Missing Indexes
If any expected indexes are missing:
1. **Check the migration file** - ensure all indexes from the template were included
2. **Re-run the migration** - `alembic upgrade head`
3. **Manually create missing indexes** using the SQL from the migration template

### Foreign Key Constraint Errors
If the foreign key constraint is missing:
```sql
-- Manually add the foreign key constraint
ALTER TABLE users
ADD CONSTRAINT fk_users_tenant_id 
FOREIGN KEY (tenant_id) REFERENCES tenants(id);
```

### Performance Issues
If queries are slow:
1. **Verify clustered index** - `index_id` should be clustered, not `id`
2. **Check filtered indexes** - should have `is_deleted = 0` filters
3. **Use execution plans** - `SET STATISTICS IO ON` to analyze query performance

### Test Script Failures
If the relationship test fails:
1. **Check field names** - ensure using `user_metadata` not `metadata`
2. **Verify imports** - ensure all models import correctly
3. **Check database connection** - verify connection string and permissions

### Expected vs Actual Schema Differences
If your schema doesn't match the expected results:
1. **Column names** - verify `user_metadata` field exists
2. **Data types** - ensure UNIQUEIDENTIFIER for UUIDs
3. **Defaults** - check server defaults like `GETDATE()` and `NEWID()`
4. **Check constraints** - verify status and identity_provider constraints exist