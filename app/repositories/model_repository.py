# app/repositories/model_repository.py
"""
Repository for Model (Simulation Model) entity with model-specific operations.

Provides tenant-scoped CRUD operations plus model-specific queries
for finding models by user, organization, team, source, and template status.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.repositories.base import BaseRepository
from app.db.models.simulation_model import Model


class ModelRepository(BaseRepository[Model]):
    """
    Repository for Model entity with model-specific operations.

    Provides tenant-scoped CRUD operations plus model-specific queries
    like finding models by source, user, organization, team, and template status.
    """

    def __init__(self):
        """Initialize ModelRepository with Model model."""
        super().__init__(Model)

    def get_models_by_user(
        self, db: Session, tenant_id: UUID, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Model]:
        """
        Get models created by a specific user within a tenant.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            user_id: User UUID who created the models
            skip: Pagination offset
            limit: Maximum results to return

        Returns:
            List of models created by the user
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.created_by_user_id == user_id,
                    self.model.is_deleted == False,
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_models_by_organization(
        self, db: Session, tenant_id: UUID, organization_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Model]:
        """
        Get models associated with a specific organization within a tenant.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            organization_id: Organization UUID
            skip: Pagination offset
            limit: Maximum results to return

        Returns:
            List of models associated with the organization
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.organization_id == organization_id,
                    self.model.is_deleted == False,
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_models_by_team(
        self, db: Session, tenant_id: UUID, team_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Model]:
        """
        Get models associated with a specific team within a tenant.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            team_id: Team UUID
            skip: Pagination offset
            limit: Maximum results to return

        Returns:
            List of models associated with the team
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.team_id == team_id,
                    self.model.is_deleted == False,
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_models_by_source(
        self, db: Session, tenant_id: UUID, source: str, skip: int = 0, limit: int = 100
    ) -> List[Model]:
        """
        Get models by source type within a tenant.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            source: Source type ('lucidchart', 'standalone', 'miro')
            skip: Pagination offset
            limit: Maximum results to return

        Returns:
            List of models from the specified source
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.source == source,
                    self.model.is_deleted == False,
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_template_models(
        self, db: Session, tenant_id: Optional[UUID] = None, skip: int = 0, limit: int = 100
    ) -> List[Model]:
        """
        Get template models. Can be tenant-specific or global.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation (None for global templates)
            skip: Pagination offset
            limit: Maximum results to return

        Returns:
            List of template models
        """
        query = db.query(self.model).filter(
            and_(
                self.model.is_template == True,
                self.model.is_deleted == False,
            )
        )
        
        # Add tenant filter if specified
        if tenant_id is not None:
            query = query.filter(self.model.tenant_id == tenant_id)
        
        return (
            query
            .order_by(self.model.name)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_public_models(
        self, db: Session, tenant_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Model]:
        """
        Get public models within a tenant.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            skip: Pagination offset
            limit: Maximum results to return

        Returns:
            List of public models
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.is_public == True,
                    self.model.is_deleted == False,
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_models_by_name(
        self, db: Session, tenant_id: UUID, name_query: str, skip: int = 0, limit: int = 100
    ) -> List[Model]:
        """
        Search models by name within a tenant using case-insensitive partial matching.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            name_query: Search term for model name
            skip: Pagination offset
            limit: Maximum results to return

        Returns:
            List of models matching the name query
        """
        return self.search(
            db=db,
            tenant_id=tenant_id,
            search_term=name_query,
            search_fields=["name", "description"],
            skip=skip,
            limit=limit,
        )

    def get_models_accessible_to_user(
        self, 
        db: Session, 
        tenant_id: UUID, 
        user_id: UUID, 
        organization_ids: Optional[List[UUID]] = None,
        team_ids: Optional[List[UUID]] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Model]:
        """
        Get models accessible to a user (created by them, their organizations, or teams).
        This method prepares for future permission system integration.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            user_id: User UUID
            organization_ids: List of organization IDs user belongs to
            team_ids: List of team IDs user belongs to
            skip: Pagination offset
            limit: Maximum results to return

        Returns:
            List of models accessible to the user
        """
        # Start with models created by the user
        conditions = [self.model.created_by_user_id == user_id]
        
        # Add public models in the tenant
        conditions.append(self.model.is_public == True)
        
        # Add models from user's organizations
        if organization_ids:
            conditions.append(self.model.organization_id.in_(organization_ids))
        
        # Add models from user's teams
        if team_ids:
            conditions.append(self.model.team_id.in_(team_ids))
        
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.is_deleted == False,
                    or_(*conditions)
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def check_name_exists(
        self, db: Session, tenant_id: UUID, name: str, exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if a model name already exists within a tenant.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            name: Model name to check
            exclude_id: Optional model ID to exclude (for updates)

        Returns:
            True if name exists, False otherwise
        """
        query = db.query(self.model.id).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.name == name,
                self.model.is_deleted == False,
            )
        )

        # Exclude current model when checking for updates
        if exclude_id:
            query = query.filter(self.model.id != exclude_id)

        return query.first() is not None

    def get_model_versions(
        self, db: Session, tenant_id: UUID, model_name: str
    ) -> List[Model]:
        """
        Get all versions of a model by name (for future versioning support).

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            model_name: Model name

        Returns:
            List of model versions ordered by version number
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.name == model_name,
                    self.model.is_deleted == False,
                )
            )
            .order_by(desc(self.model.version))
            .all()
        )

    def count_models_by_user(self, db: Session, tenant_id: UUID, user_id: UUID) -> int:
        """
        Count models created by a specific user.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            user_id: User UUID

        Returns:
            Count of models created by the user
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.created_by_user_id == user_id,
                    self.model.is_deleted == False,
                )
            )
            .count()
        )

    def count_models_by_source(self, db: Session, tenant_id: UUID, source: str) -> int:
        """
        Count models by source type within a tenant.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            source: Source type

        Returns:
            Count of models from the specified source
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.source == source,
                    self.model.is_deleted == False,
                )
            )
            .count()
        )