# app/repositories/analysis_repository.py
"""
Repository for Analysis entity with analysis-specific operations.

Provides tenant-scoped CRUD operations plus analysis-specific queries
for finding analyses by model, user, time period, and other criteria.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func
from datetime import datetime

from app.repositories.base import BaseRepository
from app.db.models.analysis import Analysis
from app.schemas.analysis import TimePeriod


class AnalysisRepository(BaseRepository[Analysis]):
    """
    Repository for Analysis entity with analysis-specific operations.

    Provides tenant-scoped CRUD operations plus analysis-specific queries
    like finding analyses by model, user, time period, and name patterns.
    """

    def __init__(self):
        """Initialize AnalysisRepository with Analysis model."""
        super().__init__(Analysis)

    def get_analyses_by_model_id(
        self, 
        db: Session, 
        tenant_id: UUID, 
        model_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Analysis]:
        """
        Get all analyses for a specific model within a tenant.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            model_id: Model UUID to filter by
            skip: Pagination offset
            limit: Maximum results to return

        Returns:
            List of analyses for the specified model
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.model_id == model_id,
                    self.model.is_deleted == False,
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_analyses_by_user_id(
        self, 
        db: Session, 
        tenant_id: UUID, 
        user_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Analysis]:
        """
        Get all analyses created by a specific user within a tenant.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            user_id: User UUID who created the analyses
            skip: Pagination offset
            limit: Maximum results to return

        Returns:
            List of analyses created by the user
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

    def find_by_name_and_model_id(
        self, 
        db: Session, 
        tenant_id: UUID, 
        model_id: UUID, 
        name: str
    ) -> Optional[Analysis]:
        """
        Find analysis by name and model ID (supports unique constraint validation).

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            model_id: Model UUID
            name: Analysis name to search for

        Returns:
            Analysis if found, None otherwise
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.model_id == model_id,
                    self.model.name == name,
                    self.model.is_deleted == False,
                )
            )
            .first()
        )

    def get_analyses_by_time_period(
        self, 
        db: Session, 
        tenant_id: UUID, 
        time_period: TimePeriod, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Analysis]:
        """
        Get analyses filtered by default time period within a tenant.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            time_period: Time period to filter by
            skip: Pagination offset
            limit: Maximum results to return

        Returns:
            List of analyses with specified time period
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.default_time_period == time_period.value,
                    self.model.is_deleted == False,
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_analyses_by_name(
        self, 
        db: Session, 
        tenant_id: UUID, 
        name_query: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Analysis]:
        """
        Search analyses by name using case-insensitive partial matching.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            name_query: Search term for analysis name
            skip: Pagination offset
            limit: Maximum results to return

        Returns:
            List of analyses matching the name query
        """
        return self.search(
            db=db,
            tenant_id=tenant_id,
            search_term=name_query,
            search_fields=["name", "description"],
            skip=skip,
            limit=limit,
        )

    def get_analyses_with_relationships(
        self, 
        db: Session, 
        tenant_id: UUID, 
        skip: int = 0, 
        limit: int = 100,
        include_model: bool = True,
        include_user: bool = True
    ) -> List[Analysis]:
        """
        Get analyses with related entity information loaded.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            skip: Pagination offset
            limit: Maximum results to return
            include_model: Whether to load model relationship
            include_user: Whether to load user relationship

        Returns:
            List of analyses with relationships loaded
        """
        query = db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.is_deleted == False,
            )
        )

        # Add eager loading for relationships
        if include_model:
            query = query.options(joinedload(self.model.model))
        if include_user:
            query = query.options(joinedload(self.model.created_by_user))

        return (
            query
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_recent_analyses(
        self, 
        db: Session, 
        tenant_id: UUID, 
        days: int = 7, 
        limit: int = 100
    ) -> List[Analysis]:
        """
        Get recently created analyses within the specified number of days.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            days: Number of days back to search (default: 7)
            limit: Maximum results to return

        Returns:
            List of recent analyses ordered by creation date (newest first)
        """
        return self.get_recent(db=db, tenant_id=tenant_id, days=days, limit=limit)

    def count_analyses_by_model(
        self, 
        db: Session, 
        tenant_id: UUID, 
        model_id: UUID
    ) -> int:
        """
        Count analyses for a specific model.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            model_id: Model UUID

        Returns:
            Number of analyses for the model
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.model_id == model_id,
                    self.model.is_deleted == False,
                )
            )
            .count()
        )

    def count_analyses_by_user(
        self, 
        db: Session, 
        tenant_id: UUID, 
        user_id: UUID
    ) -> int:
        """
        Count analyses created by a specific user.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            user_id: User UUID

        Returns:
            Number of analyses created by the user
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

    def get_analysis_statistics(
        self, 
        db: Session, 
        tenant_id: UUID,
        model_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get statistical information about analyses.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            model_id: Optional model ID to filter statistics

        Returns:
            Dictionary with analysis statistics
        """
        base_query = db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.is_deleted == False,
            )
        )

        if model_id:
            base_query = base_query.filter(self.model.model_id == model_id)

        # Total counts
        total_analyses = base_query.count()

        # Time period distribution
        time_period_counts = {}
        for period in TimePeriod:
            count = base_query.filter(
                self.model.default_time_period == period.value
            ).count()
            time_period_counts[period.value] = count

        # Average default reps
        avg_reps_result = base_query.with_entities(
            func.avg(self.model.default_reps)
        ).scalar()
        avg_default_reps = float(avg_reps_result) if avg_reps_result else 0.0

        # Most common time period
        most_common_period = None
        if time_period_counts:
            most_common_period = max(time_period_counts, key=time_period_counts.get)

        # Analyses by model (if not filtered by model_id)
        analyses_by_model = []
        if not model_id:
            model_counts = (
                base_query
                .with_entities(
                    self.model.model_id,
                    func.count(self.model.id).label('count')
                )
                .group_by(self.model.model_id)
                .order_by(desc('count'))
                .limit(10)
                .all()
            )
            analyses_by_model = [
                {"model_id": str(model_id), "count": count}
                for model_id, count in model_counts
            ]

        return {
            "total_analyses": total_analyses,
            "analyses_by_time_period": time_period_counts,
            "analyses_by_model": analyses_by_model,
            "average_default_reps": avg_default_reps,
            "most_common_time_period": most_common_period,
        }

    def check_name_availability(
        self, 
        db: Session, 
        tenant_id: UUID, 
        model_id: UUID, 
        name: str, 
        exclude_analysis_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if an analysis name is available within a model.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            model_id: Model UUID
            name: Analysis name to check
            exclude_analysis_id: Analysis ID to exclude (for updates)

        Returns:
            True if name is available, False if taken
        """
        query = db.query(self.model.id).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.model_id == model_id,
                self.model.name == name,
                self.model.is_deleted == False,
            )
        )

        # Exclude current analysis when checking for updates
        if exclude_analysis_id:
            query = query.filter(self.model.id != exclude_analysis_id)

        return query.first() is None

    def get_analyses_created_between(
        self, 
        db: Session, 
        tenant_id: UUID, 
        start_date: datetime, 
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[Analysis]:
        """
        Get analyses created within a specific date range.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            skip: Pagination offset
            limit: Maximum results to return

        Returns:
            List of analyses created within the date range
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.created_at >= start_date,
                    self.model.created_at <= end_date,
                    self.model.is_deleted == False,
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_analyses_with_high_reps(
        self, 
        db: Session, 
        tenant_id: UUID, 
        min_reps: int = 100,
        skip: int = 0,
        limit: int = 100
    ) -> List[Analysis]:
        """
        Get analyses with default_reps above a threshold.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            min_reps: Minimum number of default reps
            skip: Pagination offset
            limit: Maximum results to return

        Returns:
            List of analyses with high replication counts
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.default_reps >= min_reps,
                    self.model.is_deleted == False,
                )
            )
            .order_by(desc(self.model.default_reps))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def bulk_update_time_period(
        self, 
        db: Session, 
        tenant_id: UUID, 
        analysis_ids: List[UUID], 
        new_time_period: TimePeriod
    ) -> int:
        """
        Update time period for multiple analyses in bulk.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            analysis_ids: List of analysis IDs to update
            new_time_period: New time period to set

        Returns:
            Number of analyses updated
        """
        if not analysis_ids:
            return 0

        updated_count = (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.id.in_(analysis_ids),
                    self.model.is_deleted == False,
                )
            )
            .update(
                {
                    "default_time_period": new_time_period.value,
                    "updated_at": datetime.utcnow()
                },
                synchronize_session=False
            )
        )

        db.flush()
        return updated_count

    def get_analyses_for_models(
        self, 
        db: Session, 
        tenant_id: UUID, 
        model_ids: List[UUID],
        skip: int = 0,
        limit: int = 100
    ) -> List[Analysis]:
        """
        Get analyses for multiple models.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            model_ids: List of model IDs to get analyses for
            skip: Pagination offset
            limit: Maximum results to return

        Returns:
            List of analyses for the specified models
        """
        if not model_ids:
            return []

        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.model_id.in_(model_ids),
                    self.model.is_deleted == False,
                )
            )
            .order_by(self.model.model_id, desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )