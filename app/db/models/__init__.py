"""
Database models package.

All models inherit from BaseEntity which provides:
- Multi-tenant architecture with tenant_id foreign key
- Dual-key pattern (id + index_id) for performance optimization  
- Audit fields (created_at, updated_at, is_deleted) for tracking
- Consistent indexing strategy for tenant-scoped queries
- Soft delete functionality for data retention
"""

from .base_entity import BaseEntity

__all__ = ["BaseEntity"]