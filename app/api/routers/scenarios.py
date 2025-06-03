# app/api/routers/scenarios.py
"""
FastAPI router for Scenario management endpoints.

Provides comprehensive REST API for creating, reading, updating, and deleting
scenarios with execution lifecycle management, proper validation, authorization, 
and error handling.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.api.deps import get_db, get_current_user_mock, MockCurrentUser
from app.services.scenario_service import get_scenario_service, ScenarioService
from app.schemas.scenario import (
    ScenarioCreate, ScenarioUpdate, ScenarioRead, ScenarioSummary,
    ScenarioListResponse, ScenarioQuery, ScenarioStatistics,
    ScenarioCopyRequest, BulkScenarioCreate, BulkScenarioResponse,
    ScenarioValidationResponse, ScenarioExecutionRequest, ScenarioState,
    ScenarioExecutionProgress, TimePeriod, ScenarioStateUpdate
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.post("/", response_model=ScenarioRead, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    scenario_data: ScenarioCreate,
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    scenario_service: ScenarioService = Depends(get_scenario_service)
):
    """
    Create a new scenario.
    
    Creates a new scenario linked to a specific analysis with validation
    for name uniqueness and proper tenant isolation. Inherits default
    parameters from parent analysis if not specified.
    """
    try:
        scenario = scenario_service.create_scenario(
            db=db,
            tenant_id=current_user.tenant_id,
            scenario_create=scenario_data,
            current_user_id=current_user.user_id
        )
        
        logger.info(f"Scenario created via API: {scenario.name} by user {current_user.user_id}")
        return scenario
        
    except ValueError as e:
        logger.warning(f"Scenario creation validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        logger.warning(f"Scenario creation permission error: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating scenario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error creating scenario"
        )


@router.get("/{scenario_id}", response_model=ScenarioRead)
async def get_scenario(
    scenario_id: UUID,
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    scenario_service: ScenarioService = Depends(get_scenario_service)
):
    """
    Get a specific scenario by ID.
    
    Returns detailed scenario information including execution state,
    progress, error information, and configuration parameters.
    """
    try:
        scenario = scenario_service.get_scenario_by_id(
            db=db,
            tenant_id=current_user.tenant_id,
            scenario_id=scenario_id,
            current_user_id=current_user.user_id
        )
        
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found"
            )
        
        return scenario
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving scenario {scenario_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving scenario"
        )


@router.put("/{scenario_id}", response_model=ScenarioRead)
async def update_scenario(
    scenario_id: UUID,
    scenario_data: ScenarioUpdate,
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    scenario_service: ScenarioService = Depends(get_scenario_service)
):
    """
    Update an existing scenario.
    
    Updates scenario metadata with validation for name uniqueness
    and authorization checking. Only modifiable when scenario is
    not running or completed.
    """
    try:
        updated_scenario = scenario_service.update_scenario(
            db=db,
            tenant_id=current_user.tenant_id,
            scenario_id=scenario_id,
            scenario_update=scenario_data,
            current_user_id=current_user.user_id
        )
        
        if not updated_scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found"
            )
        
        logger.info(f"Scenario updated via API: {scenario_id} by user {current_user.user_id}")
        return updated_scenario
        
    except ValueError as e:
        logger.warning(f"Scenario update validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        logger.warning(f"Scenario update permission error: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating scenario {scenario_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error updating scenario"
        )


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(
    scenario_id: UUID,
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    scenario_service: ScenarioService = Depends(get_scenario_service)
):
    """
    Delete a scenario (soft delete).
    
    Soft deletes the scenario and all associated data.
    Cannot delete running scenarios - they must be cancelled first.
    """
    try:
        deleted = scenario_service.delete_scenario(
            db=db,
            tenant_id=current_user.tenant_id,
            scenario_id=scenario_id,
            current_user_id=current_user.user_id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found"
            )
        
        logger.info(f"Scenario deleted via API: {scenario_id} by user {current_user.user_id}")
        
    except ValueError as e:
        logger.warning(f"Scenario deletion validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        logger.warning(f"Scenario deletion permission error: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting scenario {scenario_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error deleting scenario"
        )


@router.get("/analyses/{analysis_id}/scenarios", response_model=ScenarioListResponse)
async def list_scenarios_for_analysis(
    analysis_id: UUID,
    skip: int = Query(0, ge=0, description="Number of scenarios to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of scenarios to return"),
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    scenario_service: ScenarioService = Depends(get_scenario_service)
):
    """
    List all scenarios for a specific analysis.
    
    Returns paginated list of scenarios belonging to the specified analysis
    with proper tenant isolation and permission filtering.
    """
    try:
        scenarios = scenario_service.list_scenarios_for_analysis(
            db=db,
            tenant_id=current_user.tenant_id,
            analysis_id=analysis_id,
            skip=skip,
            limit=limit,
            current_user_id=current_user.user_id
        )
        
        # Get total count for pagination
        # Note: This could be optimized with a dedicated count method
        total_scenarios = scenario_service.list_scenarios_for_analysis(
            db=db,
            tenant_id=current_user.tenant_id,
            analysis_id=analysis_id,
            skip=0,
            limit=10000  # Large number to get total count
        )
        
        return ScenarioListResponse(
            scenarios=scenarios,
            total=len(total_scenarios),
            skip=skip,
            limit=limit
        )
        
    except ValueError as e:
        logger.warning(f"Analysis validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error listing scenarios for analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error listing scenarios"
        )


@router.get("/users/{user_id}/scenarios", response_model=ScenarioListResponse)
async def list_scenarios_by_user(
    user_id: UUID,
    skip: int = Query(0, ge=0, description="Number of scenarios to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of scenarios to return"),
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    scenario_service: ScenarioService = Depends(get_scenario_service)
):
    """
    List scenarios created by a specific user.
    
    Returns paginated list of scenarios created by the specified user
    within the current tenant.
    """
    try:
        scenarios = scenario_service.list_scenarios_by_user(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=user_id,
            skip=skip,
            limit=limit
        )
        
        # Get total count for pagination
        total_scenarios = scenario_service.list_scenarios_by_user(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=user_id,
            skip=0,
            limit=10000  # Large number to get total count
        )
        
        return ScenarioListResponse(
            scenarios=scenarios,
            total=len(total_scenarios),
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Unexpected error listing scenarios for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error listing scenarios"
        )


@router.post("/search", response_model=ScenarioListResponse)
async def search_scenarios(
    query: ScenarioQuery,
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    scenario_service: ScenarioService = Depends(get_scenario_service)
):
    """
    Search scenarios with advanced filtering.
    
    Supports filtering by analysis, user, state, time period, name search,
    date ranges, error status, and other criteria with pagination and sorting.
    """
    try:
        scenarios = scenario_service.search_scenarios(
            db=db,
            tenant_id=current_user.tenant_id,
            query=query,
            current_user_id=current_user.user_id
        )
        
        # For search results, we'll use the query limit as total
        # In a production system, you'd want a separate count query
        total = len(scenarios) if len(scenarios) < query.limit else query.limit
        
        return ScenarioListResponse(
            scenarios=scenarios,
            total=total,
            skip=query.skip,
            limit=query.limit
        )
        
    except Exception as e:
        logger.error(f"Unexpected error searching scenarios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error searching scenarios"
        )


# === Execution Control Endpoints ===

@router.post("/{scenario_id}/prepare", response_model=dict)
async def prepare_scenario_for_run(
    scenario_id: UUID,
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    scenario_service: ScenarioService = Depends(get_scenario_service)
):
    """
    Prepare scenario for execution.
    
    Sets the scenario state to 'ready_to_run' after validation.
    This is typically called before starting execution.
    """
    try:
        success = scenario_service.prepare_scenario_for_run(
            db=db,
            tenant_id=current_user.tenant_id,
            scenario_id=scenario_id,
            current_user_id=current_user.user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found"
            )
        
        logger.info(f"Scenario prepared for run via API: {scenario_id} by user {current_user.user_id}")
        return {"message": "Scenario prepared for execution", "scenario_id": scenario_id}
        
    except ValueError as e:
        logger.warning(f"Scenario preparation validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        logger.warning(f"Scenario preparation permission error: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error preparing scenario {scenario_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error preparing scenario"
        )


@router.post("/{scenario_id}/run", response_model=dict)
async def start_scenario_run(
    scenario_id: UUID,
    execution_request: Optional[ScenarioExecutionRequest] = None,
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    scenario_service: ScenarioService = Depends(get_scenario_service)
):
    """
    Start scenario execution.
    
    Initiates execution by setting state to 'is_running' and recording
    start time. The actual simulation engine integration would happen
    after this API call.
    """
    try:
        success = scenario_service.start_scenario_run(
            db=db,
            tenant_id=current_user.tenant_id,
            scenario_id=scenario_id,
            execution_request=execution_request
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found or cannot be started"
            )
        
        logger.info(f"Scenario execution started via API: {scenario_id} by user {current_user.user_id}")
        return {"message": "Scenario execution started", "scenario_id": scenario_id}
        
    except ValueError as e:
        logger.warning(f"Scenario start validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error starting scenario {scenario_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error starting scenario"
        )


@router.post("/{scenario_id}/cancel", response_model=dict)
async def cancel_scenario_run(
    scenario_id: UUID,
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    scenario_service: ScenarioService = Depends(get_scenario_service)
):
    """
    Cancel a running scenario.
    
    Attempts to cancel a running scenario by setting state to 'cancelling'.
    The actual cancellation would be handled by the simulation engine.
    """
    try:
        success = scenario_service.cancel_scenario_run(
            db=db,
            tenant_id=current_user.tenant_id,
            scenario_id=scenario_id,
            current_user_id=current_user.user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found or cannot be cancelled"
            )
        
        logger.info(f"Scenario cancellation initiated via API: {scenario_id} by user {current_user.user_id}")
        return {"message": "Scenario cancellation initiated", "scenario_id": scenario_id}
        
    except ValueError as e:
        logger.warning(f"Scenario cancellation validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        logger.warning(f"Scenario cancellation permission error: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error cancelling scenario {scenario_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error cancelling scenario"
        )


@router.get("/{scenario_id}/status", response_model=dict)
async def get_scenario_status(
    scenario_id: UUID,
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    scenario_service: ScenarioService = Depends(get_scenario_service)
):
    """
    Get current execution status and progress.
    
    Returns detailed progress information including current replication,
    progress percentage, timing, and any error details.
    """
    try:
        scenario = scenario_service.get_scenario_by_id(
            db=db,
            tenant_id=current_user.tenant_id,
            scenario_id=scenario_id,
            current_user_id=current_user.user_id
        )
        
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found"
            )
        
        # Extract progress information from the scenario
        progress_info = {
            "scenario_id": scenario.id,
            "state": scenario.state,
            "current_rep": scenario.current_rep,
            "total_reps": scenario.total_reps,
            "progress_percentage": float(scenario.progress_percentage) if scenario.progress_percentage else None,
            "started_at": scenario.started_at.isoformat() if scenario.started_at else None,
            "completed_at": scenario.completed_at.isoformat() if scenario.completed_at else None,
            "execution_time_ms": scenario.execution_time_ms,
            "has_errors": scenario.state == ScenarioState.RAN_WITH_ERRORS,
            "error_message": scenario.error_message,
            "is_running": scenario.state == ScenarioState.IS_RUNNING,
            "is_completed": scenario.state in [ScenarioState.RAN_SUCCESS, ScenarioState.RAN_WITH_ERRORS]
        }
        
        return progress_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting scenario status {scenario_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error getting scenario status"
        )


# === Additional Utility Endpoints ===

@router.post("/{scenario_id}/copy", response_model=ScenarioRead, status_code=status.HTTP_201_CREATED)
async def copy_scenario(
    scenario_id: UUID,
    copy_request: ScenarioCopyRequest,
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    scenario_service: ScenarioService = Depends(get_scenario_service)
):
    """
    Copy an existing scenario with a new name.
    
    Creates a duplicate of the specified scenario with a new name
    and optionally a different target analysis.
    """
    try:
        # Set the source scenario ID from the path parameter
        copy_request.source_scenario_id = scenario_id
        
        copied_scenario = scenario_service.copy_scenario(
            db=db,
            tenant_id=current_user.tenant_id,
            copy_request=copy_request,
            current_user_id=current_user.user_id
        )
        
        logger.info(f"Scenario copied via API: {scenario_id} -> {copied_scenario.id} by user {current_user.user_id}")
        return copied_scenario
        
    except ValueError as e:
        logger.warning(f"Scenario copy validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        logger.warning(f"Scenario copy permission error: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error copying scenario {scenario_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error copying scenario"
        )


@router.post("/bulk", response_model=BulkScenarioResponse, status_code=status.HTTP_201_CREATED)
async def bulk_create_scenarios(
    bulk_request: BulkScenarioCreate,
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    scenario_service: ScenarioService = Depends(get_scenario_service)
):
    """
    Create multiple scenarios in bulk.
    
    Efficiently creates multiple scenarios for the same analysis
    with individual success/failure tracking.
    """
    try:
        result = scenario_service.bulk_create_scenarios(
            db=db,
            tenant_id=current_user.tenant_id,
            bulk_request=bulk_request,
            current_user_id=current_user.user_id
        )
        
        logger.info(f"Bulk scenario creation via API: {result.total_successful}/{result.total_requested} successful by user {current_user.user_id}")
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error in bulk scenario creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error in bulk scenario creation"
        )


@router.post("/validate", response_model=ScenarioValidationResponse)
async def validate_scenario_creation(
    scenario_data: ScenarioCreate,
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    scenario_service: ScenarioService = Depends(get_scenario_service)
):
    """
    Validate scenario creation without actually creating it.
    
    Performs all validation checks (name uniqueness, analysis existence, etc.)
    and returns detailed validation results without creating the scenario.
    """
    try:
        validation_result = scenario_service.validate_scenario_creation(
            db=db,
            tenant_id=current_user.tenant_id,
            scenario_create=scenario_data,
            current_user_id=current_user.user_id
        )
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Unexpected error validating scenario creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error validating scenario"
        )


@router.get("/statistics", response_model=ScenarioStatistics)
async def get_scenario_statistics(
    analysis_id: Optional[UUID] = Query(None, description="Optional analysis ID to filter statistics"),
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    scenario_service: ScenarioService = Depends(get_scenario_service)
):
    """
    Get statistical information about scenarios.
    
    Returns comprehensive analytics including counts by state, analysis,
    time period, execution success rates, and recent activity.
    """
    try:
        statistics = scenario_service.get_scenario_statistics(
            db=db,
            tenant_id=current_user.tenant_id,
            analysis_id=analysis_id
        )
        
        return statistics
        
    except Exception as e:
        logger.error(f"Unexpected error getting scenario statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error getting statistics"
        )


@router.get("/states", response_model=List[str])
async def get_available_states():
    """
    Get list of available scenario states.
    
    Returns the allowed values for scenario state field.
    """
    return [state.value for state in ScenarioState]


@router.get("/time-periods", response_model=List[str])
async def get_available_time_periods():
    """
    Get list of available time periods for scenarios.
    
    Returns the allowed values for time_period field.
    """
    return [period.value for period in TimePeriod]


@router.get("/my-scenarios", response_model=ScenarioListResponse)
async def get_current_user_scenarios(
    skip: int = Query(0, ge=0, description="Number of scenarios to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of scenarios to return"),
    db: Session = Depends(get_db),
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    scenario_service: ScenarioService = Depends(get_scenario_service)
):
    """
    Get scenarios created by the current user.
    
    Convenience endpoint for getting the current user's scenarios
    without specifying the user ID.
    """
    try:
        scenarios = scenario_service.list_scenarios_by_user(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id,
            skip=skip,
            limit=limit
        )
        
        # Get total count for pagination
        total_scenarios = scenario_service.list_scenarios_by_user(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id,
            skip=0,
            limit=10000
        )
        
        return ScenarioListResponse(
            scenarios=scenarios,
            total=len(total_scenarios),
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Unexpected error getting current user scenarios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error getting user scenarios"
        )