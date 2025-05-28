import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, DateTime, Boolean, BigInteger, Index, 
    ForeignKey, text as sa_text, UniqueConstraint, PrimaryKeyConstraint, Identity
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.ext.declarative import declared_attr
from app.db.session import Base

class BaseEntity(Base):
    """
    Abstract base class for all database entities in Quodsi.
    
    Provides:
    - Multi-tenant architecture with tenant_id
    - Dual-key pattern (id + index_id) for performance
    - Audit fields (created_at, updated_at, is_deleted)
    - Consistent indexing strategy
    """
    __abstract__ = True

    # Primary logical identifier (UUID)
    # Used for external references and API responses
    # Note: Primary key constraint defined in __table_args__ as non-clustered
    id = Column(
        UNIQUEIDENTIFIER, 
        default=uuid.uuid4, 
        nullable=False
    )
    
    # Physical ordering key (auto-incrementing integer)
    # Used as clustered index for optimal insert performance
    # Note: Using Identity for proper SQL Server IDENTITY column
    index_id = Column(
        BigInteger, 
        Identity(start=1, increment=1),
        unique=True, 
        nullable=False
    )

    @declared_attr
    def tenant_id(cls):
        """
        Multi-tenancy foreign key.
        Special handling for 'tenants' table which doesn't reference itself.
        """
        if cls.__tablename__ == 'tenants':
            # Tenants table has nullable tenant_id (for system tenants)
            return Column(
                UNIQUEIDENTIFIER, 
                nullable=True, 
                index=True,
                comment="Nullable for tenants table"
            )
        else:
            # All other tables have required tenant_id FK
            return Column(
                UNIQUEIDENTIFIER, 
                # ForeignKey(
                #     "tenants.id", 
                #     name=f"fk_{cls.__tablename__}_tenant_id"
                # ), 
                nullable=False, 
                index=True,
                comment="Multi-tenant isolation key"
            )

    # Audit timestamps
    created_at = Column(
        DateTime, 
        nullable=False, 
        default=lambda: datetime.now(timezone.utc),
        comment="Record creation timestamp"
    )
    
    updated_at = Column(
        DateTime, 
        nullable=False, 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Record last update timestamp"
    )
    
    # Soft delete flag
    is_deleted = Column(
        Boolean, 
        nullable=False, 
        default=False, 
        index=True,
        comment="Soft delete flag"
    )

    @declared_attr  # type: ignore
    def __table_args__(cls):
        """
        Define indexes and constraints for optimal performance.
        All tables get tenant-aware indexing strategy.
        SQL Server specific: PK on id (non-clustered), clustered index on index_id.
        """
        # Base table configuration and indexes
        args = [
            # Explicit primary key constraint (non-clustered)
            PrimaryKeyConstraint('id', mssql_clustered=False),
            # Clustered index on index_id for insert performance
            Index(
                f'ix_{cls.__tablename__}_index_id', 
                'index_id', 
                unique=True, 
                mssql_clustered=True
            ),
        ]
        
        # Add tenant-specific indexes for non-tenant tables
        if cls.__tablename__ != 'tenants':
            args.extend([
                # Most common query pattern: tenant + active records
                Index(
                    f'ix_{cls.__tablename__}_tenant_active', 
                    'tenant_id', 'is_deleted', 'index_id',
                    mssql_where=sa_text('is_deleted = 0')
                ),
                # Tenant + ID lookup pattern
                Index(
                    f'ix_{cls.__tablename__}_tenant_id_lookup',
                    'tenant_id', 'id',
                    mssql_where=sa_text('is_deleted = 0')
                ),
            ])
        else:
            # Special indexes for tenants table
            args.extend([
                # Active tenants lookup
                Index(
                    f'ix_{cls.__tablename__}_active', 
                    'is_deleted',
                    mssql_where=sa_text('is_deleted = 0')
                ),
            ])
        
        return tuple(args)

    def __repr__(self):
        """String representation for debugging"""
        tenant_info = getattr(self, 'tenant_id', 'N/A')
        return (
            f"<{self.__class__.__name__}("
            f"id={self.id}, "
            f"tenant_id={tenant_info}, "
            f"index_id={self.index_id}"
            f")>"
        )

    def soft_delete(self):
        """
        Mark record as deleted without removing from database.
        Note: Caller is responsible for committing the transaction.
        """
        self.is_deleted = True
        self.updated_at = datetime.now(timezone.utc)

    def restore(self):
        """
        Restore a soft-deleted record.
        Note: Caller is responsible for committing the transaction.
        """
        self.is_deleted = False
        self.updated_at = datetime.now(timezone.utc)

    @classmethod
    def get_active_query_filter(cls):
        """
        Get SQLAlchemy filter for active (non-deleted) records.
        Usage: query.filter(Model.get_active_query_filter())
        """
        return cls.is_deleted is False

    @classmethod
    def get_tenant_query_filter(cls, tenant_id):
        """
        Get SQLAlchemy filter for tenant-scoped records.
        Usage: query.filter(Model.get_tenant_query_filter(tenant_id))
        """
        if cls.__tablename__ == 'tenants':
            # For tenants table, filter by id instead of tenant_id
            return cls.id == tenant_id
        return cls.tenant_id == tenant_id

    @classmethod
    def get_active_tenant_filter(cls, tenant_id):
        """
        Get combined filter for active records within a tenant.
        Most common query pattern.
        """
        if cls.__tablename__ == 'tenants':
            return (cls.id == tenant_id) & (cls.is_deleted is False)
        return (cls.tenant_id == tenant_id) & (cls.is_deleted is False)