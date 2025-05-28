from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from uuid import UUID
from app.db.models.base_entity import BaseEntity

# Generic type for SQLAlchemy models that inherit from BaseEntity
ModelType = TypeVar("ModelType", bound=BaseEntity)

class BaseRepository(Generic[ModelType]):
    """
    Base repository providing tenant-scoped CRUD operations.
    
    This generic repository automatically enforces tenant isolation
    for all database operations, ensuring multi-tenant data security.
    
    Type Parameters:
        ModelType: SQLAlchemy model class that inherits from BaseEntity
    
    Usage:
        class UserRepository(BaseRepository[User]):
            def __init__(self):
                super().__init__(User)
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        Initialize repository with a specific model type.
        
        Args:
            model: SQLAlchemy model class that inherits from BaseEntity
        """
        self.model = model
    
    def get_by_id(self, db: Session, tenant_id: UUID, id: UUID) -> Optional[ModelType]:
        """
        Get a single entity by UUID, scoped to tenant.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            id: Entity UUID to retrieve
            
        Returns:
            Entity instance or None if not found
            
        Example:
            user = user_repo.get_by_id(db, tenant_id, user_id)
        """
        return db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.id == id,
                self.model.is_deleted == False
            )
        ).first()
    
    def get_by_index_id(self, db: Session, tenant_id: UUID, index_id: int) -> Optional[ModelType]:
        """
        Get a single entity by index_id (clustered primary key), scoped to tenant.
        
        This is often more performant than UUID lookups due to clustered indexing.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            index_id: Entity index_id (auto-increment integer)
            
        Returns:
            Entity instance or None if not found
        """
        return db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.index_id == index_id,
                self.model.is_deleted == False
            )
        ).first()
    
    def get_all(self, db: Session, tenant_id: UUID, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get all entities for a tenant with pagination.
        
        Results are ordered by index_id (creation order) for consistent pagination.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            skip: Number of records to skip (pagination offset)
            limit: Maximum number of records to return
            
        Returns:
            List of entity instances
            
        Example:
            users = user_repo.get_all(db, tenant_id, skip=0, limit=50)
        """
        return db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.is_deleted == False
            )
        ).order_by(self.model.index_id).offset(skip).limit(limit).all()
    
    def count(self, db: Session, tenant_id: UUID) -> int:
        """
        Count all non-deleted entities for a tenant.
        
        Useful for pagination metadata and analytics.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            
        Returns:
            Number of entities
        """
        return db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.is_deleted == False
            )
        ).count()
    
    def create(self, db: Session, *, obj_in: Dict[str, Any], tenant_id: UUID) -> ModelType:
        """
        Create a new entity with automatic tenant assignment.
        
        The tenant_id is automatically set and cannot be overridden for security.
        Uses flush() instead of commit() to allow service-level transaction management.
        
        Args:
            db: Database session
            obj_in: Dictionary of field values for the new entity
            tenant_id: Tenant UUID (automatically assigned)
            
        Returns:
            Created entity instance
            
        Example:
            user_data = {"email": "user@example.com", "display_name": "User"}
            new_user = user_repo.create(db, obj_in=user_data, tenant_id=tenant_id)
        """
        # Ensure tenant_id is set and cannot be overridden
        obj_in = obj_in.copy()  # Don't mutate the original dict
        obj_in["tenant_id"] = tenant_id
        
        # Create the entity instance
        db_obj = self.model(**obj_in)
        
        # Add to session and flush to get the generated ID
        db.add(db_obj)
        db.flush()  # Flush to database without committing transaction
        db.refresh(db_obj)  # Refresh to get auto-generated fields
        
        return db_obj
    
    def update(self, db: Session, *, db_obj: ModelType, obj_in: Dict[str, Any]) -> ModelType:
        """
        Update an existing entity with new data.
        
        Automatically updates the updated_at timestamp and prevents
        modification of protected fields like id and tenant_id.
        
        Args:
            db: Database session
            db_obj: Existing entity instance to update
            obj_in: Dictionary of field values to update
            
        Returns:
            Updated entity instance
            
        Example:
            updated_user = user_repo.update(
                db, db_obj=user, obj_in={"display_name": "New Name"}
            )
        """
        from datetime import datetime, timezone
        
        # Update fields (excluding protected fields)
        protected_fields = {"id", "tenant_id", "index_id", "created_at"}
        
        for field, value in obj_in.items():
            if field not in protected_fields and hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        # Automatically update the timestamp
        db_obj.updated_at = datetime.now(timezone.utc)
        
        # Save changes
        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        
        return db_obj
    
    def soft_delete(self, db: Session, tenant_id: UUID, id: UUID) -> bool:
        """
        Soft delete an entity by setting is_deleted=True.
        
        Soft deletes preserve data for audit trails and potential recovery
        while removing entities from normal query results.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            id: Entity UUID to delete
            
        Returns:
            True if entity was found and deleted, False otherwise
            
        Example:
            deleted = user_repo.soft_delete(db, tenant_id, user_id)
        """
        from datetime import datetime, timezone
        
        db_obj = self.get_by_id(db, tenant_id, id)
        if db_obj:
            db_obj.is_deleted = True
            db_obj.updated_at = datetime.now(timezone.utc)
            db.add(db_obj)
            db.flush()
            return True
        return False
    
    def hard_delete(self, db: Session, tenant_id: UUID, id: UUID) -> bool:
        """
        Permanently delete an entity from the database.
        
        ⚠️  WARNING: This permanently removes data. Use with extreme caution.
        Typically only used for GDPR compliance or data cleanup operations.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            id: Entity UUID to delete
            
        Returns:
            True if entity was found and deleted, False otherwise
        """
        db_obj = self.get_by_id(db, tenant_id, id)
        if db_obj:
            db.delete(db_obj)
            db.flush()
            return True
        return False
    
    def search(self, db: Session, tenant_id: UUID, *, search_term: str, 
               search_fields: List[str], skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Search entities by term across specified fields.
        
        Performs case-insensitive LIKE searches across multiple fields
        using OR conditions (matches any field).
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            search_term: Term to search for
            search_fields: List of model field names to search in
            skip: Pagination offset
            limit: Maximum results to return
            
        Returns:
            List of matching entities
            
        Example:
            users = user_repo.search(
                db, tenant_id, 
                search_term="john", 
                search_fields=["email", "display_name"],
                limit=25
            )
        """
        # Handle empty search term
        if not search_term.strip():
            return self.get_all(db, tenant_id, skip=skip, limit=limit)
        
        # Build search conditions for each field
        search_conditions = []
        for field_name in search_fields:
            if hasattr(self.model, field_name):
                field_attr = getattr(self.model, field_name)
                # Use ilike for case-insensitive search
                search_conditions.append(field_attr.ilike(f"%{search_term}%"))
        
        # Return empty list if no valid fields found
        if not search_conditions:
            return []
        
        # Execute search query
        return db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.is_deleted == False,
                or_(*search_conditions)  # Match any of the search conditions
            )
        ).order_by(self.model.index_id).offset(skip).limit(limit).all()
    
    def get_recent(self, db: Session, tenant_id: UUID, *, days: int = 7, limit: int = 100) -> List[ModelType]:
        """
        Get recently created entities within the specified number of days.
        
        Useful for activity feeds, recent items lists, and analytics.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            days: Number of days back to search (default: 7)
            limit: Maximum results to return
            
        Returns:
            List of recent entities ordered by creation date (newest first)
        """
        from datetime import datetime, timezone, timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        return db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.is_deleted == False,
                self.model.created_at >= cutoff_date
            )
        ).order_by(self.model.created_at.desc()).limit(limit).all()
    
    def exists(self, db: Session, tenant_id: UUID, id: UUID) -> bool:
        """
        Check if an entity exists without loading the full object.
        
        More efficient than get_by_id() when you only need to verify existence.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            id: Entity UUID to check
            
        Returns:
            True if entity exists, False otherwise
        """
        return db.query(self.model.id).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.id == id,
                self.model.is_deleted == False
            )
        ).first() is not None