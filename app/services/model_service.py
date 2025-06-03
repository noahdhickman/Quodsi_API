# app/services/model_service.py
"""
Service for Model (Simulation Model) business operations.

Handles model management, permission integration, version control,
template operations, and business logic enforcement while maintaining
proper separation from data access.

Key Responsibilities:
- Model CRUD operations with business validation
- Permission system integration (prepared for future implementation)
- Template model operations and copying
- Version management and conflict resolution
- Access logging and audit trail preparation
- Business rule enforcement for model data
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import Depends

from app.db.models.simulation_model import Model
from app.repositories.model_repository import ModelRepository
from app.repositories.user_repository import user_repo
from app.repositories.organization_repository import organization_repo
from app.repositories.tenant_repository import tenant_repo
from app.schemas.simulation_model import (
    ModelCreate,
    ModelUpdate,
    ModelRead,
    ModelSummary,
    ModelListResponse,
    ModelTemplateCreate,
    ModelPermissionContext,
    ModelAccessInfo,
)
from app.core.logging_config import get_logger
from app.db.session import get_db

logger = get_logger(__name__)


class ModelService:
    """
    Service for Model (Simulation Model) business operations.

    Handles model management, permission integration, version control,
    template operations, and business logic enforcement while maintaining
    proper separation from data access.
    """

    def __init__(self, db: Session):
        """
        Initialize service with database session.

        Args:
            db: Database session for all operations
        """
        self.db = db
        self.model_repo = ModelRepository()
        self.user_repo = user_repo
        self.organization_repo = organization_repo
        self.tenant_repo = tenant_repo

    # === Core CRUD Operations ===

    def create_model(
        self, tenant_id: UUID, user_id: UUID, model_data: ModelCreate
    ) -> ModelRead:
        """
        Create a new simulation model with business validation.

        Args:
            tenant_id: Tenant UUID for isolation
            user_id: User ID of the creator
            model_data: Model creation data

        Returns:
            Created model data

        Raises:
            ValueError: If validation fails or name already exists
            PermissionError: If user lacks permissions (future)

        Example:
            model_data = ModelCreate(name="My Model", source="lucidchart")
            new_model = service.create_model(tenant_id, user_id, model_data)
        """
        logger.info(
            "Creating new simulation model",
            extra={
                "extra_fields": {
                    "tenant_id": str(tenant_id),
                    "user_id": str(user_id),
                    "model_name": model_data.name,
                    "source": model_data.source,
                    "operation": "create_model",
                }
            },
        )

        try:
            # Validate model name uniqueness within tenant
            if self.model_repo.check_name_exists(self.db, tenant_id, model_data.name):
                raise ValueError(f"Model name '{model_data.name}' already exists")

            # Validate user exists and belongs to tenant
            user = self.user_repo.get_by_id(self.db, tenant_id, user_id)
            if not user:
                raise ValueError("User not found or not in tenant")

            # Validate organization and team associations if provided
            if model_data.organization_id:
                org = self.organization_repo.get_by_id(
                    self.db, tenant_id, model_data.organization_id
                )
                if not org:
                    raise ValueError("Associated organization not found")

            # Validate time configuration consistency
            self._validate_time_configuration(model_data)

            # Prepare creation data with required system fields
            create_data = model_data.model_dump(exclude_unset=True)
            create_data.update({
                "tenant_id": tenant_id,
                "created_by_user_id": user_id,
                "version": 1,  # Initial version
            })

            # Create the model
            new_model = self.model_repo.create(self.db, obj_in=create_data)
            self.db.commit()

            # TODO: Future - Log access for audit trail
            # self._log_model_access(tenant_id, user_id, new_model.id, "create")

            logger.info(
                "Simulation model created successfully",
                extra={
                    "extra_fields": {
                        "tenant_id": str(tenant_id),
                        "user_id": str(user_id),
                        "model_id": str(new_model.id),
                        "model_name": new_model.name,
                        "operation": "create_model",
                        "status": "success",
                    }
                },
            )

            return ModelRead.model_validate(new_model)

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Failed to create model: {str(e)}",
                exc_info=True,
                extra={
                    "extra_fields": {
                        "tenant_id": str(tenant_id),
                        "user_id": str(user_id),
                        "model_name": model_data.name,
                        "operation": "create_model",
                        "status": "failed",
                        "error_type": type(e).__name__,
                    }
                },
            )
            raise e

    def get_model(
        self, tenant_id: UUID, model_id: UUID, user_id: Optional[UUID] = None
    ) -> Optional[ModelRead]:
        """
        Get a model by ID with permission validation.

        Args:
            tenant_id: Tenant UUID for isolation
            model_id: Model UUID to retrieve
            user_id: Optional user ID for permission checking (future)

        Returns:
            Model data or None if not found/accessible

        Example:
            model = service.get_model(tenant_id, model_id, user_id)
        """
        model = self.model_repo.get_by_id(self.db, tenant_id, model_id)
        if not model:
            return None

        # TODO: Future - Check user permissions
        # if user_id and not self._check_model_permission(tenant_id, user_id, model_id, "read"):
        #     return None

        # TODO: Future - Log access for audit trail
        # if user_id:
        #     self._log_model_access(tenant_id, user_id, model_id, "read")

        return ModelRead.model_validate(model)

    def update_model(
        self, tenant_id: UUID, model_id: UUID, user_id: UUID, model_update: ModelUpdate
    ) -> Optional[ModelRead]:
        """
        Update a model with business validation and permission checking.

        Args:
            tenant_id: Tenant UUID for isolation
            model_id: Model UUID to update
            user_id: User ID performing the update
            model_update: Update data

        Returns:
            Updated model data or None if not found/accessible

        Raises:
            ValueError: If validation fails
            PermissionError: If user lacks permissions (future)
        """
        logger.info(
            "Updating simulation model",
            extra={
                "extra_fields": {
                    "tenant_id": str(tenant_id),
                    "user_id": str(user_id),
                    "model_id": str(model_id),
                    "operation": "update_model",
                }
            },
        )

        try:
            # Get existing model
            model = self.model_repo.get_by_id(self.db, tenant_id, model_id)
            if not model:
                return None

            # TODO: Future - Check user permissions
            # if not self._check_model_permission(tenant_id, user_id, model_id, "write"):
            #     raise PermissionError("User lacks permission to update this model")

            # Validate name uniqueness if name is being changed
            if model_update.name and model_update.name != model.name:
                if self.model_repo.check_name_exists(
                    self.db, tenant_id, model_update.name, exclude_id=model_id
                ):
                    raise ValueError(f"Model name '{model_update.name}' already exists")

            # Validate associations if being changed
            if model_update.organization_id:
                org = self.organization_repo.get_by_id(
                    self.db, tenant_id, model_update.organization_id
                )
                if not org:
                    raise ValueError("Associated organization not found")

            # Validate time configuration if being changed
            if any(
                getattr(model_update, field, None) is not None
                for field in [
                    "time_type",
                    "one_clock_unit",
                    "warmup_clock_period",
                    "run_clock_period",
                ]
            ):
                # Create a combined data object for validation
                combined_data = ModelCreate(
                    name=model.name,
                    source=model.source,
                    time_type=model_update.time_type or model.time_type,
                    one_clock_unit=model_update.one_clock_unit or model.one_clock_unit,
                    warmup_clock_period=model_update.warmup_clock_period or model.warmup_clock_period,
                    run_clock_period=model_update.run_clock_period or model.run_clock_period,
                )
                self._validate_time_configuration(combined_data)

            # Prepare update data
            update_data = model_update.model_dump(exclude_unset=True)

            # Update the model
            updated_model = self.model_repo.update(
                self.db, db_obj=model, obj_in=update_data
            )
            self.db.commit()

            # TODO: Future - Log access for audit trail
            # self._log_model_access(tenant_id, user_id, model_id, "update")

            logger.info(
                "Simulation model updated successfully",
                extra={
                    "extra_fields": {
                        "tenant_id": str(tenant_id),
                        "user_id": str(user_id),
                        "model_id": str(model_id),
                        "operation": "update_model",
                        "status": "success",
                    }
                },
            )

            return ModelRead.model_validate(updated_model)

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Failed to update model: {str(e)}",
                exc_info=True,
                extra={
                    "extra_fields": {
                        "tenant_id": str(tenant_id),
                        "user_id": str(user_id),
                        "model_id": str(model_id),
                        "operation": "update_model",
                        "status": "failed",
                        "error_type": type(e).__name__,
                    }
                },
            )
            raise e

    def delete_model(
        self, tenant_id: UUID, model_id: UUID, user_id: UUID
    ) -> bool:
        """
        Soft delete a model with permission validation.

        Args:
            tenant_id: Tenant UUID for isolation
            model_id: Model UUID to delete
            user_id: User ID performing the deletion

        Returns:
            True if deletion successful, False if model not found

        Raises:
            PermissionError: If user lacks permissions (future)
        """
        logger.info(
            "Deleting simulation model",
            extra={
                "extra_fields": {
                    "tenant_id": str(tenant_id),
                    "user_id": str(user_id),
                    "model_id": str(model_id),
                    "operation": "delete_model",
                }
            },
        )

        try:
            # Get existing model
            model = self.model_repo.get_by_id(self.db, tenant_id, model_id)
            if not model:
                return False

            # TODO: Future - Check user permissions
            # if not self._check_model_permission(tenant_id, user_id, model_id, "admin"):
            #     raise PermissionError("User lacks permission to delete this model")

            # Soft delete the model
            self.model_repo.remove(self.db, id=model_id)
            self.db.commit()

            # TODO: Future - Log access for audit trail
            # self._log_model_access(tenant_id, user_id, model_id, "delete")

            logger.info(
                "Simulation model deleted successfully",
                extra={
                    "extra_fields": {
                        "tenant_id": str(tenant_id),
                        "user_id": str(user_id),
                        "model_id": str(model_id),
                        "operation": "delete_model",
                        "status": "success",
                    }
                },
            )

            return True

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Failed to delete model: {str(e)}",
                exc_info=True,
                extra={
                    "extra_fields": {
                        "tenant_id": str(tenant_id),
                        "user_id": str(user_id),
                        "model_id": str(model_id),
                        "operation": "delete_model",
                        "status": "failed",
                        "error_type": type(e).__name__,
                    }
                },
            )
            raise e

    # === Query Operations ===

    def list_models(
        self,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        team_id: Optional[UUID] = None,
        source: Optional[str] = None,
        is_template: Optional[bool] = None,
        is_public: Optional[bool] = None,
        search_query: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> ModelListResponse:
        """
        List models with filtering and permission validation.

        Args:
            tenant_id: Tenant UUID for isolation
            user_id: Optional user ID for filtering by creator
            organization_id: Optional organization filter
            team_id: Optional team filter
            source: Optional source filter ('lucidchart', 'standalone', 'miro')
            is_template: Optional template filter
            is_public: Optional public filter
            search_query: Optional search term for name/description
            skip: Pagination offset
            limit: Maximum results to return

        Returns:
            Paginated list of models

        Example:
            models = service.list_models(tenant_id, user_id=user_id, limit=50)
        """
        models = []

        # Apply specific filtering based on parameters
        if user_id:
            models = self.model_repo.get_models_by_user(
                self.db, tenant_id, user_id, skip, limit
            )
        elif organization_id:
            models = self.model_repo.get_models_by_organization(
                self.db, tenant_id, organization_id, skip, limit
            )
        elif team_id:
            models = self.model_repo.get_models_by_team(
                self.db, tenant_id, team_id, skip, limit
            )
        elif source:
            models = self.model_repo.get_models_by_source(
                self.db, tenant_id, source, skip, limit
            )
        elif is_template is True:
            models = self.model_repo.get_template_models(
                self.db, tenant_id, skip, limit
            )
        elif is_public is True:
            models = self.model_repo.get_public_models(
                self.db, tenant_id, skip, limit
            )
        elif search_query:
            models = self.model_repo.search_models_by_name(
                self.db, tenant_id, search_query, skip, limit
            )
        else:
            models = self.model_repo.get_all(self.db, tenant_id, skip=skip, limit=limit)

        # TODO: Future - Filter based on user permissions
        # if requesting_user_id:
        #     models = self._filter_accessible_models(tenant_id, requesting_user_id, models)

        # Get total count for pagination
        total = self.model_repo.count(self.db, tenant_id)

        # Convert to summary format
        model_summaries = [ModelSummary.model_validate(model) for model in models]

        return ModelListResponse(
            models=model_summaries,
            total=total,
            skip=skip,
            limit=limit,
        )

    def get_accessible_models(
        self,
        tenant_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> ModelListResponse:
        """
        Get models accessible to a specific user.

        Args:
            tenant_id: Tenant UUID for isolation
            user_id: User UUID to check access for
            skip: Pagination offset
            limit: Maximum results to return

        Returns:
            Paginated list of accessible models
        """
        # TODO: Future - Get user's organization and team memberships
        # organization_ids = self._get_user_organization_ids(tenant_id, user_id)
        # team_ids = self._get_user_team_ids(tenant_id, user_id)

        # For now, use basic access logic (creator + public models)
        models = self.model_repo.get_models_accessible_to_user(
            self.db,
            tenant_id,
            user_id,
            organization_ids=None,  # TODO: Pass actual org IDs
            team_ids=None,  # TODO: Pass actual team IDs
            skip=skip,
            limit=limit,
        )

        total = len(models)  # TODO: Implement proper count with permissions
        model_summaries = [ModelSummary.model_validate(model) for model in models]

        return ModelListResponse(
            models=model_summaries,
            total=total,
            skip=skip,
            limit=limit,
        )

    # === Template Operations ===

    def create_from_template(
        self,
        tenant_id: UUID,
        user_id: UUID,
        template_request: ModelTemplateCreate,
    ) -> ModelRead:
        """
        Create a new model from an existing template.

        Args:
            tenant_id: Tenant UUID for isolation
            user_id: User ID creating the new model
            template_request: Template creation request

        Returns:
            Newly created model data

        Raises:
            ValueError: If template not found or validation fails
            PermissionError: If user lacks permissions (future)
        """
        logger.info(
            "Creating model from template",
            extra={
                "extra_fields": {
                    "tenant_id": str(tenant_id),
                    "user_id": str(user_id),
                    "template_id": str(template_request.template_model_id),
                    "new_name": template_request.new_model_name,
                    "operation": "create_from_template",
                }
            },
        )

        try:
            # Get template model
            template_model = self.model_repo.get_by_id(
                self.db, tenant_id, template_request.template_model_id
            )
            if not template_model or not template_model.is_template:
                raise ValueError("Template model not found or not marked as template")

            # TODO: Future - Check user permissions for template
            # if not self._check_model_permission(tenant_id, user_id, template_model.id, "read"):
            #     raise PermissionError("User lacks permission to use this template")

            # Validate new model name uniqueness
            if self.model_repo.check_name_exists(
                self.db, tenant_id, template_request.new_model_name
            ):
                raise ValueError(
                    f"Model name '{template_request.new_model_name}' already exists"
                )

            # Copy template data to new model
            new_model_data = ModelCreate(
                name=template_request.new_model_name,
                description=template_request.description or template_model.description,
                source=template_model.source,
                source_document_id=None,  # Clear source references for copies
                source_url=None,
                reps=template_model.reps,
                forecast_days=template_model.forecast_days,
                random_seed=template_model.random_seed,
                time_type=template_model.time_type,
                one_clock_unit=template_model.one_clock_unit,
                warmup_clock_period=template_model.warmup_clock_period,
                run_clock_period=template_model.run_clock_period,
                warmup_date_time=template_model.warmup_date_time,
                start_date_time=template_model.start_date_time,
                finish_date_time=template_model.finish_date_time,
                organization_id=template_request.organization_id,
                team_id=template_request.team_id,
                is_public=False,  # New models are private by default
                is_template=False,  # New models are not templates by default
            )

            # Create the new model
            new_model = self.create_model(tenant_id, user_id, new_model_data)

            logger.info(
                "Model created from template successfully",
                extra={
                    "extra_fields": {
                        "tenant_id": str(tenant_id),
                        "user_id": str(user_id),
                        "template_id": str(template_request.template_model_id),
                        "new_model_id": str(new_model.id),
                        "operation": "create_from_template",
                        "status": "success",
                    }
                },
            )

            return new_model

        except Exception as e:
            logger.error(
                f"Failed to create model from template: {str(e)}",
                exc_info=True,
                extra={
                    "extra_fields": {
                        "tenant_id": str(tenant_id),
                        "user_id": str(user_id),
                        "template_id": str(template_request.template_model_id),
                        "operation": "create_from_template",
                        "status": "failed",
                        "error_type": type(e).__name__,
                    }
                },
            )
            raise e

    def get_template_models(
        self, tenant_id: Optional[UUID] = None, skip: int = 0, limit: int = 100
    ) -> ModelListResponse:
        """
        Get available template models.

        Args:
            tenant_id: Optional tenant UUID (None for global templates)
            skip: Pagination offset
            limit: Maximum results to return

        Returns:
            Paginated list of template models
        """
        models = self.model_repo.get_template_models(self.db, tenant_id, skip, limit)
        model_summaries = [ModelSummary.model_validate(model) for model in models]

        # TODO: Implement proper count for templates
        total = len(models)

        return ModelListResponse(
            models=model_summaries,
            total=total,
            skip=skip,
            limit=limit,
        )

    # === Analytics and Statistics ===

    def get_model_statistics(self, tenant_id: UUID) -> Dict[str, Any]:
        """
        Get model statistics for a tenant.

        Args:
            tenant_id: Tenant UUID for isolation

        Returns:
            Dictionary with model statistics
        """
        try:
            total_models = self.model_repo.count(self.db, tenant_id)

            # Count by source
            source_counts = {}
            for source in ["lucidchart", "standalone", "miro"]:
                count = self.model_repo.count_models_by_source(
                    self.db, tenant_id, source
                )
                source_counts[source] = count

            # TODO: Add more analytics
            # - Models created per month
            # - Template usage statistics
            # - Most active model creators

            return {
                "total_models": total_models,
                "source_distribution": source_counts,
                "analysis_date": datetime.now(timezone.utc).isoformat(),
            }

        except Exception:
            return {
                "total_models": 0,
                "source_distribution": {"lucidchart": 0, "standalone": 0, "miro": 0},
                "analysis_date": datetime.now(timezone.utc).isoformat(),
            }

    # === Business Validation Methods ===

    def _validate_time_configuration(self, model_data: ModelCreate) -> None:
        """
        Validate time configuration consistency.

        Args:
            model_data: Model data to validate

        Raises:
            ValueError: If time configuration is invalid
        """
        if model_data.time_type == "clock":
            # Clock mode validation
            if model_data.one_clock_unit is None:
                raise ValueError("Clock unit is required for clock mode")

            # Check that calendar fields are not set in clock mode
            if any([
                model_data.warmup_date_time,
                model_data.start_date_time,
                model_data.finish_date_time,
            ]):
                raise ValueError("Calendar fields cannot be set in clock mode")

        elif model_data.time_type == "calendar":
            # Calendar mode validation
            if model_data.one_clock_unit is not None:
                raise ValueError("Clock unit cannot be set in calendar mode")

            # Check that clock period fields are not set in calendar mode
            if any([
                model_data.warmup_clock_period,
                model_data.run_clock_period,
            ]):
                raise ValueError("Clock period fields cannot be set in calendar mode")

    # === Future Permission System Integration ===
    # These methods are placeholders for future permission system integration

    def _check_model_permission(
        self, tenant_id: UUID, user_id: UUID, model_id: UUID, permission: str
    ) -> bool:
        """
        Check if user has permission for a model (future implementation).

        Args:
            tenant_id: Tenant UUID for isolation
            user_id: User UUID to check
            model_id: Model UUID to check access for
            permission: Permission type ('read', 'write', 'execute', 'admin')

        Returns:
            True if user has permission, False otherwise
        """
        # TODO: Implement actual permission checking
        # This would integrate with the future ModelPermissionService
        return True

    def _log_model_access(
        self, tenant_id: UUID, user_id: UUID, model_id: UUID, action: str
    ) -> None:
        """
        Log model access for audit trail (future implementation).

        Args:
            tenant_id: Tenant UUID for isolation
            user_id: User UUID performing action
            model_id: Model UUID being accessed
            action: Action type ('create', 'read', 'update', 'delete', 'execute')
        """
        # TODO: Implement actual access logging
        # This would create entries in the ModelAccessLog table
        pass

    def _get_user_organization_ids(self, tenant_id: UUID, user_id: UUID) -> List[UUID]:
        """
        Get organization IDs that a user belongs to (future implementation).

        Args:
            tenant_id: Tenant UUID for isolation
            user_id: User UUID to check

        Returns:
            List of organization UUIDs
        """
        # TODO: Implement organization membership lookup
        return []

    def _get_user_team_ids(self, tenant_id: UUID, user_id: UUID) -> List[UUID]:
        """
        Get team IDs that a user belongs to (future implementation).

        Args:
            tenant_id: Tenant UUID for isolation
            user_id: User UUID to check

        Returns:
            List of team UUIDs
        """
        # TODO: Implement team membership lookup
        return []


# Dependency injection helper for FastAPI
def get_model_service(db: Session = Depends(get_db)) -> ModelService:
    """
    Dependency injection helper for FastAPI endpoints.

    Usage in FastAPI:
        @router.post("/models")
        async def create_model(
            model_data: ModelCreate,
            current_user: User = Depends(get_current_user),
            model_service: ModelService = Depends(get_model_service)
        ):
            return model_service.create_model(current_user.tenant_id, current_user.id, model_data)
    """
    return ModelService(db)