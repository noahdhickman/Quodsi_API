# app/api/routers/analyses.py
"""
FastAPI router for Analysis management endpoints.

Provides comprehensive REST API for creating, reading, updating, and deleting
analyses with proper validation, authorization, and error handling.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.api.deps import get_db, get_current_user_mock, MockCurrentUser
from app.services.analysis_service import get_analysis_service, AnalysisService
from app.schemas.analysis import (
    AnalysisCreate, AnalysisUpdate, AnalysisRead, AnalysisSummary,
    AnalysisListResponse, AnalysisQuery, AnalysisStatistics,
    AnalysisCopyRequest, BulkAnalysisCreate, BulkAnalysisResponse,
    AnalysisValidationResponse, TimePeriod
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/analyses", tags=["Analyses"])


@router.post("/", response_model=AnalysisRead, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    analysis_data: AnalysisCreate,
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Create a new analysis.
    
    Creates a new analysis linked to a specific model with validation
    for name uniqueness and proper tenant isolation.
    """
    try:
        analysis = analysis_service.create_analysis(
            db=db,
            tenant_id=current_user.tenant_id,
            analysis_create=analysis_data,
            current_user_id=current_user.user_id
        )
        
        logger.info(f"Analysis created via API: {analysis.name} by user {current_user.user_id}")
        return analysis
        
    except ValueError as e:
        logger.warning(f"Analysis creation validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        logger.warning(f"Analysis creation permission error: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error creating analysis"
        )


@router.get("/{analysis_id}", response_model=AnalysisRead)
async def get_analysis(
    analysis_id: UUID,
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Get a specific analysis by ID.
    
    Returns detailed analysis information including all metadata
    and default parameters for child scenarios.
    """
    try:
        analysis = analysis_service.get_analysis_by_id(
            db=db,
            tenant_id=current_user.tenant_id,
            analysis_id=analysis_id,
            current_user_id=current_user.user_id
        )
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis {analysis_id} not found"
            )
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving analysis"
        )


@router.put("/{analysis_id}", response_model=AnalysisRead)
async def update_analysis(
    analysis_id: UUID,
    analysis_data: AnalysisUpdate,
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Update an existing analysis.
    
    Updates analysis properties with validation for name uniqueness
    and authorization checking. Only the analysis creator can update.
    """
    try:
        updated_analysis = analysis_service.update_analysis(
            db=db,
            tenant_id=current_user.tenant_id,
            analysis_id=analysis_id,
            analysis_update=analysis_data,
            current_user_id=current_user.user_id
        )
        
        if not updated_analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis {analysis_id} not found"
            )
        
        logger.info(f"Analysis updated via API: {analysis_id} by user {current_user.user_id}")
        return updated_analysis
        
    except ValueError as e:
        logger.warning(f"Analysis update validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        logger.warning(f"Analysis update permission error: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error updating analysis"
        )


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(
    analysis_id: UUID,
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Delete an analysis (soft delete).
    
    Soft deletes the analysis and all associated data.
    Only the analysis creator can delete the analysis.
    """
    try:
        deleted = analysis_service.delete_analysis(
            db=db,
            tenant_id=current_user.tenant_id,
            analysis_id=analysis_id,
            current_user_id=current_user.user_id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis {analysis_id} not found"
            )
        
        logger.info(f"Analysis deleted via API: {analysis_id} by user {current_user.user_id}")
        
    except PermissionError as e:
        logger.warning(f"Analysis deletion permission error: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error deleting analysis"
        )


@router.get("/models/{model_id}/analyses", response_model=AnalysisListResponse)
async def list_analyses_for_model(
    model_id: UUID,
    skip: int = Query(0, ge=0, description="Number of analyses to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of analyses to return"),
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    List all analyses for a specific model.
    
    Returns paginated list of analyses belonging to the specified model
    with proper tenant isolation and permission filtering.
    """
    try:
        analyses = analysis_service.list_analyses_for_model(
            db=db,
            tenant_id=current_user.tenant_id,
            model_id=model_id,
            skip=skip,
            limit=limit,
            current_user_id=current_user.user_id
        )
        
        # Get total count for pagination
        # Note: This could be optimized with a dedicated count method
        total_analyses = analysis_service.list_analyses_for_model(
            db=db,
            tenant_id=current_user.tenant_id,
            model_id=model_id,
            skip=0,
            limit=10000  # Large number to get total count
        )
        
        return AnalysisListResponse(
            analyses=analyses,
            total=len(total_analyses),
            skip=skip,
            limit=limit
        )
        
    except ValueError as e:
        logger.warning(f"Model validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error listing analyses for model {model_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error listing analyses"
        )


@router.get("/users/{user_id}/analyses", response_model=AnalysisListResponse)
async def list_analyses_by_user(
    user_id: UUID,
    skip: int = Query(0, ge=0, description="Number of analyses to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of analyses to return"),
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    List analyses created by a specific user.
    
    Returns paginated list of analyses created by the specified user
    within the current tenant.
    """
    try:
        analyses = analysis_service.list_analyses_by_user(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=user_id,
            skip=skip,
            limit=limit
        )
        
        # Get total count for pagination
        total_analyses = analysis_service.list_analyses_by_user(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=user_id,
            skip=0,
            limit=10000  # Large number to get total count
        )
        
        return AnalysisListResponse(
            analyses=analyses,
            total=len(total_analyses),
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Unexpected error listing analyses for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error listing analyses"
        )


@router.post("/search", response_model=AnalysisListResponse)
async def search_analyses(
    query: AnalysisQuery,
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Search analyses with advanced filtering.
    
    Supports filtering by model, user, time period, name search,
    date ranges, and other criteria with pagination.
    """
    try:
        analyses = analysis_service.search_analyses(
            db=db,
            tenant_id=current_user.tenant_id,
            query=query,
            current_user_id=current_user.user_id
        )
        
        # For search results, we'll use the query limit as total
        # In a production system, you'd want a separate count query
        total = len(analyses) if len(analyses) < query.limit else query.limit
        
        return AnalysisListResponse(
            analyses=analyses,
            total=total,
            skip=query.skip,
            limit=query.limit
        )
        
    except Exception as e:
        logger.error(f"Unexpected error searching analyses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error searching analyses"
        )


@router.post("/{analysis_id}/copy", response_model=AnalysisRead, status_code=status.HTTP_201_CREATED)
async def copy_analysis(
    analysis_id: UUID,
    copy_request: AnalysisCopyRequest,
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Copy an existing analysis with a new name.
    
    Creates a duplicate of the specified analysis with a new name
    and optionally a different target model.
    """
    try:
        # Set the source analysis ID from the path parameter
        copy_request.source_analysis_id = analysis_id
        
        copied_analysis = analysis_service.copy_analysis(
            db=db,
            tenant_id=current_user.tenant_id,
            copy_request=copy_request,
            current_user_id=current_user.user_id
        )
        
        logger.info(f"Analysis copied via API: {analysis_id} -> {copied_analysis.id} by user {current_user.user_id}")
        return copied_analysis
        
    except ValueError as e:
        logger.warning(f"Analysis copy validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        logger.warning(f"Analysis copy permission error: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error copying analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error copying analysis"
        )


@router.post("/bulk", response_model=BulkAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def bulk_create_analyses(
    bulk_request: BulkAnalysisCreate,
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Create multiple analyses in bulk.
    
    Efficiently creates multiple analyses for the same model
    with individual success/failure tracking.
    """
    try:
        result = analysis_service.bulk_create_analyses(
            db=db,
            tenant_id=current_user.tenant_id,
            bulk_request=bulk_request,
            current_user_id=current_user.user_id
        )
        
        logger.info(f"Bulk analysis creation via API: {result.total_successful}/{result.total_requested} successful by user {current_user.user_id}")
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error in bulk analysis creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error in bulk analysis creation"
        )


@router.post("/validate", response_model=AnalysisValidationResponse)
async def validate_analysis_creation(
    analysis_data: AnalysisCreate,
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Validate analysis creation without actually creating it.
    
    Performs all validation checks (name uniqueness, model existence, etc.)
    and returns detailed validation results without creating the analysis.
    """
    try:
        validation_result = analysis_service.validate_analysis_creation(
            db=db,
            tenant_id=current_user.tenant_id,
            analysis_create=analysis_data,
            current_user_id=current_user.user_id
        )
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Unexpected error validating analysis creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error validating analysis"
        )


@router.get("/statistics", response_model=AnalysisStatistics)
async def get_analysis_statistics(
    model_id: Optional[UUID] = Query(None, description="Optional model ID to filter statistics"),
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Get statistical information about analyses.
    
    Returns comprehensive analytics including counts by time period,
    most active models, recent activity, and usage patterns.
    """
    try:
        statistics = analysis_service.get_analysis_statistics(
            db=db,
            tenant_id=current_user.tenant_id,
            model_id=model_id
        )
        
        return statistics
        
    except Exception as e:
        logger.error(f"Unexpected error getting analysis statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error getting statistics"
        )


# Additional utility endpoints

@router.get("/time-periods", response_model=List[str])
async def get_available_time_periods():
    """
    Get list of available time periods for analyses.
    
    Returns the allowed values for default_time_period field.
    """
    return [period.value for period in TimePeriod]


@router.get("/my-analyses", response_model=AnalysisListResponse)
async def get_current_user_analyses(
    skip: int = Query(0, ge=0, description="Number of analyses to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of analyses to return"),
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Get analyses created by the current user.
    
    Convenience endpoint for getting the current user's analyses
    without specifying the user ID.
    """
    try:
        analyses = analysis_service.list_analyses_by_user(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id,
            skip=skip,
            limit=limit
        )
        
        # Get total count for pagination
        total_analyses = analysis_service.list_analyses_by_user(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id,
            skip=0,
            limit=10000
        )
        
        return AnalysisListResponse(
            analyses=analyses,
            total=len(total_analyses),
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Unexpected error getting current user analyses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error getting user analyses"
        )