# app/services/analysis_service.py
"""
Service layer for Analysis business operations.

Handles analysis management, validation, authorization, and business logic
while maintaining proper separation from data access and API concerns.

Key Responsibilities:
- Analysis CRUD operations with business validation
- Authorization and permission checking
- Business rule enforcement (name uniqueness, tenant consistency)
- Default value management and configuration
- Bulk operations and advanced queries
"""
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timezone

from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.model_repository import ModelRepository
from app.repositories.user_repository import UserRepository
from app.schemas.analysis import (
    AnalysisCreate, AnalysisUpdate, AnalysisRead, AnalysisSummary,
    AnalysisQuery, AnalysisStatistics, AnalysisCopyRequest,
    BulkAnalysisCreate, BulkAnalysisResponse, AnalysisValidationResponse,
    TimePeriod
)
from app.db.models.analysis import Analysis
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class AnalysisService:
    """Service for managing analysis business operations"""
    
    def __init__(self):
        self.analysis_repo = AnalysisRepository()
        self.model_repo = ModelRepository()
        self.user_repo = UserRepository()
    
    def create_analysis(
        self,
        db: Session,
        tenant_id: UUID,
        analysis_create: AnalysisCreate,
        current_user_id: UUID
    ) -> AnalysisRead:
        """
        Create a new analysis with business validation.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            analysis_create: Analysis creation data
            current_user_id: ID of user creating the analysis
            
        Returns:
            Created analysis
            
        Raises:
            ValueError: If validation fails
            PermissionError: If user lacks permission
        """
        try:
            # Validate the parent model exists and belongs to tenant
            model = self.model_repo.get_by_id(db, tenant_id, analysis_create.model_id)
            if not model:
                raise ValueError(f"Model {analysis_create.model_id} not found in tenant {tenant_id}")
            
            # Validate user exists and belongs to tenant
            user = self.user_repo.get_by_id(db, tenant_id, current_user_id)
            if not user:
                raise ValueError(f"User {current_user_id} not found in tenant {tenant_id}")
            
            # Check name uniqueness within model
            existing_analysis = self.analysis_repo.find_by_name_and_model_id(
                db, tenant_id, analysis_create.model_id, analysis_create.name
            )
            if existing_analysis:
                raise ValueError(f"Analysis with name '{analysis_create.name}' already exists for this model")
            
            # TODO: Add permission checking here when permission system is integrated
            # For now, assume user can create analyses for any model in their tenant
            
            # Prepare analysis data
            analysis_data = analysis_create.model_dump()
            analysis_data["created_by_user_id"] = current_user_id
            
            # Create the analysis
            analysis = self.analysis_repo.create(
                db=db,
                obj_in=analysis_data,
                tenant_id=tenant_id
            )
            
            logger.info(f"Created analysis: {analysis.name} (ID: {analysis.id}) by user {current_user_id}")
            
            return AnalysisRead.model_validate(analysis)
            
        except Exception as e:
            logger.error(f"Error creating analysis: {e}")
            raise
    
    def get_analysis_by_id(
        self,
        db: Session,
        tenant_id: UUID,
        analysis_id: UUID,
        current_user_id: Optional[UUID] = None
    ) -> Optional[AnalysisRead]:
        """
        Get analysis by ID with optional permission checking.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            analysis_id: Analysis ID to retrieve
            current_user_id: Optional user ID for permission checking
            
        Returns:
            Analysis if found and accessible, None otherwise
        """
        analysis = self.analysis_repo.get_by_id(db, tenant_id, analysis_id)
        if not analysis:
            return None
        
        # TODO: Add permission checking here when permission system is integrated
        # For now, return analysis if it exists in the tenant
        
        return AnalysisRead.model_validate(analysis)
    
    def update_analysis(
        self,
        db: Session,
        tenant_id: UUID,
        analysis_id: UUID,
        analysis_update: AnalysisUpdate,
        current_user_id: UUID
    ) -> Optional[AnalysisRead]:
        """
        Update an analysis with authorization and validation.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            analysis_id: Analysis ID to update
            analysis_update: Update data
            current_user_id: User performing the update
            
        Returns:
            Updated analysis if successful, None if not found
            
        Raises:
            PermissionError: If user lacks permission to update
            ValueError: If validation fails
        """
        try:
            # Get the existing analysis
            analysis = self.analysis_repo.get_by_id(db, tenant_id, analysis_id)
            if not analysis:
                return None
            
            # Check if user has permission to update (creator or admin)
            if not analysis.is_editable_by_user(current_user_id):
                raise PermissionError("User does not have permission to update this analysis")
            
            # Validate name uniqueness if name is being updated
            if analysis_update.name and analysis_update.name != analysis.name:
                existing_analysis = self.analysis_repo.find_by_name_and_model_id(
                    db, tenant_id, analysis.model_id, analysis_update.name
                )
                if existing_analysis and existing_analysis.id != analysis_id:
                    raise ValueError(f"Analysis with name '{analysis_update.name}' already exists for this model")
            
            # Prepare update data (only include provided fields)
            update_data = analysis_update.model_dump(exclude_unset=True)
            
            # Update the analysis
            updated_analysis = self.analysis_repo.update(
                db=db,
                db_obj=analysis,
                obj_in=update_data
            )
            
            logger.info(f"Updated analysis: {updated_analysis.name} (ID: {analysis_id}) by user {current_user_id}")
            
            return AnalysisRead.model_validate(updated_analysis)
            
        except Exception as e:
            logger.error(f"Error updating analysis {analysis_id}: {e}")
            raise
    
    def delete_analysis(
        self,
        db: Session,
        tenant_id: UUID,
        analysis_id: UUID,
        current_user_id: UUID
    ) -> bool:
        """
        Soft delete an analysis with authorization checking.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            analysis_id: Analysis ID to delete
            current_user_id: User performing the deletion
            
        Returns:
            True if deleted successfully, False if not found
            
        Raises:
            PermissionError: If user lacks permission to delete
        """
        try:
            # Get the existing analysis
            analysis = self.analysis_repo.get_by_id(db, tenant_id, analysis_id)
            if not analysis:
                return False
            
            # Check if user has permission to delete (creator or admin)
            if not analysis.is_editable_by_user(current_user_id):
                raise PermissionError("User does not have permission to delete this analysis")
            
            # Soft delete the analysis
            deleted = self.analysis_repo.soft_delete(db, tenant_id, analysis_id)
            
            if deleted:
                logger.info(f"Deleted analysis: {analysis.name} (ID: {analysis_id}) by user {current_user_id}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting analysis {analysis_id}: {e}")
            raise
    
    def list_analyses_for_model(
        self,
        db: Session,
        tenant_id: UUID,
        model_id: UUID,
        skip: int = 0,
        limit: int = 100,
        current_user_id: Optional[UUID] = None
    ) -> List[AnalysisSummary]:
        """
        List all analyses for a specific model.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            model_id: Model ID to get analyses for
            skip: Pagination offset
            limit: Maximum results
            current_user_id: Optional user ID for permission filtering
            
        Returns:
            List of analysis summaries
        """
        try:
            # Validate model exists
            model = self.model_repo.get_by_id(db, tenant_id, model_id)
            if not model:
                raise ValueError(f"Model {model_id} not found in tenant {tenant_id}")
            
            # Get analyses for the model
            analyses = self.analysis_repo.get_analyses_by_model_id(
                db, tenant_id, model_id, skip=skip, limit=limit
            )
            
            # TODO: Filter by permissions when permission system is integrated
            # For now, return all analyses in the tenant
            
            return [AnalysisSummary.model_validate(analysis) for analysis in analyses]
            
        except Exception as e:
            logger.error(f"Error listing analyses for model {model_id}: {e}")
            raise
    
    def list_analyses_by_user(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[AnalysisSummary]:
        """
        List analyses created by a specific user.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            user_id: User ID to get analyses for
            skip: Pagination offset
            limit: Maximum results
            
        Returns:
            List of analysis summaries
        """
        try:
            analyses = self.analysis_repo.get_analyses_by_user_id(
                db, tenant_id, user_id, skip=skip, limit=limit
            )
            
            return [AnalysisSummary.model_validate(analysis) for analysis in analyses]
            
        except Exception as e:
            logger.error(f"Error listing analyses for user {user_id}: {e}")
            raise
    
    def search_analyses(
        self,
        db: Session,
        tenant_id: UUID,
        query: AnalysisQuery,
        current_user_id: Optional[UUID] = None
    ) -> List[AnalysisSummary]:
        """
        Search analyses with advanced filtering.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            query: Search query parameters
            current_user_id: Optional user ID for permission filtering
            
        Returns:
            List of matching analysis summaries
        """
        try:
            analyses = []
            
            # Apply different search strategies based on query parameters
            if query.name_contains:
                # Text search
                analyses = self.analysis_repo.search_analyses_by_name(
                    db, tenant_id, query.name_contains, skip=query.skip, limit=query.limit
                )
            elif query.model_id:
                # Model-specific search
                analyses = self.analysis_repo.get_analyses_by_model_id(
                    db, tenant_id, query.model_id, skip=query.skip, limit=query.limit
                )
            elif query.created_by_user_id:
                # User-specific search
                analyses = self.analysis_repo.get_analyses_by_user_id(
                    db, tenant_id, query.created_by_user_id, skip=query.skip, limit=query.limit
                )
            elif query.time_period:
                # Time period search
                analyses = self.analysis_repo.get_analyses_by_time_period(
                    db, tenant_id, query.time_period, skip=query.skip, limit=query.limit
                )
            elif query.created_after or query.created_before:
                # Date range search
                start_date = query.created_after or datetime.min.replace(tzinfo=timezone.utc)
                end_date = query.created_before or datetime.now(timezone.utc)
                analyses = self.analysis_repo.get_analyses_created_between(
                    db, tenant_id, start_date, end_date, skip=query.skip, limit=query.limit
                )
            else:
                # General listing
                analyses = self.analysis_repo.get_all(
                    db, tenant_id, skip=query.skip, limit=query.limit
                )
            
            # TODO: Apply permission filtering when permission system is integrated
            
            return [AnalysisSummary.model_validate(analysis) for analysis in analyses]
            
        except Exception as e:
            logger.error(f"Error searching analyses: {e}")
            raise
    
    def copy_analysis(
        self,
        db: Session,
        tenant_id: UUID,
        copy_request: AnalysisCopyRequest,
        current_user_id: UUID
    ) -> AnalysisRead:
        """
        Copy an existing analysis with a new name.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            copy_request: Copy request parameters
            current_user_id: User performing the copy
            
        Returns:
            Newly created analysis copy
            
        Raises:
            ValueError: If source analysis not found or validation fails
            PermissionError: If user lacks permission
        """
        try:
            # Get the source analysis
            source_analysis = self.analysis_repo.get_by_id(db, tenant_id, copy_request.source_analysis_id)
            if not source_analysis:
                raise ValueError(f"Source analysis {copy_request.source_analysis_id} not found")
            
            # TODO: Check if user has permission to read source analysis
            
            # Determine target model
            target_model_id = copy_request.target_model_id or source_analysis.model_id
            
            # Validate target model exists
            target_model = self.model_repo.get_by_id(db, tenant_id, target_model_id)
            if not target_model:
                raise ValueError(f"Target model {target_model_id} not found")
            
            # Create the copy
            analysis_create = AnalysisCreate(
                name=copy_request.new_name,
                description=copy_request.new_description or source_analysis.description,
                model_id=target_model_id,
                default_reps=source_analysis.default_reps,
                default_time_period=TimePeriod(source_analysis.default_time_period)
            )
            
            copied_analysis = self.create_analysis(
                db, tenant_id, analysis_create, current_user_id
            )
            
            logger.info(f"Copied analysis: {source_analysis.name} -> {copied_analysis.name} by user {current_user_id}")
            
            return copied_analysis
            
        except Exception as e:
            logger.error(f"Error copying analysis {copy_request.source_analysis_id}: {e}")
            raise
    
    def get_analysis_statistics(
        self,
        db: Session,
        tenant_id: UUID,
        model_id: Optional[UUID] = None
    ) -> AnalysisStatistics:
        """
        Get statistical information about analyses.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            model_id: Optional model ID to filter statistics
            
        Returns:
            Analysis statistics
        """
        try:
            stats_data = self.analysis_repo.get_analysis_statistics(db, tenant_id, model_id)
            
            # Get recent analyses
            recent_analyses = self.analysis_repo.get_recent_analyses(db, tenant_id, days=7, limit=5)
            recent_summaries = [AnalysisSummary.model_validate(analysis) for analysis in recent_analyses]
            
            return AnalysisStatistics(
                total_analyses=stats_data["total_analyses"],
                analyses_by_time_period=stats_data["analyses_by_time_period"],
                analyses_by_model=stats_data["analyses_by_model"],
                recent_analyses=recent_summaries,
                average_default_reps=stats_data["average_default_reps"],
                most_common_time_period=stats_data["most_common_time_period"],
                period_start=datetime.now(timezone.utc).replace(day=1),  # Start of current month
                period_end=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Error getting analysis statistics: {e}")
            raise
    
    def validate_analysis_creation(
        self,
        db: Session,
        tenant_id: UUID,
        analysis_create: AnalysisCreate,
        current_user_id: UUID
    ) -> AnalysisValidationResponse:
        """
        Validate analysis creation without actually creating it.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            analysis_create: Analysis creation data to validate
            current_user_id: User who would create the analysis
            
        Returns:
            Validation response with errors and warnings
        """
        validation_errors = []
        warnings = []
        
        # Check model exists
        model_exists = self.model_repo.exists(db, tenant_id, analysis_create.model_id)
        if not model_exists:
            validation_errors.append(f"Model {analysis_create.model_id} not found")
        
        # Check user exists
        user_exists = self.user_repo.exists(db, tenant_id, current_user_id)
        if not user_exists:
            validation_errors.append(f"User {current_user_id} not found")
        
        # Check name availability
        name_available = True
        if model_exists:  # Only check if model exists
            name_available = self.analysis_repo.check_name_availability(
                db, tenant_id, analysis_create.model_id, analysis_create.name
            )
            if not name_available:
                validation_errors.append(f"Analysis name '{analysis_create.name}' already exists for this model")
        
        # Add warnings for high replication counts
        if analysis_create.default_reps > 1000:
            warnings.append(f"High replication count ({analysis_create.default_reps}) may impact performance")
        
        return AnalysisValidationResponse(
            is_valid=len(validation_errors) == 0,
            validation_errors=validation_errors,
            warnings=warnings,
            name_available=name_available,
            model_exists=model_exists,
            user_has_permission=user_exists,  # Simplified for now
            tenant_consistent=True  # Always true with our tenant isolation
        )
    
    def bulk_create_analyses(
        self,
        db: Session,
        tenant_id: UUID,
        bulk_request: BulkAnalysisCreate,
        current_user_id: UUID
    ) -> BulkAnalysisResponse:
        """
        Create multiple analyses in bulk.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            bulk_request: Bulk creation request
            current_user_id: User creating the analyses
            
        Returns:
            Bulk operation response with success/failure details
        """
        successful_analyses = []
        failed_analyses = []
        
        for analysis_create in bulk_request.analyses:
            try:
                created_analysis = self.create_analysis(
                    db, tenant_id, analysis_create, current_user_id
                )
                successful_analyses.append(created_analysis.id)
            except Exception as e:
                failed_analyses.append({
                    "name": analysis_create.name,
                    "error": str(e)
                })
        
        return BulkAnalysisResponse(
            successful_analyses=successful_analyses,
            failed_analyses=failed_analyses,
            total_requested=len(bulk_request.analyses),
            total_successful=len(successful_analyses),
            total_failed=len(failed_analyses)
        )


# Dependency injection function
def get_analysis_service() -> AnalysisService:
    """Get AnalysisService instance for dependency injection."""
    return AnalysisService()