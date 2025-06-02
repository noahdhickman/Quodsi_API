# Module 3.3: BaseEntity Migration Testing

**Duration:** 15-20 minutes  
**Objective:** Test BaseEntity with Alembic migration to verify database schema generation.

**Prerequisites:** Step 2 completed - Test model created

---

## Step 3: Test BaseEntity with Alembic Migration

### 3.1 Generate Migration for Test Model
```bash
# Generate migration to test BaseEntity
alembic revision --autogenerate -m "test BaseEntity implementation"
```

### 3.2 Review Generated Migration
Open the generated migration file in `alembic/versions/` and verify it contains:

1. **Proper table structure:**
   - `id` as UNIQUEIDENTIFIER primary key
   - `index_id` as BIGINT with IDENTITY
   - `tenant_id` as UNIQUEIDENTIFIER with FK
   - `created_at`, `updated_at` as DATETIME2
   - `is_deleted` as BIT

2. **Correct indexes:**
   - Clustered index on `index_id`
   - Tenant-aware indexes
   - Filtered indexes with WHERE clauses

**⚠️ Important SQL Server Fix Required:**
Alembic's auto-generation may not properly handle the non-clustered primary key. You'll need to manually edit the migration file:

**Find this line:**
```python
sa.PrimaryKeyConstraint('id'),
```

**Change it to:**
```python
sa.PrimaryKeyConstraint('id', mssql_clustered=False),
```

**Why:** SQL Server creates clustered primary keys by default, but we want `index_id` to be the clustered index for performance. This manual edit ensures the primary key is non-clustered.

**Note:** This manual edit will be required for most migrations when using BaseEntity with SQL Server. This is normal and expected behavior.

### 3.3 Apply Migration
```bash
# Apply the migration to create test table
alembic upgrade head
```

**✅ Checkpoint:** Check your database - you should see a `test_models` table with BaseEntity structure.

---

## Troubleshooting

### Issue: "Cannot create more than one clustered index" Error
**Problem:** 
```
sqlalchemy.exc.ProgrammingError: Cannot create more than one clustered index on table 'test_models'. 
Drop the existing clustered index 'PK__test_mod__...' before creating another.
```

**Solution:**
1. The migration file needs manual editing (see section 3.2 above)
2. Ensure `sa.PrimaryKeyConstraint('id', mssql_clustered=False)` is in the migration
3. This tells SQL Server to create a non-clustered primary key
4. Allows `index_id` to be the clustered index for optimal performance

**This is expected behavior** when using advanced SQL Server indexing with SQLAlchemy/Alembic.

---

**Next Step:** [033_BaseEntity_Functionality_Testing.md](./033_BaseEntity_Functionality_Testing.md)
