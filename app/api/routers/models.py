# app/api/routers/models.py
"""
FastAPI router for Model (Simulation Model) management endpoints.

Provides REST API endpoints for creating, reading, updating, and deleting
simulation models with proper error handling, logging, and tenant isolation.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Path
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.services.model_service import ModelService, get_model_service
from app.schemas.simulation_model import (
    ModelCreate,
    ModelUpdate,
    ModelRead,
    ModelSummary,
    ModelListResponse,
    ModelTemplateCreate,
)
from app.api.response_helpers import create_success_response, create_error_response
from app.api.deps import (
    get_current_user_mock,
    get_current_user_from_db,
    MockCurrentUser,
)
from app.db.models.user import User
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/models", tags=["models"])


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_model(
    request: Request,
    model_data: ModelCreate,
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    model_service: ModelService = Depends(get_model_service),
):
    """
    Create a new simulation model.

    Creates a new simulation model with the provided configuration.
    Model names must be unique within a tenant.

    Args:
        model_data: Model creation data including name, source, and configuration
        current_user: Authenticated user context
        model_service: Model service instance

    Returns:
        Created model data with success response

    Raises:
        400: Validation error or name conflict
        500: Internal server error
    """
    # Get request ID from middleware
    request_id = getattr(request.state, "request_id", "unknown")

    # Log request entry with context
    logger.info(
        "Model creation request received",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "user_id": str(current_user.user_id),
                "tenant_id": str(current_user.tenant_id),
                "model_name": model_data.name,
                "source": model_data.source,
                "endpoint": "/models/",
                "method": "POST",
            }
        },
    )

    try:
        # Create the model
        new_model = model_service.create_model(
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id,
            model_data=model_data,
        )

        # Log successful completion
        logger.info(
            "Model created successfully",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "model_id": str(new_model.id),
                    "model_name": new_model.name,
                    "endpoint": "/models/",
                    "status": "success",
                }
            },
        )

        return create_success_response(
            data={
                **new_model.model_dump(mode='json'),
                "message": "Model created successfully",
            },
            tenant_id=current_user.tenant_id,
        )

    except ValueError as e:
        # Business logic errors (validation, duplicates, etc.)
        logger.warning(
            f"Model creation validation error: {str(e)}",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "model_name": model_data.name,
                    "error": str(e),
                    "endpoint": "/models/",
                    "status": "validation_error",
                }
            },
        )

        return create_error_response(
            message=str(e),
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"field_errors": {"name": [str(e)]}},
            tenant_id=current_user.tenant_id,
        )

    except Exception as e:
        # Unexpected errors
        logger.error(
            f"Unexpected error during model creation: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "model_name": model_data.name,
                    "error_type": type(e).__name__,
                    "endpoint": "/models/",
                    "status": "error",
                }
            },
        )

        return create_error_response(
            message="Failed to create model",
            error_code="INTERNAL_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            tenant_id=current_user.tenant_id,
        )


@router.get("/", response_model=dict)
async def list_models(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    user_id: Optional[UUID] = Query(None, description="Filter by creator"),
    organization_id: Optional[UUID] = Query(None, description="Filter by organization"),
    team_id: Optional[UUID] = Query(None, description="Filter by team"),
    source: Optional[str] = Query(None, description="Filter by source type"),
    is_template: Optional[bool] = Query(None, description="Filter by template status"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    search: Optional[str] = Query(None, description="Search by name/description"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    model_service: ModelService = Depends(get_model_service),
):
    """
    List simulation models with filtering and pagination.

    Returns a paginated list of models accessible to the current user.
    Various filters can be applied to narrow down the results.

    Args:
        skip: Pagination offset
        limit: Maximum results to return
        user_id: Filter by creator user ID
        organization_id: Filter by organization ID
        team_id: Filter by team ID
        source: Filter by source type
        is_template: Filter by template status
        is_public: Filter by public status
        search: Search term for name/description
        current_user: Authenticated user context
        model_service: Model service instance

    Returns:
        Paginated list of models with metadata

    Raises:
        500: Internal server error
    """
    # Get request ID from middleware
    request_id = getattr(request.state, "request_id", "unknown")

    # Log request entry
    logger.info(
        "Model list request received",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "user_id": str(current_user.user_id),
                "tenant_id": str(current_user.tenant_id),
                "skip": skip,
                "limit": limit,
                "filters": {
                    "user_id": str(user_id) if user_id else None,
                    "organization_id": str(organization_id) if organization_id else None,
                    "team_id": str(team_id) if team_id else None,
                    "source": source,
                    "is_template": is_template,
                    "is_public": is_public,
                    "search": search,
                },
                "endpoint": "/models/",
                "method": "GET",
            }
        },
    )

    try:
        # Get models with applied filters
        models_response = model_service.list_models(
            tenant_id=current_user.tenant_id,
            user_id=user_id,
            organization_id=organization_id,
            team_id=team_id,
            source=source,
            is_template=is_template,
            is_public=is_public,
            search_query=search,
            skip=skip,
            limit=limit,
        )

        # Log successful completion
        logger.info(
            "Models retrieved successfully",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "results_count": len(models_response.models),
                    "total_count": models_response.total,
                    "endpoint": "/models/",
                    "status": "success",
                }
            },
        )

        return create_success_response(
            data=models_response.model_dump(mode='json'),
            tenant_id=current_user.tenant_id,
        )

    except Exception as e:
        # Unexpected errors
        logger.error(
            f"Unexpected error during model listing: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "error_type": type(e).__name__,
                    "endpoint": "/models/",
                    "status": "error",
                }
            },
        )

        return create_error_response(
            message="Failed to retrieve models",
            error_code="INTERNAL_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            tenant_id=current_user.tenant_id,
        )


@router.get("/{model_id}", response_model=dict)
async def get_model(
    request: Request,
    model_id: UUID = Path(..., description="Model ID"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    model_service: ModelService = Depends(get_model_service),
):
    """
    Get details of a specific simulation model.

    Retrieves complete information about a simulation model including
    all configuration parameters and metadata.

    Args:
        model_id: UUID of the model to retrieve
        current_user: Authenticated user context
        model_service: Model service instance

    Returns:
        Complete model data

    Raises:
        404: Model not found
        500: Internal server error
    """
    # Get request ID from middleware
    request_id = getattr(request.state, "request_id", "unknown")

    # Log request entry
    logger.info(
        "Model retrieval request received",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "user_id": str(current_user.user_id),
                "tenant_id": str(current_user.tenant_id),
                "model_id": str(model_id),
                "endpoint": f"/models/{model_id}",
                "method": "GET",
            }
        },
    )

    try:
        # Get the model
        model = model_service.get_model(
            tenant_id=current_user.tenant_id,
            model_id=model_id,
            user_id=current_user.user_id,
        )

        if not model:
            logger.warning(
                "Model not found",
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "user_id": str(current_user.user_id),
                        "tenant_id": str(current_user.tenant_id),
                        "model_id": str(model_id),
                        "endpoint": f"/models/{model_id}",
                        "status": "not_found",
                    }
                },
            )

            return create_error_response(
                message="Model not found",
                error_code="NOT_FOUND",
                status_code=status.HTTP_404_NOT_FOUND,
                tenant_id=current_user.tenant_id,
            )

        # Log successful completion
        logger.info(
            "Model retrieved successfully",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "model_id": str(model_id),
                    "model_name": model.name,
                    "endpoint": f"/models/{model_id}",
                    "status": "success",
                }
            },
        )

        return create_success_response(
            data=model.model_dump(mode='json'),
            tenant_id=current_user.tenant_id,
        )

    except Exception as e:
        # Unexpected errors
        logger.error(
            f"Unexpected error during model retrieval: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "model_id": str(model_id),
                    "error_type": type(e).__name__,
                    "endpoint": f"/models/{model_id}",
                    "status": "error",
                }
            },
        )

        return create_error_response(
            message="Failed to retrieve model",
            error_code="INTERNAL_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            tenant_id=current_user.tenant_id,
        )


@router.put("/{model_id}", response_model=dict)
async def update_model(
    request: Request,
    model_id: UUID = Path(..., description="Model ID"),
    model_update: ModelUpdate = ...,
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    model_service: ModelService = Depends(get_model_service),
):
    """
    Update a simulation model.

    Updates the specified model with new configuration data.
    Only certain fields can be updated, and validation is applied.

    Args:
        model_id: UUID of the model to update
        model_update: Update data
        current_user: Authenticated user context
        model_service: Model service instance

    Returns:
        Updated model data

    Raises:
        400: Validation error
        404: Model not found
        500: Internal server error
    """
    # Get request ID from middleware
    request_id = getattr(request.state, "request_id", "unknown")

    # Log request entry
    logger.info(
        "Model update request received",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "user_id": str(current_user.user_id),
                "tenant_id": str(current_user.tenant_id),
                "model_id": str(model_id),
                "endpoint": f"/models/{model_id}",
                "method": "PUT",
            }
        },
    )

    try:
        # Update the model
        updated_model = model_service.update_model(
            tenant_id=current_user.tenant_id,
            model_id=model_id,
            user_id=current_user.user_id,
            model_update=model_update,
        )

        if not updated_model:
            logger.warning(
                "Model not found for update",
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "user_id": str(current_user.user_id),
                        "tenant_id": str(current_user.tenant_id),
                        "model_id": str(model_id),
                        "endpoint": f"/models/{model_id}",
                        "status": "not_found",
                    }
                },
            )

            return create_error_response(
                message="Model not found",
                error_code="NOT_FOUND",
                status_code=status.HTTP_404_NOT_FOUND,
                tenant_id=current_user.tenant_id,
            )

        # Log successful completion
        logger.info(
            "Model updated successfully",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "model_id": str(model_id),
                    "model_name": updated_model.name,
                    "endpoint": f"/models/{model_id}",
                    "status": "success",
                }
            },
        )

        return create_success_response(
            data={
                **updated_model.model_dump(mode='json'),
                "message": "Model updated successfully",
            },
            tenant_id=current_user.tenant_id,
        )

    except ValueError as e:
        # Business logic errors
        logger.warning(
            f"Model update validation error: {str(e)}",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "model_id": str(model_id),
                    "error": str(e),
                    "endpoint": f"/models/{model_id}",
                    "status": "validation_error",
                }
            },
        )

        return create_error_response(
            message=str(e),
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            tenant_id=current_user.tenant_id,
        )

    except Exception as e:
        # Unexpected errors
        logger.error(
            f"Unexpected error during model update: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "model_id": str(model_id),
                    "error_type": type(e).__name__,
                    "endpoint": f"/models/{model_id}",
                    "status": "error",
                }
            },
        )

        return create_error_response(
            message="Failed to update model",
            error_code="INTERNAL_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            tenant_id=current_user.tenant_id,
        )


@router.delete("/{model_id}", response_model=dict)
async def delete_model(
    request: Request,
    model_id: UUID = Path(..., description="Model ID"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    model_service: ModelService = Depends(get_model_service),
):
    """
    Delete a simulation model (soft delete).

    Marks the specified model as deleted. The model data is retained
    for audit purposes but is no longer accessible via normal queries.

    Args:
        model_id: UUID of the model to delete
        current_user: Authenticated user context
        model_service: Model service instance

    Returns:
        Success confirmation

    Raises:
        404: Model not found
        500: Internal server error
    """
    # Get request ID from middleware
    request_id = getattr(request.state, "request_id", "unknown")

    # Log request entry
    logger.info(
        "Model deletion request received",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "user_id": str(current_user.user_id),
                "tenant_id": str(current_user.tenant_id),
                "model_id": str(model_id),
                "endpoint": f"/models/{model_id}",
                "method": "DELETE",
            }
        },
    )

    try:
        # Delete the model
        success = model_service.delete_model(
            tenant_id=current_user.tenant_id,
            model_id=model_id,
            user_id=current_user.user_id,
        )

        if not success:
            logger.warning(
                "Model not found for deletion",
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "user_id": str(current_user.user_id),
                        "tenant_id": str(current_user.tenant_id),
                        "model_id": str(model_id),
                        "endpoint": f"/models/{model_id}",
                        "status": "not_found",
                    }
                },
            )

            return create_error_response(
                message="Model not found",
                error_code="NOT_FOUND",
                status_code=status.HTTP_404_NOT_FOUND,
                tenant_id=current_user.tenant_id,
            )

        # Log successful completion
        logger.info(
            "Model deleted successfully",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "model_id": str(model_id),
                    "endpoint": f"/models/{model_id}",
                    "status": "success",
                }
            },
        )

        return create_success_response(
            data={"message": "Model deleted successfully"},
            tenant_id=current_user.tenant_id,
        )

    except Exception as e:
        # Unexpected errors
        logger.error(
            f"Unexpected error during model deletion: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "model_id": str(model_id),
                    "error_type": type(e).__name__,
                    "endpoint": f"/models/{model_id}",
                    "status": "error",
                }
            },
        )

        return create_error_response(
            message="Failed to delete model",
            error_code="INTERNAL_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            tenant_id=current_user.tenant_id,
        )


@router.post("/from-template", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_from_template(
    request: Request,
    template_request: ModelTemplateCreate,
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    model_service: ModelService = Depends(get_model_service),
):
    """
    Create a new model from an existing template.

    Creates a new model by copying configuration from an existing template
    model. The new model gets a unique name and can have different associations.

    Args:
        template_request: Template creation request data
        current_user: Authenticated user context
        model_service: Model service instance

    Returns:
        Created model data

    Raises:
        400: Validation error or template not found
        500: Internal server error
    """
    # Get request ID from middleware
    request_id = getattr(request.state, "request_id", "unknown")

    # Log request entry
    logger.info(
        "Template model creation request received",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "user_id": str(current_user.user_id),
                "tenant_id": str(current_user.tenant_id),
                "template_id": str(template_request.template_model_id),
                "new_name": template_request.new_model_name,
                "endpoint": "/models/from-template",
                "method": "POST",
            }
        },
    )

    try:
        # Create the model from template
        new_model = model_service.create_from_template(
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id,
            template_request=template_request,
        )

        # Log successful completion
        logger.info(
            "Model created from template successfully",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "template_id": str(template_request.template_model_id),
                    "new_model_id": str(new_model.id),
                    "new_name": new_model.name,
                    "endpoint": "/models/from-template",
                    "status": "success",
                }
            },
        )

        return create_success_response(
            data={
                **new_model.model_dump(mode='json'),
                "message": "Model created from template successfully",
            },
            tenant_id=current_user.tenant_id,
        )

    except ValueError as e:
        # Business logic errors
        logger.warning(
            f"Template model creation validation error: {str(e)}",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "template_id": str(template_request.template_model_id),
                    "error": str(e),
                    "endpoint": "/models/from-template",
                    "status": "validation_error",
                }
            },
        )

        return create_error_response(
            message=str(e),
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            tenant_id=current_user.tenant_id,
        )

    except Exception as e:
        # Unexpected errors
        logger.error(
            f"Unexpected error during template model creation: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "template_id": str(template_request.template_model_id),
                    "error_type": type(e).__name__,
                    "endpoint": "/models/from-template",
                    "status": "error",
                }
            },
        )

        return create_error_response(
            message="Failed to create model from template",
            error_code="INTERNAL_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            tenant_id=current_user.tenant_id,
        )


@router.get("/templates/available", response_model=dict)
async def list_template_models(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    include_global: bool = Query(True, description="Include global templates"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    model_service: ModelService = Depends(get_model_service),
):
    """
    List available template models.

    Returns template models that can be used to create new models.
    Can include both tenant-specific and global templates.

    Args:
        skip: Pagination offset
        limit: Maximum results to return
        include_global: Whether to include global templates
        current_user: Authenticated user context
        model_service: Model service instance

    Returns:
        Paginated list of template models

    Raises:
        500: Internal server error
    """
    # Get request ID from middleware
    request_id = getattr(request.state, "request_id", "unknown")

    # Log request entry
    logger.info(
        "Template models list request received",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "user_id": str(current_user.user_id),
                "tenant_id": str(current_user.tenant_id),
                "skip": skip,
                "limit": limit,
                "include_global": include_global,
                "endpoint": "/models/templates/available",
                "method": "GET",
            }
        },
    )

    try:
        # Get template models
        tenant_id = current_user.tenant_id if not include_global else None
        templates_response = model_service.get_template_models(
            tenant_id=tenant_id,
            skip=skip,
            limit=limit,
        )

        # Log successful completion
        logger.info(
            "Template models retrieved successfully",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "results_count": len(templates_response.models),
                    "total_count": templates_response.total,
                    "endpoint": "/models/templates/available",
                    "status": "success",
                }
            },
        )

        return create_success_response(
            data=templates_response.model_dump(mode='json'),
            tenant_id=current_user.tenant_id,
        )

    except Exception as e:
        # Unexpected errors
        logger.error(
            f"Unexpected error during template models listing: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "error_type": type(e).__name__,
                    "endpoint": "/models/templates/available",
                    "status": "error",
                }
            },
        )

        return create_error_response(
            message="Failed to retrieve template models",
            error_code="INTERNAL_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            tenant_id=current_user.tenant_id,
        )


@router.get("/accessible", response_model=dict)
async def get_accessible_models(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    model_service: ModelService = Depends(get_model_service),
):
    """
    Get models accessible to the current user.

    Returns models that the current user can access based on their
    permissions, including models they created, public models, and
    models shared through organizations and teams.

    Args:
        skip: Pagination offset
        limit: Maximum results to return
        current_user: Authenticated user context
        model_service: Model service instance

    Returns:
        Paginated list of accessible models

    Raises:
        500: Internal server error
    """
    # Get request ID from middleware
    request_id = getattr(request.state, "request_id", "unknown")

    # Log request entry
    logger.info(
        "Accessible models request received",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "user_id": str(current_user.user_id),
                "tenant_id": str(current_user.tenant_id),
                "skip": skip,
                "limit": limit,
                "endpoint": "/models/accessible",
                "method": "GET",
            }
        },
    )

    try:
        # Get accessible models
        models_response = model_service.get_accessible_models(
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id,
            skip=skip,
            limit=limit,
        )

        # Log successful completion
        logger.info(
            "Accessible models retrieved successfully",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "results_count": len(models_response.models),
                    "total_count": models_response.total,
                    "endpoint": "/models/accessible",
                    "status": "success",
                }
            },
        )

        return create_success_response(
            data=models_response.model_dump(mode='json'),
            tenant_id=current_user.tenant_id,
        )

    except Exception as e:
        # Unexpected errors
        logger.error(
            f"Unexpected error during accessible models retrieval: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "error_type": type(e).__name__,
                    "endpoint": "/models/accessible",
                    "status": "error",
                }
            },
        )

        return create_error_response(
            message="Failed to retrieve accessible models",
            error_code="INTERNAL_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            tenant_id=current_user.tenant_id,
        )


@router.get("/statistics", response_model=dict)
async def get_model_statistics(
    request: Request,
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    model_service: ModelService = Depends(get_model_service),
):
    """
    Get model statistics for the current tenant.

    Returns comprehensive statistics about models within the tenant,
    including counts by source, creation trends, and usage metrics.

    Args:
        current_user: Authenticated user context
        model_service: Model service instance

    Returns:
        Model statistics and analytics

    Raises:
        500: Internal server error
    """
    # Get request ID from middleware
    request_id = getattr(request.state, "request_id", "unknown")

    # Log request entry
    logger.info(
        "Model statistics request received",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "user_id": str(current_user.user_id),
                "tenant_id": str(current_user.tenant_id),
                "endpoint": "/models/statistics",
                "method": "GET",
            }
        },
    )

    try:
        # Get model statistics
        statistics = model_service.get_model_statistics(
            tenant_id=current_user.tenant_id
        )

        # Log successful completion
        logger.info(
            "Model statistics retrieved successfully",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "total_models": statistics.get("total_models", 0),
                    "endpoint": "/models/statistics",
                    "status": "success",
                }
            },
        )

        return create_success_response(
            data=statistics,
            tenant_id=current_user.tenant_id,
        )

    except Exception as e:
        # Unexpected errors
        logger.error(
            f"Unexpected error during model statistics retrieval: {str(e)}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(current_user.user_id),
                    "tenant_id": str(current_user.tenant_id),
                    "error_type": type(e).__name__,
                    "endpoint": "/models/statistics",
                    "status": "error",
                }
            },
        )

        return create_error_response(
            message="Failed to retrieve model statistics",
            error_code="INTERNAL_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            tenant_id=current_user.tenant_id,
        )