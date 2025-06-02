# app/services/model_service.py
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.models.simulation_model import Model
from app.repositories.model_repository import ModelRepository
from app.schemas.simulation_model import (
    ModelCreate,
    ModelUpdate,
    ModelCreateFromTemplate,
)


class ModelService:
    """Service layer for simulation model business logic"""

    def __init__(self):
        self.model_repository = ModelRepository()

    def create_model(
        self,
        db: Session,
        tenant_id: UUID,
        model_create: ModelCreate,
        current_user_id: UUID,
    ) -> Model:
        """
        Create a new simulation model with business logic and validation
        """
        # Check if model name already exists for this tenant
        existing_model = self.model_repository.get_latest_version_by_name(
            db, tenant_id, model_create.name
        )
        if existing_model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model with name '{model_create.name}' already exists",
            )

        # Create model data dictionary
        model_data = model_create.dict()
        model_data["tenant_id"] = tenant_id
        model_data["created_by_user_id"] = current_user_id
        model_data["version"] = 1  # Always start with version 1

        # Apply business rules for defaults
        if model_data.get("reps") is None:
            model_data["reps"] = 1

        if model_data.get("forecast_days") is None:
            model_data["forecast_days"] = 30

        if model_data.get("time_type") is None:
            model_data["time_type"] = "calendar"

        # Validate organization/team associations if provided
        if model_data.get("organization_id"):
            # TODO: Verify user has access to this organization
            # For now, we'll trust the input
            pass

        if model_data.get("team_id"):
            # TODO: Verify user has access to this team
            # For now, we'll trust the input
            pass

        # Create the model
        return self.model_repository.create(db, **model_data)

    def get_model_by_id(
        self,
        db: Session,
        tenant_id: UUID,
        model_id: UUID,
        load_relationships: bool = False,
    ) -> Optional[Model]:
        """Get a model by ID with optional relationship loading"""
        if load_relationships:
            return self.model_repository.get_with_relationships(db, tenant_id, model_id)
        else:
            return self.model_repository.get_by_id(db, tenant_id, model_id)

    def update_model(
        self,
        db: Session,
        tenant_id: UUID,
        model_id: UUID,
        model_update: ModelUpdate,
        current_user_id: UUID,
    ) -> Optional[Model]:
        """
        Update a model with permission checking and business logic
        """
        # Get existing model
        existing_model = self.model_repository.get_by_id(db, tenant_id, model_id)
        if not existing_model:
            return None

        # Check permissions - for now, only creator can update
        # TODO: Implement proper permission system
        if existing_model.created_by_user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the model creator can update this model",
            )

        # If name is being changed, check for conflicts
        if model_update.name and model_update.name != existing_model.name:
            existing_name_model = self.model_repository.get_latest_version_by_name(
                db, tenant_id, model_update.name
            )
            if existing_name_model and existing_name_model.id != model_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Model with name '{model_update.name}' already exists",
                )

        # Prepare update data (only include non-None values)
        update_data = {
            key: value
            for key, value in model_update.dict().items()
            if value is not None
        }

        # Business logic for certain updates
        if "is_template" in update_data and update_data["is_template"]:
            # When making a model a template, we might want to clear sensitive data
            # or apply template-specific logic
            pass

        # Increment version on significant changes
        significant_fields = {
            "source",
            "source_document_id",
            "reps",
            "forecast_days",
            "time_type",
            "one_clock_unit",
        }
        if any(field in update_data for field in significant_fields):
            update_data["version"] = existing_model.version + 1

        return self.model_repository.update(db, tenant_id, model_id, **update_data)

    def delete_model(
        self, db: Session, tenant_id: UUID, model_id: UUID, current_user_id: UUID
    ) -> bool:
        """
        Soft delete a model with permission checking
        """
        # Get existing model
        existing_model = self.model_repository.get_by_id(db, tenant_id, model_id)
        if not existing_model:
            return False

        # Check permissions - for now, only creator can delete
        # TODO: Implement proper permission system
        if existing_model.created_by_user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the model creator can delete this model",
            )

        # Perform soft delete
        return self.model_repository.delete(db, tenant_id, model_id)

    def list_models_for_tenant(
        self, db: Session, tenant_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Model]:
        """List all models for a tenant"""
        return self.model_repository.get_all(db, tenant_id, skip, limit)

    def list_models_for_user(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Model]:
        """List models created by a specific user"""
        return self.model_repository.get_models_by_user(
            db, tenant_id, user_id, skip, limit
        )

    def list_accessible_models(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Model]:
        """List models accessible to a user"""
        return self.model_repository.get_accessible_models(
            db, tenant_id, user_id, skip, limit
        )

    def search_models(
        self,
        db: Session,
        tenant_id: UUID,
        name_query: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Model]:
        """Search models by name"""
        return self.model_repository.search_models_by_name(
            db, tenant_id, name_query, skip, limit
        )

    def get_template_models(
        self,
        db: Session,
        tenant_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Model]:
        """Get template models"""
        return self.model_repository.get_template_models(db, tenant_id, skip, limit)

    def create_model_from_template(
        self,
        db: Session,
        tenant_id: UUID,
        template_model_id: UUID,
        template_create: ModelCreateFromTemplate,
        current_user_id: UUID,
    ) -> Model:
        """
        Create a new model based on an existing template
        """
        # Get the template model
        template_model = self.model_repository.get_by_id(
            db, tenant_id, template_model_id
        )
        if not template_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Template model not found"
            )

        if not template_model.is_template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Model is not a template",
            )

        # Check if name already exists
        existing_model = self.model_repository.get_latest_version_by_name(
            db, tenant_id, template_create.name
        )
        if existing_model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model with name '{template_create.name}' already exists",
            )

        # Create new model data based on template
        model_data = {
            # New model specific data
            "name": template_create.name,
            "description": template_create.description or template_model.description,
            "tenant_id": tenant_id,
            "created_by_user_id": current_user_id,
            "organization_id": template_create.organization_id,
            "team_id": template_create.team_id,
            "version": 1,
            # Copy template settings
            "source": template_model.source,
            "source_document_id": template_model.source_document_id,
            "source_url": template_model.source_url,
            "reps": template_model.reps,
            "forecast_days": template_model.forecast_days,
            "random_seed": template_model.random_seed,
            "time_type": template_model.time_type,
            "one_clock_unit": template_model.one_clock_unit,
            "warmup_clock_period": template_model.warmup_clock_period,
            "run_clock_period": template_model.run_clock_period,
            "warmup_date_time": template_model.warmup_date_time,
            "start_date_time": template_model.start_date_time,
            "finish_date_time": template_model.finish_date_time,
            # New model is not a template by default
            "is_template": False,
            "is_public": False,
        }

        return self.model_repository.create(db, **model_data)

    def get_models_by_source(
        self, db: Session, tenant_id: UUID, source: str, skip: int = 0, limit: int = 100
    ) -> List[Model]:
        """Get models by source type"""
        return self.model_repository.get_models_by_source(
            db, tenant_id, source, skip, limit
        )

    def get_models_by_organization(
        self,
        db: Session,
        tenant_id: UUID,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Model]:
        """Get models by organization"""
        return self.model_repository.get_models_by_organization(
            db, tenant_id, organization_id, skip, limit
        )

    def get_models_by_team(
        self,
        db: Session,
        tenant_id: UUID,
        team_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Model]:
        """Get models by team"""
        return self.model_repository.get_models_by_team(
            db, tenant_id, team_id, skip, limit
        )

    def get_user_model_count(self, db: Session, tenant_id: UUID, user_id: UUID) -> int:
        """Get count of models created by a user"""
        return self.model_repository.count_models_by_user(db, tenant_id, user_id)
