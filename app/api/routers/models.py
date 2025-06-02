# app/api/routers/models.py
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.schemas.simulation_model import (
    ModelCreate,
    ModelRead,
    ModelUpdate,
    ModelSummary,
    ModelCreateFromTemplate,
)
from app.services.model_service import ModelService
from app.db.models.user import User

router = APIRouter(prefix="/models", tags=["models"])
model_service = ModelService()


@router.post("/", response_model=ModelRead, status_code=status.HTTP_201_CREATED)
def create_model(
    model_create: ModelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new simulation model.

    - **name**: Unique name for the model within the tenant
    - **source**: Source type (lucidchart, miro, manual, import)
    - **description**: Optional description
    - **simulation parameters**: Various simulation settings with defaults
    """
    try:
        model = model_service.create_model(
            db=db,
            tenant_id=current_user.tenant_id,
            model_create=model_create,
            current_user_id=current_user.id,
        )
        return model
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create model",
        )


@router.get("/", response_model=List[ModelSummary])
def list_models(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    source: Optional[str] = Query(None, description="Filter by source type"),
    organization_id: Optional[UUID] = Query(None, description="Filter by organization"),
    team_id: Optional[UUID] = Query(None, description="Filter by team"),
    user_id: Optional[UUID] = Query(None, description="Filter by creator"),
    search: Optional[str] = Query(None, description="Search by model name"),
    templates_only: bool = Query(False, description="Return only template models"),
    accessible_only: bool = Query(True, description="Return only accessible models"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List simulation models with various filtering options.

    By default, returns models accessible to the current user.
    Use query parameters to filter results.
    """
    try:
        # Apply filters based on query parameters
        if templates_only:
            models = model_service.get_template_models(
                db=db, tenant_id=current_user.tenant_id, skip=skip, limit=limit
            )
        elif search:
            models = model_service.search_models(
                db=db,
                tenant_id=current_user.tenant_id,
                name_query=search,
                skip=skip,
                limit=limit,
            )
        elif source:
            models = model_service.get_models_by_source(
                db=db,
                tenant_id=current_user.tenant_id,
                source=source,
                skip=skip,
                limit=limit,
            )
        elif organization_id:
            models = model_service.get_models_by_organization(
                db=db,
                tenant_id=current_user.tenant_id,
                organization_id=organization_id,
                skip=skip,
                limit=limit,
            )
        elif team_id:
            models = model_service.get_models_by_team(
                db=db,
                tenant_id=current_user.tenant_id,
                team_id=team_id,
                skip=skip,
                limit=limit,
            )
        elif user_id:
            models = model_service.list_models_for_user(
                db=db,
                tenant_id=current_user.tenant_id,
                user_id=user_id,
                skip=skip,
                limit=limit,
            )
        elif accessible_only:
            models = model_service.list_accessible_models(
                db=db,
                tenant_id=current_user.tenant_id,
                user_id=current_user.id,
                skip=skip,
                limit=limit,
            )
        else:
            models = model_service.list_models_for_tenant(
                db=db, tenant_id=current_user.tenant_id, skip=skip, limit=limit
            )

        return models
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve models",
        )


@router.get("/{model_id}", response_model=ModelRead)
def get_model(
    model_id: UUID,
    include_relationships: bool = Query(False, description="Include related entities"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get details of a specific simulation model.

    - **model_id**: UUID of the model
    - **include_relationships**: Whether to include user/org/team details
    """
    model = model_service.get_model_by_id(
        db=db,
        tenant_id=current_user.tenant_id,
        model_id=model_id,
        load_relationships=include_relationships,
    )

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
        )

    return model


@router.put("/{model_id}", response_model=ModelRead)
def update_model(
    model_id: UUID,
    model_update: ModelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a simulation model.

    Only the model creator can update the model (for now).
    Some updates may increment the model version.
    """
    try:
        model = model_service.update_model(
            db=db,
            tenant_id=current_user.tenant_id,
            model_id=model_id,
            model_update=model_update,
            current_user_id=current_user.id,
        )

        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
            )

        return model
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update model",
        )


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(
    model_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a simulation model (soft delete).

    Only the model creator can delete the model (for now).
    """
    try:
        success = model_service.delete_model(
            db=db,
            tenant_id=current_user.tenant_id,
            model_id=model_id,
            current_user_id=current_user.id,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete model",
        )


@router.post(
    "/from-template/{template_model_id}",
    response_model=ModelRead,
    status_code=status.HTTP_201_CREATED,
)
def create_model_from_template(
    template_model_id: UUID,
    template_create: ModelCreateFromTemplate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new model based on an existing template.

    - **template_model_id**: UUID of the template model to copy from
    - **name**: Name for the new model
    - **description**: Optional description override
    """
    try:
        model = model_service.create_model_from_template(
            db=db,
            tenant_id=current_user.tenant_id,
            template_model_id=template_model_id,
            template_create=template_create,
            current_user_id=current_user.id,
        )
        return model
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create model from template",
        )


@router.get("/templates/", response_model=List[ModelSummary])
def list_template_models(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    include_public: bool = Query(True, description="Include public templates"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List available template models.

    Returns template models accessible to the current user.
    """
    try:
        tenant_id = current_user.tenant_id if include_public else None
        templates = model_service.get_template_models(
            db=db, tenant_id=tenant_id, skip=skip, limit=limit
        )
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve template models",
        )


@router.get("/users/{user_id}/count")
def get_user_model_count(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the count of models created by a specific user.
    """
    try:
        count = model_service.get_user_model_count(
            db=db, tenant_id=current_user.tenant_id, user_id=user_id
        )
        return {"user_id": user_id, "model_count": count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user model count",
        )
