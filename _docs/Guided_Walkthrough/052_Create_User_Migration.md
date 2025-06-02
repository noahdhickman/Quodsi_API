# Step 3: Create User Migration

## 3.1 Generate the Migration
Run the Alembic command to generate the user migration:

```bash
# From your project root directory
alembic revision --autogenerate -m "Create users table"
```

## 3.2 Review and Edit the Migration
Open the generated migration file (e.g., `alembic/versions/xxxx_create_users_table.py`) and ensure it looks similar to this:

**⚠️ Important SQL Server Fixes Required:**
Just like with the Tenant migration, you'll need to manually edit the migration file:

1. **Primary key constraint**: Change `sa.PrimaryKeyConstraint('id')` to `sa.PrimaryKeyConstraint('id', mssql_clustered=False)`
2. **Add missing indexes**: Alembic may miss some critical BaseEntity indexes

```python
"""Create users table

Revision ID: xxxx
Revises: yyyy  # This should be the tenant migration ID
Create Date: 2025-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER

# revision identifiers
revision = 'xxxx'
down_revision = 'yyyy'  # Previous migration (tenants)
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        # BaseEntity fields
        sa.Column('id', UNIQUEIDENTIFIER, nullable=False, default=sa.text('NEWID()')),
        sa.Column('index_id', sa.BigInteger().with_variant(sa.Integer, "sqlite"), 
                 autoincrement=True, nullable=False),
        sa.Column('tenant_id', UNIQUEIDENTIFIER, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('GETDATE()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('GETDATE()')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        
        # User-specific fields
        sa.Column('identity_provider', sa.String(length=50), nullable=False),
        sa.Column('identity_provider_id', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('login_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('total_usage_minutes', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('last_session_start', sa.DateTime(), nullable=True),
        sa.Column('last_active_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default=sa.text("'active'")),
        sa.Column('user_metadata', sa.String(length=4000), nullable=True),
        
        # Primary key constraint (non-clustered)
        sa.PrimaryKeyConstraint('id', mssql_clustered=False),
        
        # Foreign key to tenants
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_users_tenant'),
        
        # Check constraints
        sa.CheckConstraint("status IN ('active', 'invited', 'suspended', 'pending_verification')", 
                          name='ck_users_status'),
        sa.CheckConstraint("identity_provider IN ('entra_id', 'google', 'email', 'github')", 
                          name='ck_users_identity_provider'),
    )
    
    # Create indexes
    # Critical missing indexes from BaseEntity - manually added
    # Clustered index on index_id for optimal insert performance  
    op.create_index(
        'ix_users_index_id',
        'users', 
        ['index_id'],
        unique=True,
        mssql_clustered=True
    )
    
    # Filtered index for active users (most common query pattern)
    op.create_index(
        'ix_users_active',
        'users',
        ['is_deleted'], 
        mssql_where='is_deleted = 0'
    )
    
    # BaseEntity indexes
    op.create_index('ix_users_tenant_active', 'users', ['tenant_id', 'is_deleted', 'index_id'], 
                   mssql_where='is_deleted = 0')
    op.create_index('ix_users_tenant_id_lookup', 'users', ['tenant_id', 'id'],
                   mssql_where='is_deleted = 0')
    
    # User-specific indexes
    op.create_index('ix_users_tenant_email', 'users', ['tenant_id', 'email'], unique=True,
                   mssql_where='is_deleted = 0')
    op.create_index('ix_users_identity_provider', 'users', ['identity_provider', 'identity_provider_id'], 
                   unique=True, mssql_where='is_deleted = 0')
    op.create_index('ix_users_tenant_status', 'users', ['tenant_id', 'status'], 
                   mssql_where='is_deleted = 0')
    op.create_index('ix_users_tenant_last_login', 'users', ['tenant_id', 'last_login_at'], 
                   mssql_where='is_deleted = 0')
    
    # Critical missing indexes from BaseEntity - manually added
    # Filtered index for active users (most common query pattern)
    op.create_index(
        'ix_users_active',
        'users',
        ['is_deleted'], 
        mssql_where='is_deleted = 0'
    )


def downgrade() -> None:
    # Drop indexes first (in reverse order of creation)
    # Drop user-specific indexes first
    op.drop_index('ix_users_tenant_last_login', table_name='users')
    op.drop_index('ix_users_tenant_status', table_name='users')
    op.drop_index('ix_users_identity_provider', table_name='users')
    op.drop_index('ix_users_tenant_email', table_name='users')
    
    # Drop BaseEntity indexes
    op.drop_index('ix_users_tenant_id_lookup', table_name='users')
    op.drop_index('ix_users_tenant_active', table_name='users')
    
    # Drop critical BaseEntity indexes
    op.drop_index('ix_users_active', table_name='users')
    op.drop_index('ix_users_index_id', table_name='users')
    
    # Drop table
    op.drop_table('users')
```

## 3.3 Run the Migration
Apply the migration to your database:

```bash
alembic upgrade head
```

## Troubleshooting

### Issue: "metadata" Reserved Attribute Error
If you encounter the error `Attribute name 'metadata' is reserved when using the Declarative API`, ensure you:

1. **Updated the User model** to use `user_metadata` instead of `metadata`
2. **Updated all Pydantic schemas** to use `user_metadata`
3. **Updated the migration** to create the column as `user_metadata`

### Issue: BaseEntity __table_args__ Errors
If you get errors related to BaseEntity's `__table_args__`, ensure you:

1. **Use `super().__table_args__`** instead of `BaseEntity.__table_args__.fget(cls)`
2. **Remove BaseEntity from `__all__`** in models `__init__.py` to prevent Alembic confusion

### Issue: Missing Critical Indexes
Alembic often misses the critical BaseEntity indexes. **Always manually add**:

1. **Clustered index on `index_id`** for optimal insert performance
2. **Filtered index on `is_deleted`** for active record queries
3. **Proper `mssql_where` filters** (not `postgresql_where`) for SQL Server

### Migration Generation Checklist
Before running `alembic revision --autogenerate`:

✅ User model uses `user_metadata` field name  
✅ User model `__table_args__` uses `super().__table_args__`  
✅ BaseEntity not exported in models `__all__` list  
✅ All imports work without circular dependencies

### Post-Generation Review Checklist
After generating the migration, **manually verify and add**:

✅ Clustered index on `index_id` with `mssql_clustered=True`  
✅ Filtered index on `is_deleted` with `mssql_where='is_deleted = 0'`  
✅ All filtered indexes use `mssql_where` (not `postgresql_where`)  
✅ Primary key constraint uses `mssql_clustered=False`