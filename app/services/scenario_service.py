# app/services/scenario_service.py
"""
Service layer for Scenario business operations.

Handles scenario lifecycle management, execution state tracking, validation,
authorization, and business logic while maintaining proper separation from 
data access and API concerns.

Key Responsibilities:
- Scenario CRUD operations with business validation
- Execution lifecycle management (prepare, start, progress, complete, fail)
- Authorization and permission checking
- Business rule enforcement (name uniqueness, state transitions)
- Default value management from parent analysis
- Bulk operations and advanced queries
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.scenario_repository import ScenarioRepository
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.model_repository import ModelRepository
from app.repositories.user_repository import UserRepository
from app.schemas.scenario import (
    ScenarioCreate, ScenarioUpdate, ScenarioRead, ScenarioSummary,
    ScenarioStateUpdate, ScenarioQuery, ScenarioStatistics, 
    ScenarioCopyRequest, BulkScenarioCreate, BulkScenarioResponse,
    ScenarioValidationResponse, ScenarioExecutionRequest, 
    ScenarioExecutionProgress, ScenarioState, TimePeriod
)
from app.db.models.scenario import Scenario
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ScenarioService:
    """Service for managing scenario business operations"""
    
    def __init__(self):
        self.scenario_repo = ScenarioRepository()
        self.analysis_repo = AnalysisRepository()
        self.model_repo = ModelRepository()
        self.user_repo = UserRepository()
    
    def create_scenario(
        self,
        db: Session,
        tenant_id: UUID,
        scenario_create: ScenarioCreate,
        current_user_id: UUID
    ) -> ScenarioRead:
        """
        Create a new scenario with business validation.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            scenario_create: Scenario creation data
            current_user_id: ID of user creating the scenario
            
        Returns:
            Created scenario
            
        Raises:
            ValueError: If validation fails
            PermissionError: If user lacks permission
        """
        try:
            # Validate the parent analysis exists and belongs to tenant
            analysis = self.analysis_repo.get_by_id(db, tenant_id, scenario_create.analysis_id)
            if not analysis:
                raise ValueError(f"Analysis {scenario_create.analysis_id} not found in tenant {tenant_id}")
            
            # Validate user exists and belongs to tenant
            user = self.user_repo.get_by_id(db, tenant_id, current_user_id)
            if not user:
                raise ValueError(f"User {current_user_id} not found in tenant {tenant_id}")
            
            # Check name uniqueness within analysis
            existing_scenario = self.scenario_repo.find_by_name_and_analysis_id(
                db, tenant_id, scenario_create.analysis_id, scenario_create.name
            )
            if existing_scenario:
                raise ValueError(f"Scenario with name '{scenario_create.name}' already exists in this analysis")
            
            # TODO: Add permission checking here when permission system is integrated
            # For now, assume user can create scenarios for any analysis in their tenant
            
            # Inherit defaults from parent analysis if not provided
            scenario_data = scenario_create.model_dump()
            
            # Use analysis defaults if not explicitly set
            if scenario_create.reps == 1:  # Default value, might want to inherit
                scenario_data["reps"] = analysis.default_reps
            
            if scenario_create.time_period == TimePeriod.DAILY:  # Default value, might want to inherit
                scenario_data["time_period"] = analysis.default_time_period
            
            # Set additional fields
            scenario_data["created_by_user_id"] = current_user_id
            scenario_data["state"] = ScenarioState.NOT_READY_TO_RUN
            scenario_data["total_reps"] = scenario_data["reps"]  # Initialize total_reps
            
            # Create the scenario
            scenario = self.scenario_repo.create(
                db=db,
                obj_in=scenario_data,
                tenant_id=tenant_id
            )
            
            logger.info(f"Created scenario: {scenario.name} (ID: {scenario.id}) by user {current_user_id}")
            
            return ScenarioRead.model_validate(scenario)
            
        except Exception as e:
            logger.error(f"Error creating scenario: {e}")
            raise
    
    def get_scenario_by_id(
        self,
        db: Session,
        tenant_id: UUID,
        scenario_id: UUID,
        current_user_id: Optional[UUID] = None
    ) -> Optional[ScenarioRead]:
        """
        Get scenario by ID with optional permission checking.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            scenario_id: Scenario ID to retrieve
            current_user_id: Optional user ID for permission checking
            
        Returns:
            Scenario if found and accessible, None otherwise
        """
        scenario = self.scenario_repo.get_by_id(db, tenant_id, scenario_id)
        if not scenario:
            return None
        
        # TODO: Add permission checking here when permission system is integrated
        # For now, return scenario if it exists in the tenant
        
        return ScenarioRead.model_validate(scenario)
    
    def update_scenario(
        self,
        db: Session,
        tenant_id: UUID,
        scenario_id: UUID,
        scenario_update: ScenarioUpdate,
        current_user_id: UUID
    ) -> Optional[ScenarioRead]:
        """
        Update a scenario with authorization and validation.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            scenario_id: Scenario ID to update
            scenario_update: Update data
            current_user_id: User performing the update
            
        Returns:
            Updated scenario if successful, None if not found
            
        Raises:
            PermissionError: If user lacks permission to update
            ValueError: If validation fails
        """
        try:
            # Get the existing scenario
            scenario = self.scenario_repo.get_by_id(db, tenant_id, scenario_id)
            if not scenario:
                return None
            
            # Check if scenario can be modified
            if not scenario.can_be_modified():
                raise ValueError(f"Scenario cannot be modified while in '{scenario.state}' state")
            
            # Check if user has permission to update (creator or admin)
            if not scenario.is_editable_by_user(current_user_id):
                raise PermissionError("User does not have permission to update this scenario")
            
            # Validate name uniqueness if name is being updated
            if scenario_update.name and scenario_update.name != scenario.name:
                existing_scenario = self.scenario_repo.find_by_name_and_analysis_id(
                    db, tenant_id, scenario.analysis_id, scenario_update.name
                )
                if existing_scenario and existing_scenario.id != scenario_id:
                    raise ValueError(f"Scenario with name '{scenario_update.name}' already exists in this analysis")
            
            # Prepare update data (only include provided fields)
            update_data = scenario_update.model_dump(exclude_unset=True)
            
            # If reps is updated, also update total_reps for consistency
            if 'reps' in update_data:
                update_data['total_reps'] = update_data['reps']
            
            # Update the scenario
            updated_scenario = self.scenario_repo.update(
                db=db,
                db_obj=scenario,
                obj_in=update_data
            )
            
            logger.info(f"Updated scenario: {updated_scenario.name} (ID: {scenario_id}) by user {current_user_id}")
            
            return ScenarioRead.model_validate(updated_scenario)
            
        except Exception as e:
            logger.error(f"Error updating scenario {scenario_id}: {e}")
            raise
    
    def delete_scenario(
        self,
        db: Session,
        tenant_id: UUID,
        scenario_id: UUID,
        current_user_id: UUID
    ) -> bool:
        """
        Soft delete a scenario with authorization checking.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            scenario_id: Scenario ID to delete
            current_user_id: User performing the deletion
            
        Returns:
            True if deleted successfully, False if not found
            
        Raises:
            PermissionError: If user lacks permission to delete
            ValueError: If scenario cannot be deleted
        """
        try:
            # Get the existing scenario
            scenario = self.scenario_repo.get_by_id(db, tenant_id, scenario_id)
            if not scenario:
                return False
            
            # Check if scenario is in a deletable state
            if scenario.is_running():
                raise ValueError("Cannot delete a running scenario. Cancel it first.")
            
            # Check if user has permission to delete (creator or admin)
            if not scenario.is_editable_by_user(current_user_id):
                raise PermissionError("User does not have permission to delete this scenario")
            
            # Soft delete the scenario
            deleted = self.scenario_repo.soft_delete(db, tenant_id, scenario_id)
            
            if deleted:
                logger.info(f"Deleted scenario: {scenario.name} (ID: {scenario_id}) by user {current_user_id}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting scenario {scenario_id}: {e}")
            raise
    
    def list_scenarios_for_analysis(
        self,
        db: Session,
        tenant_id: UUID,
        analysis_id: UUID,
        skip: int = 0,
        limit: int = 100,
        current_user_id: Optional[UUID] = None
    ) -> List[ScenarioSummary]:
        """
        List all scenarios for a specific analysis.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            analysis_id: Analysis ID to get scenarios for
            skip: Pagination offset
            limit: Maximum results
            current_user_id: Optional user ID for permission filtering
            
        Returns:
            List of scenario summaries
        """
        try:
            # Validate analysis exists
            analysis = self.analysis_repo.get_by_id(db, tenant_id, analysis_id)
            if not analysis:
                raise ValueError(f"Analysis {analysis_id} not found in tenant {tenant_id}")
            
            # Get scenarios for the analysis
            scenarios = self.scenario_repo.get_scenarios_by_analysis_id(
                db, tenant_id, analysis_id, skip=skip, limit=limit
            )
            
            # TODO: Filter by permissions when permission system is integrated
            # For now, return all scenarios in the tenant
            
            return [ScenarioSummary.model_validate(scenario) for scenario in scenarios]
            
        except Exception as e:
            logger.error(f"Error listing scenarios for analysis {analysis_id}: {e}")
            raise
    
    def list_scenarios_by_user(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ScenarioSummary]:
        """
        List scenarios created by a specific user.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            user_id: User ID to get scenarios for
            skip: Pagination offset
            limit: Maximum results
            
        Returns:
            List of scenario summaries
        """
        try:
            scenarios = self.scenario_repo.get_scenarios_by_user_id(
                db, tenant_id, user_id, skip=skip, limit=limit
            )
            
            return [ScenarioSummary.model_validate(scenario) for scenario in scenarios]
            
        except Exception as e:
            logger.error(f"Error listing scenarios for user {user_id}: {e}")
            raise
    
    # === Execution Lifecycle Methods ===
    
    def prepare_scenario_for_run(
        self,
        db: Session,
        tenant_id: UUID,
        scenario_id: UUID,
        current_user_id: UUID
    ) -> bool:
        """
        Prepare scenario for execution by setting state to 'ready_to_run'.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            scenario_id: Scenario ID to prepare
            current_user_id: User requesting the preparation
            
        Returns:
            True if successfully prepared
            
        Raises:
            ValueError: If scenario cannot be prepared
            PermissionError: If user lacks permission
        """
        try:
            scenario = self.scenario_repo.get_by_id(db, tenant_id, scenario_id)
            if not scenario:
                raise ValueError(f"Scenario {scenario_id} not found")
            
            # Check permissions
            if not scenario.is_editable_by_user(current_user_id):
                raise PermissionError("User does not have permission to prepare this scenario")
            
            # Check if scenario can be prepared
            if not scenario.can_be_executed():
                raise ValueError(f"Scenario in '{scenario.state}' state cannot be prepared for execution")
            
            # Reset execution state and prepare
            scenario.reset_execution_state()
            
            # Update to ready state
            updated_scenario = self.scenario_repo.update_scenario_status(
                db, tenant_id, scenario_id, ScenarioState.READY_TO_RUN
            )
            
            if updated_scenario:
                logger.info(f"Prepared scenario for run: {scenario.name} (ID: {scenario_id})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error preparing scenario {scenario_id}: {e}")
            raise
    
    def start_scenario_run(
        self,
        db: Session,
        tenant_id: UUID,
        scenario_id: UUID,
        execution_request: Optional[ScenarioExecutionRequest] = None
    ) -> bool:
        """
        Start scenario execution by setting state to 'is_running'.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            scenario_id: Scenario ID to start
            execution_request: Optional execution parameters
            
        Returns:
            True if successfully started
            
        Raises:
            ValueError: If scenario cannot be started
        """
        try:
            scenario = self.scenario_repo.get_by_id(db, tenant_id, scenario_id)
            if not scenario:
                raise ValueError(f"Scenario {scenario_id} not found")
            
            # Check if scenario can be started
            if scenario.state != ScenarioState.READY_TO_RUN:
                raise ValueError(f"Scenario must be in 'ready_to_run' state to start. Current state: {scenario.state}")
            
            # Prepare progress details
            progress_details = {
                'started_at': datetime.now(timezone.utc),
                'current_rep': 0,
                'total_reps': scenario.reps,
                'progress_percentage': 0.0
            }
            
            # Override reps if provided in execution request
            if execution_request and execution_request.override_reps:
                progress_details['total_reps'] = execution_request.override_reps
            
            # Update to running state
            updated_scenario = self.scenario_repo.update_scenario_status(
                db, tenant_id, scenario_id, ScenarioState.IS_RUNNING, progress_details
            )
            
            if updated_scenario:
                logger.info(f"Started scenario execution: {scenario.name} (ID: {scenario_id})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error starting scenario {scenario_id}: {e}")
            raise
    
    def update_scenario_progress(
        self,
        db: Session,
        tenant_id: UUID,
        scenario_id: UUID,
        current_rep: int,
        total_reps: int,
        progress_percentage: float
    ) -> bool:
        """
        Update scenario execution progress.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            scenario_id: Scenario ID to update
            current_rep: Current replication number
            total_reps: Total replications to run
            progress_percentage: Progress percentage (0-100)
            
        Returns:
            True if successfully updated
        """
        try:
            scenario = self.scenario_repo.get_by_id(db, tenant_id, scenario_id)
            if not scenario:
                raise ValueError(f"Scenario {scenario_id} not found")
            
            # Validate progress data
            if current_rep < 0 or current_rep > total_reps:
                raise ValueError(f"Invalid current_rep: {current_rep} (total: {total_reps})")
            
            if progress_percentage < 0 or progress_percentage > 100:
                raise ValueError(f"Invalid progress_percentage: {progress_percentage}")
            
            # Update progress
            progress_details = {
                'current_rep': current_rep,
                'total_reps': total_reps,
                'progress_percentage': progress_percentage
            }
            
            updated_scenario = self.scenario_repo.update_scenario_status(
                db, tenant_id, scenario_id, scenario.state, progress_details
            )
            
            return updated_scenario is not None
            
        except Exception as e:
            logger.error(f"Error updating scenario progress {scenario_id}: {e}")
            raise
    
    def complete_scenario_run(
        self,
        db: Session,
        tenant_id: UUID,
        scenario_id: UUID,
        execution_time_ms: int,
        blob_storage_path: str
    ) -> bool:
        """
        Complete scenario execution successfully.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            scenario_id: Scenario ID to complete
            execution_time_ms: Total execution time in milliseconds
            blob_storage_path: Path to results in blob storage
            
        Returns:
            True if successfully completed
        """
        try:
            scenario = self.scenario_repo.get_by_id(db, tenant_id, scenario_id)
            if not scenario:
                raise ValueError(f"Scenario {scenario_id} not found")
            
            # Prepare completion details
            progress_details = {
                'completed_at': datetime.now(timezone.utc),
                'execution_time_ms': execution_time_ms,
                'blob_storage_path': blob_storage_path,
                'progress_percentage': 100.0,
                'current_rep': scenario.total_reps or scenario.reps
            }
            
            # Update to success state
            updated_scenario = self.scenario_repo.update_scenario_status(
                db, tenant_id, scenario_id, ScenarioState.RAN_SUCCESS, progress_details
            )
            
            if updated_scenario:
                logger.info(f"Completed scenario execution: {scenario.name} (ID: {scenario_id}) in {execution_time_ms}ms")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error completing scenario {scenario_id}: {e}")
            raise
    
    def fail_scenario_run(
        self,
        db: Session,
        tenant_id: UUID,
        scenario_id: UUID,
        error_message: str,
        error_details: Optional[str] = None,
        error_stack_trace: Optional[str] = None
    ) -> bool:
        """
        Mark scenario execution as failed with error information.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            scenario_id: Scenario ID to fail
            error_message: User-friendly error message
            error_details: Technical error details
            error_stack_trace: Full stack trace
            
        Returns:
            True if successfully marked as failed
        """
        try:
            scenario = self.scenario_repo.get_by_id(db, tenant_id, scenario_id)
            if not scenario:
                raise ValueError(f"Scenario {scenario_id} not found")
            
            # Calculate execution time if scenario was running
            execution_time_ms = None
            if scenario.started_at:
                execution_duration = datetime.now(timezone.utc) - scenario.started_at
                execution_time_ms = int(execution_duration.total_seconds() * 1000)
            
            # Prepare failure details
            progress_details = {
                'completed_at': datetime.now(timezone.utc),
                'error_message': error_message,
                'error_details': error_details,
                'error_stack_trace': error_stack_trace
            }
            
            if execution_time_ms:
                progress_details['execution_time_ms'] = execution_time_ms
            
            # Update to error state
            updated_scenario = self.scenario_repo.update_scenario_status(
                db, tenant_id, scenario_id, ScenarioState.RAN_WITH_ERRORS, progress_details
            )
            
            if updated_scenario:
                logger.error(f"Failed scenario execution: {scenario.name} (ID: {scenario_id}) - {error_message}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error failing scenario {scenario_id}: {e}")
            raise
    
    def cancel_scenario_run(
        self,
        db: Session,
        tenant_id: UUID,
        scenario_id: UUID,
        current_user_id: UUID
    ) -> bool:
        """
        Cancel a running scenario.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            scenario_id: Scenario ID to cancel
            current_user_id: User requesting cancellation
            
        Returns:
            True if successfully cancelled
            
        Raises:
            PermissionError: If user lacks permission
            ValueError: If scenario cannot be cancelled
        """
        try:
            scenario = self.scenario_repo.get_by_id(db, tenant_id, scenario_id)
            if not scenario:
                raise ValueError(f"Scenario {scenario_id} not found")
            
            # Check permissions
            if not scenario.is_editable_by_user(current_user_id):
                raise PermissionError("User does not have permission to cancel this scenario")
            
            # Check if scenario can be cancelled
            if scenario.state != ScenarioState.IS_RUNNING:
                raise ValueError(f"Can only cancel running scenarios. Current state: {scenario.state}")
            
            # Update to cancelling state (external system should handle actual cancellation)
            updated_scenario = self.scenario_repo.update_scenario_status(
                db, tenant_id, scenario_id, ScenarioState.CANCELLING
            )
            
            if updated_scenario:
                logger.info(f"Initiated cancellation for scenario: {scenario.name} (ID: {scenario_id})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling scenario {scenario_id}: {e}")
            raise
    
    # === Additional Service Methods ===
    
    def search_scenarios(
        self,
        db: Session,
        tenant_id: UUID,
        query: ScenarioQuery,
        current_user_id: Optional[UUID] = None
    ) -> List[ScenarioSummary]:
        """
        Search scenarios with advanced filtering.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            query: Search query parameters
            current_user_id: Optional user ID for permission filtering
            
        Returns:
            List of matching scenario summaries
        """
        try:
            scenarios = []
            
            # Apply different search strategies based on query parameters
            if query.name_contains:
                # Text search
                scenarios = self.scenario_repo.search_scenarios_by_name(
                    db, tenant_id, query.name_contains, skip=query.skip, limit=query.limit
                )
            elif query.analysis_id:
                # Analysis-specific search
                scenarios = self.scenario_repo.get_scenarios_by_analysis_id(
                    db, tenant_id, query.analysis_id, skip=query.skip, limit=query.limit
                )
            elif query.created_by_user_id:
                # User-specific search
                scenarios = self.scenario_repo.get_scenarios_by_user_id(
                    db, tenant_id, query.created_by_user_id, skip=query.skip, limit=query.limit
                )
            elif query.state:
                # State-specific search
                scenarios = self.scenario_repo.get_scenarios_by_state(
                    db, tenant_id, query.state, skip=query.skip, limit=query.limit
                )
            elif query.time_period:
                # Time period search
                scenarios = self.scenario_repo.get_scenarios_by_time_period(
                    db, tenant_id, query.time_period, skip=query.skip, limit=query.limit
                )
            elif query.has_errors is not None:
                # Error status search
                if query.has_errors:
                    scenarios = self.scenario_repo.get_scenarios_with_errors(
                        db, tenant_id, skip=query.skip, limit=query.limit
                    )
                else:
                    # Get scenarios without errors (successful or not completed)
                    scenarios = self.scenario_repo.get_all(
                        db, tenant_id, skip=query.skip, limit=query.limit
                    )
                    scenarios = [s for s in scenarios if not s.has_errors()]
            elif query.completed_after or query.completed_before:
                # Date range search
                start_date = query.completed_after or datetime.min.replace(tzinfo=timezone.utc)
                end_date = query.completed_before or datetime.now(timezone.utc)
                scenarios = self.scenario_repo.get_scenarios_completed_between(
                    db, tenant_id, start_date, end_date, skip=query.skip, limit=query.limit
                )
            else:
                # General listing
                scenarios = self.scenario_repo.get_all(
                    db, tenant_id, skip=query.skip, limit=query.limit
                )
            
            # TODO: Apply permission filtering when permission system is integrated
            
            return [ScenarioSummary.model_validate(scenario) for scenario in scenarios]
            
        except Exception as e:
            logger.error(f"Error searching scenarios: {e}")
            raise
    
    def copy_scenario(
        self,
        db: Session,
        tenant_id: UUID,
        copy_request: ScenarioCopyRequest,
        current_user_id: UUID
    ) -> ScenarioRead:
        """
        Copy an existing scenario with a new name.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            copy_request: Copy request parameters
            current_user_id: User performing the copy
            
        Returns:
            Newly created scenario copy
            
        Raises:
            ValueError: If source scenario not found or validation fails
            PermissionError: If user lacks permission
        """
        try:
            # Get the source scenario (source_scenario_id should be set by the API layer)
            source_scenario_id = getattr(copy_request, 'source_scenario_id', None)
            if not source_scenario_id:
                raise ValueError("Source scenario ID is required for copying")
                
            source_scenario = self.scenario_repo.get_by_id(db, tenant_id, source_scenario_id)
            if not source_scenario:
                raise ValueError(f"Source scenario {source_scenario_id} not found")
            
            # TODO: Check if user has permission to read source scenario
            
            # Determine target analysis
            target_analysis_id = copy_request.target_analysis_id or source_scenario.analysis_id
            
            # Validate target analysis exists
            target_analysis = self.analysis_repo.get_by_id(db, tenant_id, target_analysis_id)
            if not target_analysis:
                raise ValueError(f"Target analysis {target_analysis_id} not found")
            
            # Create the copy
            scenario_create = ScenarioCreate(
                name=copy_request.new_name,
                description=copy_request.new_description or source_scenario.description,
                analysis_id=target_analysis_id,
                reps=source_scenario.reps,
                time_period=TimePeriod(source_scenario.time_period)
            )
            
            copied_scenario = self.create_scenario(
                db, tenant_id, scenario_create, current_user_id
            )
            
            logger.info(f"Copied scenario: {source_scenario.name} -> {copied_scenario.name} by user {current_user_id}")
            
            # TODO: Copy item profiles if requested when item profiles are implemented
            
            return copied_scenario
            
        except Exception as e:
            logger.error(f"Error copying scenario: {e}")
            raise
    
    def get_scenario_statistics(
        self,
        db: Session,
        tenant_id: UUID,
        analysis_id: Optional[UUID] = None
    ) -> ScenarioStatistics:
        """
        Get statistical information about scenarios.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            analysis_id: Optional analysis ID to filter statistics
            
        Returns:
            Scenario statistics
        """
        try:
            stats_data = self.scenario_repo.get_scenario_statistics(db, tenant_id, analysis_id)
            
            # Get recent scenarios
            recent_scenarios = self.scenario_repo.get_recent_scenarios(db, tenant_id, days=7, limit=5)
            recent_summaries = [ScenarioSummary.model_validate(scenario) for scenario in recent_scenarios]
            
            return ScenarioStatistics(
                total_scenarios=stats_data["total_scenarios"],
                scenarios_by_state=stats_data["scenarios_by_state"],
                scenarios_by_analysis=stats_data["scenarios_by_analysis"],
                scenarios_by_time_period=stats_data["scenarios_by_time_period"],
                average_execution_time_ms=stats_data["average_execution_time_ms"],
                success_rate_percentage=stats_data["success_rate_percentage"],
                most_common_errors=stats_data["most_common_errors"],
                recent_scenarios=recent_summaries,
                period_start=datetime.now(timezone.utc).replace(day=1),  # Start of current month
                period_end=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Error getting scenario statistics: {e}")
            raise
    
    def validate_scenario_creation(
        self,
        db: Session,
        tenant_id: UUID,
        scenario_create: ScenarioCreate,
        current_user_id: UUID
    ) -> ScenarioValidationResponse:
        """
        Validate scenario creation without actually creating it.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            scenario_create: Scenario creation data to validate
            current_user_id: User who would create the scenario
            
        Returns:
            Validation response with errors and warnings
        """
        validation_errors = []
        warnings = []
        
        # Check analysis exists
        analysis_exists = self.analysis_repo.exists(db, tenant_id, scenario_create.analysis_id)
        if not analysis_exists:
            validation_errors.append(f"Analysis {scenario_create.analysis_id} not found")
        
        # Check user exists
        user_exists = self.user_repo.exists(db, tenant_id, current_user_id)
        if not user_exists:
            validation_errors.append(f"User {current_user_id} not found")
        
        # Check name availability
        name_available = True
        if analysis_exists:  # Only check if analysis exists
            name_available = self.scenario_repo.check_name_availability(
                db, tenant_id, scenario_create.analysis_id, scenario_create.name
            )
            if not name_available:
                validation_errors.append(f"Scenario name '{scenario_create.name}' already exists in this analysis")
        
        # Add warnings for high replication counts
        if scenario_create.reps > 1000:
            warnings.append(f"High replication count ({scenario_create.reps}) may impact performance")
        
        return ScenarioValidationResponse(
            is_valid=len(validation_errors) == 0,
            validation_errors=validation_errors,
            warnings=warnings,
            name_available=name_available,
            analysis_exists=analysis_exists,
            user_has_permission=user_exists,  # Simplified for now
            analysis_allows_scenarios=True  # Always true for now
        )
    
    def bulk_create_scenarios(
        self,
        db: Session,
        tenant_id: UUID,
        bulk_request: BulkScenarioCreate,
        current_user_id: UUID
    ) -> BulkScenarioResponse:
        """
        Create multiple scenarios in bulk.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            bulk_request: Bulk creation request
            current_user_id: User creating the scenarios
            
        Returns:
            Bulk operation response with success/failure details
        """
        successful_scenarios = []
        failed_scenarios = []
        
        for scenario_base in bulk_request.scenarios:
            try:
                # Convert ScenarioBase to ScenarioCreate
                scenario_create = ScenarioCreate(
                    analysis_id=bulk_request.analysis_id,
                    **scenario_base.model_dump()
                )
                
                created_scenario = self.create_scenario(
                    db, tenant_id, scenario_create, current_user_id
                )
                successful_scenarios.append(created_scenario.id)
            except Exception as e:
                failed_scenarios.append({
                    "name": scenario_base.name,
                    "error": str(e)
                })
        
        return BulkScenarioResponse(
            successful_scenarios=successful_scenarios,
            failed_scenarios=failed_scenarios,
            total_requested=len(bulk_request.scenarios),
            total_successful=len(successful_scenarios),
            total_failed=len(failed_scenarios)
        )


# Dependency injection function
def get_scenario_service() -> ScenarioService:
    """Get ScenarioService instance for dependency injection."""
    return ScenarioService()