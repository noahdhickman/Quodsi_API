# app/repositories/scenario_repository.py
"""
Repository for Scenario data access operations.

Provides data access methods for scenario management with proper tenant isolation,
execution state tracking, and efficient querying patterns.
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc, asc, case, text
from sqlalchemy.orm import Session, joinedload

from app.repositories.base import BaseRepository
from app.db.models.scenario import Scenario
from app.schemas.scenario import ScenarioState, TimePeriod


class ScenarioRepository(BaseRepository[Scenario]):
    """Repository for scenario data access with tenant isolation"""

    def __init__(self):
        super().__init__(Scenario)

    def get_scenarios_by_analysis_id(
        self,
        db: Session,
        tenant_id: UUID,
        analysis_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Scenario]:
        """
        Get all scenarios belonging to a specific analysis.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            analysis_id: Analysis ID to get scenarios for
            skip: Pagination offset
            limit: Maximum results
            
        Returns:
            List of scenarios belonging to the analysis
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.analysis_id == analysis_id,
                    self.model.is_deleted == False
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_scenarios_by_state(
        self,
        db: Session,
        tenant_id: UUID,
        state: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Scenario]:
        """
        Get scenarios by execution state.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            state: Scenario state to filter by
            skip: Pagination offset
            limit: Maximum results
            
        Returns:
            List of scenarios in the specified state
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.state == state,
                    self.model.is_deleted == False
                )
            )
            .order_by(desc(self.model.updated_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_scenarios_by_user_id(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Scenario]:
        """
        Get scenarios created by a specific user.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            user_id: User ID to get scenarios for
            skip: Pagination offset
            limit: Maximum results
            
        Returns:
            List of scenarios created by the user
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.created_by_user_id == user_id,
                    self.model.is_deleted == False
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_scenarios_by_time_period(
        self,
        db: Session,
        tenant_id: UUID,
        time_period: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Scenario]:
        """
        Get scenarios by time period.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            time_period: Time period to filter by
            skip: Pagination offset
            limit: Maximum results
            
        Returns:
            List of scenarios with the specified time period
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.time_period == time_period,
                    self.model.is_deleted == False
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_scenarios_by_name(
        self,
        db: Session,
        tenant_id: UUID,
        name_pattern: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Scenario]:
        """
        Search scenarios by name pattern.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            name_pattern: Pattern to search for in scenario names
            skip: Pagination offset
            limit: Maximum results
            
        Returns:
            List of scenarios matching the name pattern
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.name.ilike(f"%{name_pattern}%"),
                    self.model.is_deleted == False
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_scenarios_completed_between(
        self,
        db: Session,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[Scenario]:
        """
        Get scenarios completed within a date range.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            start_date: Start of date range
            end_date: End of date range
            skip: Pagination offset
            limit: Maximum results
            
        Returns:
            List of scenarios completed in the date range
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.completed_at.between(start_date, end_date),
                    self.model.is_deleted == False
                )
            )
            .order_by(desc(self.model.completed_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_scenarios_with_errors(
        self,
        db: Session,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Scenario]:
        """
        Get scenarios that completed with errors.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            skip: Pagination offset
            limit: Maximum results
            
        Returns:
            List of scenarios that ran with errors
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.state == ScenarioState.RAN_WITH_ERRORS,
                    self.model.is_deleted == False
                )
            )
            .order_by(desc(self.model.completed_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_running_scenarios(
        self,
        db: Session,
        tenant_id: UUID
    ) -> List[Scenario]:
        """
        Get all currently running scenarios for a tenant.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            
        Returns:
            List of currently running scenarios
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.state == ScenarioState.IS_RUNNING,
                    self.model.is_deleted == False
                )
            )
            .order_by(asc(self.model.started_at))
            .all()
        )

    def update_scenario_status(
        self,
        db: Session,
        tenant_id: UUID,
        scenario_id: UUID,
        new_state: str,
        progress_details: Optional[Dict[str, Any]] = None
    ) -> Optional[Scenario]:
        """
        Update scenario execution status and progress.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            scenario_id: Scenario ID to update
            new_state: New execution state
            progress_details: Additional progress information
            
        Returns:
            Updated scenario or None if not found
        """
        scenario = self.get_by_id(db, tenant_id, scenario_id)
        if not scenario:
            return None

        # Update state
        scenario.state = new_state

        # Update progress details if provided
        if progress_details:
            if 'current_rep' in progress_details:
                scenario.current_rep = progress_details['current_rep']
            if 'total_reps' in progress_details:
                scenario.total_reps = progress_details['total_reps']
            if 'progress_percentage' in progress_details:
                scenario.progress_percentage = progress_details['progress_percentage']
            if 'started_at' in progress_details:
                scenario.started_at = progress_details['started_at']
            if 'completed_at' in progress_details:
                scenario.completed_at = progress_details['completed_at']
            if 'execution_time_ms' in progress_details:
                scenario.execution_time_ms = progress_details['execution_time_ms']
            if 'error_message' in progress_details:
                scenario.error_message = progress_details['error_message']
            if 'error_details' in progress_details:
                scenario.error_details = progress_details['error_details']
            if 'error_stack_trace' in progress_details:
                scenario.error_stack_trace = progress_details['error_stack_trace']
            if 'blob_storage_path' in progress_details:
                scenario.blob_storage_path = progress_details['blob_storage_path']

        # Update timestamp
        scenario.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(scenario)
        return scenario

    def find_by_name_and_analysis_id(
        self,
        db: Session,
        tenant_id: UUID,
        analysis_id: UUID,
        name: str
    ) -> Optional[Scenario]:
        """
        Find scenario by name within an analysis.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            analysis_id: Analysis ID
            name: Scenario name to search for
            
        Returns:
            Scenario if found, None otherwise
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.analysis_id == analysis_id,
                    self.model.name == name,
                    self.model.is_deleted == False
                )
            )
            .first()
        )

    def check_name_availability(
        self,
        db: Session,
        tenant_id: UUID,
        analysis_id: UUID,
        name: str,
        exclude_scenario_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if a scenario name is available within an analysis.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            analysis_id: Analysis ID
            name: Name to check
            exclude_scenario_id: Scenario ID to exclude from check (for updates)
            
        Returns:
            True if name is available, False otherwise
        """
        query = db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.analysis_id == analysis_id,
                self.model.name == name,
                self.model.is_deleted == False
            )
        )

        if exclude_scenario_id:
            query = query.filter(self.model.id != exclude_scenario_id)

        return query.first() is None

    def get_scenario_statistics(
        self,
        db: Session,
        tenant_id: UUID,
        analysis_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive scenario statistics.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            analysis_id: Optional analysis ID to filter statistics
            
        Returns:
            Dictionary with scenario statistics
        """
        base_query = db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.is_deleted == False
            )
        )

        if analysis_id:
            base_query = base_query.filter(self.model.analysis_id == analysis_id)

        # Total scenarios
        total_scenarios = base_query.count()

        # Scenarios by state
        state_counts = (
            base_query
            .with_entities(self.model.state, func.count(self.model.id))
            .group_by(self.model.state)
            .all()
        )
        scenarios_by_state = {state: count for state, count in state_counts}

        # Scenarios by time period
        period_counts = (
            base_query
            .with_entities(self.model.time_period, func.count(self.model.id))
            .group_by(self.model.time_period)
            .all()
        )
        scenarios_by_time_period = {period: count for period, count in period_counts}

        # Average execution time for completed scenarios
        completed_scenarios = base_query.filter(
            self.model.execution_time_ms.isnot(None)
        )
        avg_execution_time = (
            completed_scenarios
            .with_entities(func.avg(self.model.execution_time_ms))
            .scalar()
        )

        # Success rate
        total_completed = base_query.filter(
            self.model.state.in_([ScenarioState.RAN_SUCCESS, ScenarioState.RAN_WITH_ERRORS])
        ).count()
        
        successful_scenarios = base_query.filter(
            self.model.state == ScenarioState.RAN_SUCCESS
        ).count()

        success_rate = (successful_scenarios / total_completed * 100) if total_completed > 0 else None

        # Most common errors
        error_counts = (
            base_query
            .filter(self.model.error_message.isnot(None))
            .with_entities(self.model.error_message, func.count(self.model.id))
            .group_by(self.model.error_message)
            .order_by(desc(func.count(self.model.id)))
            .limit(5)
            .all()
        )
        most_common_errors = [
            {"error_message": error, "count": count}
            for error, count in error_counts
        ]

        # Scenarios by analysis (if not filtered by specific analysis)
        scenarios_by_analysis = {}
        if not analysis_id:
            analysis_counts = (
                base_query
                .with_entities(self.model.analysis_id, func.count(self.model.id))
                .group_by(self.model.analysis_id)
                .all()
            )
            scenarios_by_analysis = {str(analysis_id): count for analysis_id, count in analysis_counts}

        return {
            "total_scenarios": total_scenarios,
            "scenarios_by_state": scenarios_by_state,
            "scenarios_by_time_period": scenarios_by_time_period,
            "scenarios_by_analysis": scenarios_by_analysis,
            "average_execution_time_ms": float(avg_execution_time) if avg_execution_time else None,
            "success_rate_percentage": success_rate,
            "most_common_errors": most_common_errors
        }

    def get_recent_scenarios(
        self,
        db: Session,
        tenant_id: UUID,
        days: int = 7,
        limit: int = 10
    ) -> List[Scenario]:
        """
        Get recently created scenarios.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            days: Number of days to look back
            limit: Maximum results
            
        Returns:
            List of recently created scenarios
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.created_at >= cutoff_date,
                    self.model.is_deleted == False
                )
            )
            .order_by(desc(self.model.created_at))
            .limit(limit)
            .all()
        )

    def bulk_update_state(
        self,
        db: Session,
        tenant_id: UUID,
        scenario_ids: List[UUID],
        new_state: str,
        progress_details: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Bulk update multiple scenarios' states.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            scenario_ids: List of scenario IDs to update
            new_state: New state for all scenarios
            progress_details: Additional progress information
            
        Returns:
            Number of scenarios updated
        """
        query = db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.id.in_(scenario_ids),
                self.model.is_deleted == False
            )
        )

        update_values = {
            "state": new_state,
            "updated_at": datetime.now(timezone.utc)
        }

        if progress_details:
            update_values.update(progress_details)

        updated_count = query.update(update_values, synchronize_session=False)
        db.commit()
        
        return updated_count

    def get_execution_queue(
        self,
        db: Session,
        tenant_id: UUID,
        limit: int = 50
    ) -> List[Scenario]:
        """
        Get scenarios ready for execution in priority order.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            limit: Maximum scenarios to return
            
        Returns:
            List of scenarios ready for execution
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.state == ScenarioState.READY_TO_RUN,
                    self.model.is_deleted == False
                )
            )
            .order_by(asc(self.model.created_at))  # FIFO execution order
            .limit(limit)
            .all()
        )