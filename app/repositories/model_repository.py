# app/repositories/model_repository.py
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from app.db.models.simulation_model import Model
from app.repositories.base import BaseRepository


class ModelRepository(BaseRepository[Model]):
    """Repository for simulation model data access operations"""

    def __init__(self):
        super().__init__(Model)

    def get_models_by_user(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Model]:
        """Get all models created by a specific user within a tenant"""
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.created_by_user_id == user_id,
                    self.model.is_deleted == False,
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_models_by_organization(
        self,
        db: Session,
        tenant_id: UUID,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Model]:
        """Get all models associated with a specific organization"""
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.organization_id == organization_id,
                    self.model.is_deleted == False,
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_models_by_team(
        self,
        db: Session,
        tenant_id: UUID,
        team_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Model]:
        """Get all models associated with a specific team"""
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.team_id == team_id,
                    self.model.is_deleted == False,
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_models_by_name(
        self,
        db: Session,
        tenant_id: UUID,
        name_query: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Model]:
        """Search models by name (case-insensitive partial match)"""
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.name.ilike(f"%{name_query}%"),
                    self.model.is_deleted == False,
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_template_models(
        self,
        db: Session,
        tenant_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Model]:
        """
        Get template models. If tenant_id is provided, get templates for that tenant.
        If None, get global/public templates.
        """
        query = db.query(self.model).filter(
            and_(self.model.is_template == True, self.model.is_deleted == False)
        )

        if tenant_id is not None:
            # Get templates for specific tenant or public templates
            query = query.filter(
                or_(self.model.tenant_id == tenant_id, self.model.is_public == True)
            )
        else:
            # Get only public templates
            query = query.filter(self.model.is_public == True)

        return query.offset(skip).limit(limit).all()

    def get_models_by_source(
        self, db: Session, tenant_id: UUID, source: str, skip: int = 0, limit: int = 100
    ) -> List[Model]:
        """Get models by source type (lucidchart, miro, manual, import)"""
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.source == source,
                    self.model.is_deleted == False,
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_accessible_models(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Model]:
        """
        Get models accessible to a user (created by them, public, or in their org/team).
        This is a simplified version - full permission logic would be more complex.
        """
        # TODO: This will need to be enhanced when proper permissions are implemented
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    or_(
                        self.model.created_by_user_id == user_id,  # User's own models
                        self.model.is_public == True,  # Public models
                        # Could add organization/team access logic here
                    ),
                    self.model.is_deleted == False,
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_with_relationships(
        self, db: Session, tenant_id: UUID, model_id: UUID
    ) -> Optional[Model]:
        """Get a model with all its relationships loaded"""
        return (
            db.query(self.model)
            .options(
                joinedload(self.model.created_by_user),
                joinedload(self.model.organization),
                joinedload(self.model.team),
            )
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.id == model_id,
                    self.model.is_deleted == False,
                )
            )
            .first()
        )

    def count_models_by_user(self, db: Session, tenant_id: UUID, user_id: UUID) -> int:
        """Count total models created by a user"""
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

    def get_latest_version_by_name(
        self, db: Session, tenant_id: UUID, name: str
    ) -> Optional[Model]:
        """Get the latest version of a model by name"""
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.name == name,
                    self.model.is_deleted == False,
                )
            )
            .order_by(self.model.version.desc())
            .first()
        )
