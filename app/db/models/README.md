# Database Models

This directory contains all SQLAlchemy database models for the Quodsi API.

## BaseEntity

All models inherit from `BaseEntity` which provides:

### Core Fields
- `id` (UNIQUEIDENTIFIER) - Primary key for external references
- `index_id` (BIGINT IDENTITY) - Clustered index for performance
- `tenant_id` (UNIQUEIDENTIFIER) - Multi-tenant isolation
- `created_at` (DATETIME2) - Creation timestamp
- `updated_at` (DATETIME2) - Last update timestamp  
- `is_deleted` (BIT) - Soft delete flag

### Key Features
- **Multi-tenancy**: Automatic tenant isolation
- **Performance**: Optimized indexing strategy
- **Audit Trail**: Creation and update tracking
- **Soft Deletes**: Data retention and recovery
- **Query Helpers**: Built-in filter methods

### Usage Examples

```python
# Create a new model
class MyModel(BaseEntity):
    __tablename__ = "my_models"
    name = Column(String(255), nullable=False)

# Query active records for a tenant
active_records = session.query(MyModel).filter(
    MyModel.get_active_tenant_filter(tenant_id)
).all()

# Soft delete a record
record.soft_delete()
session.commit()