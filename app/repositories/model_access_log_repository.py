# app/repositories/model_access_log_repository.py
"""
Repository for managing model access logs with comprehensive audit and analytics capabilities.

This repository provides specialized methods for access logging, security monitoring,
and audit trail analysis for comprehensive compliance and security oversight.
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, text
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timezone, timedelta

from app.repositories.base import BaseRepository
from app.db.models.model_access_log import ModelAccessLog
from app.schemas.model_access_log import AccessType, AccessResult


class ModelAccessLogRepository(BaseRepository[ModelAccessLog]):
    """Repository for ModelAccessLog entities with audit and analytics operations"""
    
    def __init__(self):
        super().__init__(ModelAccessLog)
    
    def log_access(
        self,
        db: Session,
        *,
        tenant_id: UUID,
        model_id: UUID,
        user_id: UUID,
        access_type: AccessType,
        access_result: AccessResult,
        permission_source: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        endpoint: Optional[str] = None,
        request_method: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> ModelAccessLog:
        """
        Log a single access event with comprehensive context.
        
        This is the primary method for creating audit log entries.
        """
        log_data = {
            "model_id": model_id,
            "user_id": user_id,
            "access_type": access_type.value,
            "access_result": access_result.value,
            "permission_source": permission_source,
            "session_id": session_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "endpoint": endpoint,
            "request_method": request_method,
            "details": details
        }
        
        return self.create(db, obj_in=log_data, tenant_id=tenant_id)
    
    def get_logs_by_model(
        self,
        db: Session,
        tenant_id: UUID,
        model_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        access_type: Optional[AccessType] = None,
        access_result: Optional[AccessResult] = None,
        user_id: Optional[UUID] = None
    ) -> List[ModelAccessLog]:
        """Get access logs for a specific model with optional filters"""
        query = db.query(ModelAccessLog).filter(
            and_(
                ModelAccessLog.tenant_id == tenant_id,
                ModelAccessLog.model_id == model_id,
                ModelAccessLog.is_deleted == False
            )
        )
        
        # Apply optional filters
        if start_date:
            query = query.filter(ModelAccessLog.created_at >= start_date)
        if end_date:
            query = query.filter(ModelAccessLog.created_at <= end_date)
        if access_type:
            query = query.filter(ModelAccessLog.access_type == access_type.value)
        if access_result:
            query = query.filter(ModelAccessLog.access_result == access_result.value)
        if user_id:
            query = query.filter(ModelAccessLog.user_id == user_id)
        
        return query.options(
            joinedload(ModelAccessLog.model),
            joinedload(ModelAccessLog.user)
        ).order_by(
            ModelAccessLog.created_at.desc()
        ).offset(skip).limit(limit).all()
    
    def get_logs_by_user(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        model_id: Optional[UUID] = None
    ) -> List[ModelAccessLog]:
        """Get access logs for a specific user with optional filters"""
        query = db.query(ModelAccessLog).filter(
            and_(
                ModelAccessLog.tenant_id == tenant_id,
                ModelAccessLog.user_id == user_id,
                ModelAccessLog.is_deleted == False
            )
        )
        
        # Apply optional filters
        if start_date:
            query = query.filter(ModelAccessLog.created_at >= start_date)
        if end_date:
            query = query.filter(ModelAccessLog.created_at <= end_date)
        if model_id:
            query = query.filter(ModelAccessLog.model_id == model_id)
        
        return query.options(
            joinedload(ModelAccessLog.model)
        ).order_by(
            ModelAccessLog.created_at.desc()
        ).offset(skip).limit(limit).all()
    
    def get_security_events(
        self,
        db: Session,
        tenant_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        hours_back: int = 24,
        denied_only: bool = True
    ) -> List[ModelAccessLog]:
        """Get security-relevant events (denials, suspicious activity)"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        
        query = db.query(ModelAccessLog).filter(
            and_(
                ModelAccessLog.tenant_id == tenant_id,
                ModelAccessLog.created_at >= cutoff_time,
                ModelAccessLog.is_deleted == False
            )
        )
        
        if denied_only:
            query = query.filter(ModelAccessLog.access_result == AccessResult.DENIED.value)
        else:
            # Include denials, errors, and permission changes
            query = query.filter(
                or_(
                    ModelAccessLog.access_result == AccessResult.DENIED.value,
                    ModelAccessLog.access_result == AccessResult.ERROR.value,
                    ModelAccessLog.access_type == AccessType.PERMISSION_CHANGE.value
                )
            )
        
        return query.options(
            joinedload(ModelAccessLog.model),
            joinedload(ModelAccessLog.user)
        ).order_by(
            ModelAccessLog.created_at.desc()
        ).offset(skip).limit(limit).all()
    
    def get_access_analytics(
        self,
        db: Session,
        tenant_id: UUID,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        model_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get comprehensive access analytics for a time period"""
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        base_query = db.query(ModelAccessLog).filter(
            and_(
                ModelAccessLog.tenant_id == tenant_id,
                ModelAccessLog.created_at >= start_date,
                ModelAccessLog.created_at <= end_date,
                ModelAccessLog.is_deleted == False
            )
        )
        
        if model_id:
            base_query = base_query.filter(ModelAccessLog.model_id == model_id)
        
        # Overall statistics
        total_accesses = base_query.count()
        successful_accesses = base_query.filter(
            ModelAccessLog.access_result == AccessResult.SUCCESS.value
        ).count()
        denied_accesses = base_query.filter(
            ModelAccessLog.access_result == AccessResult.DENIED.value
        ).count()
        error_accesses = base_query.filter(
            ModelAccessLog.access_result == AccessResult.ERROR.value
        ).count()
        
        # Unique users and models
        unique_users = base_query.with_entities(
            func.count(func.distinct(ModelAccessLog.user_id))
        ).scalar() or 0
        
        unique_models = base_query.with_entities(
            func.count(func.distinct(ModelAccessLog.model_id))
        ).scalar() or 0
        
        # Most active users
        most_active_users = db.query(
            ModelAccessLog.user_id,
            func.count(ModelAccessLog.id).label('access_count')
        ).filter(
            and_(
                ModelAccessLog.tenant_id == tenant_id,
                ModelAccessLog.created_at >= start_date,
                ModelAccessLog.created_at <= end_date,
                ModelAccessLog.is_deleted == False
            )
        ).group_by(
            ModelAccessLog.user_id
        ).order_by(
            desc('access_count')
        ).limit(10).all()
        
        # Most accessed models
        most_accessed_models = db.query(
            ModelAccessLog.model_id,
            func.count(ModelAccessLog.id).label('access_count')
        ).filter(
            and_(
                ModelAccessLog.tenant_id == tenant_id,
                ModelAccessLog.created_at >= start_date,
                ModelAccessLog.created_at <= end_date,
                ModelAccessLog.is_deleted == False
            )
        ).group_by(
            ModelAccessLog.model_id
        ).order_by(
            desc('access_count')
        ).limit(10).all()
        
        # Access type distribution
        access_type_counts = {}
        for access_type in AccessType:
            count = base_query.filter(
                ModelAccessLog.access_type == access_type.value
            ).count()
            access_type_counts[access_type.value] = count
        
        # Unique IP addresses
        unique_ip_addresses = base_query.filter(
            ModelAccessLog.ip_address.isnot(None)
        ).with_entities(
            func.count(func.distinct(ModelAccessLog.ip_address))
        ).scalar() or 0
        
        return {
            "period_start": start_date,
            "period_end": end_date,
            "total_accesses": total_accesses,
            "successful_accesses": successful_accesses,
            "denied_accesses": denied_accesses,
            "error_accesses": error_accesses,
            "unique_users": unique_users,
            "unique_models": unique_models,
            "most_active_users": [
                {"user_id": str(user_id), "access_count": count} 
                for user_id, count in most_active_users
            ],
            "most_accessed_models": [
                {"model_id": str(model_id), "access_count": count} 
                for model_id, count in most_accessed_models
            ],
            "access_type_counts": access_type_counts,
            "failed_access_attempts": denied_accesses + error_accesses,
            "suspicious_activity_count": denied_accesses,  # Could be enhanced with more sophisticated detection
            "unique_ip_addresses": unique_ip_addresses
        }
    
    def get_user_access_summary(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID,
        model_id: UUID,
        *,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Get access summary for a specific user-model combination"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        base_query = db.query(ModelAccessLog).filter(
            and_(
                ModelAccessLog.tenant_id == tenant_id,
                ModelAccessLog.user_id == user_id,
                ModelAccessLog.model_id == model_id,
                ModelAccessLog.created_at >= cutoff_date,
                ModelAccessLog.is_deleted == False
            )
        )
        
        # Access counts
        total_accesses = base_query.count()
        successful_accesses = base_query.filter(
            ModelAccessLog.access_result == AccessResult.SUCCESS.value
        ).count()
        denied_accesses = base_query.filter(
            ModelAccessLog.access_result == AccessResult.DENIED.value
        ).count()
        
        # Access type breakdown
        read_accesses = base_query.filter(
            ModelAccessLog.access_type == AccessType.READ.value
        ).count()
        write_accesses = base_query.filter(
            ModelAccessLog.access_type == AccessType.WRITE.value
        ).count()
        execute_accesses = base_query.filter(
            ModelAccessLog.access_type == AccessType.EXECUTE.value
        ).count()
        other_accesses = total_accesses - (read_accesses + write_accesses + execute_accesses)
        
        # Timeline information
        first_access = base_query.order_by(ModelAccessLog.created_at.asc()).first()
        last_access = base_query.order_by(ModelAccessLog.created_at.desc()).first()
        last_successful_access = base_query.filter(
            ModelAccessLog.access_result == AccessResult.SUCCESS.value
        ).order_by(ModelAccessLog.created_at.desc()).first()
        
        return {
            "user_id": user_id,
            "model_id": model_id,
            "total_accesses": total_accesses,
            "successful_accesses": successful_accesses,
            "denied_accesses": denied_accesses,
            "read_accesses": read_accesses,
            "write_accesses": write_accesses,
            "execute_accesses": execute_accesses,
            "other_accesses": other_accesses,
            "first_access": first_access.created_at if first_access else None,
            "last_access": last_access.created_at if last_access else None,
            "last_successful_access": last_successful_access.created_at if last_successful_access else None
        }
    
    def get_model_access_summary(
        self,
        db: Session,
        tenant_id: UUID,
        model_id: UUID,
        *,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Get access summary for a specific model"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        base_query = db.query(ModelAccessLog).filter(
            and_(
                ModelAccessLog.tenant_id == tenant_id,
                ModelAccessLog.model_id == model_id,
                ModelAccessLog.created_at >= cutoff_date,
                ModelAccessLog.is_deleted == False
            )
        )
        
        # Basic statistics
        total_accesses = base_query.count()
        unique_users = base_query.with_entities(
            func.count(func.distinct(ModelAccessLog.user_id))
        ).scalar() or 0
        
        successful_accesses = base_query.filter(
            ModelAccessLog.access_result == AccessResult.SUCCESS.value
        ).count()
        denied_accesses = base_query.filter(
            ModelAccessLog.access_result == AccessResult.DENIED.value
        ).count()
        
        # Access type distribution
        access_type_distribution = {}
        most_common_access_type = None
        max_count = 0
        
        for access_type in AccessType:
            count = base_query.filter(
                ModelAccessLog.access_type == access_type.value
            ).count()
            access_type_distribution[access_type.value] = count
            if count > max_count:
                max_count = count
                most_common_access_type = access_type.value
        
        # Timeline
        first_access = base_query.order_by(ModelAccessLog.created_at.asc()).first()
        last_access = base_query.order_by(ModelAccessLog.created_at.desc()).first()
        
        # Top users by access count
        top_users = db.query(
            ModelAccessLog.user_id,
            func.count(ModelAccessLog.id).label('access_count')
        ).filter(
            and_(
                ModelAccessLog.tenant_id == tenant_id,
                ModelAccessLog.model_id == model_id,
                ModelAccessLog.created_at >= cutoff_date,
                ModelAccessLog.is_deleted == False
            )
        ).group_by(
            ModelAccessLog.user_id
        ).order_by(
            desc('access_count')
        ).limit(5).all()
        
        return {
            "model_id": model_id,
            "total_accesses": total_accesses,
            "unique_users": unique_users,
            "successful_accesses": successful_accesses,
            "denied_accesses": denied_accesses,
            "most_common_access_type": most_common_access_type,
            "access_type_distribution": access_type_distribution,
            "first_access": first_access.created_at if first_access else None,
            "last_access": last_access.created_at if last_access else None,
            "top_users": [
                {"user_id": str(user_id), "access_count": count} 
                for user_id, count in top_users
            ]
        }
    
    def detect_suspicious_activity(
        self,
        db: Session,
        tenant_id: UUID,
        *,
        hours_back: int = 24,
        max_failed_attempts: int = 5,
        max_different_ips: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Detect suspicious access patterns that might indicate security issues.
        
        Returns list of potential security alerts.
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        alerts = []
        
        # 1. Users with excessive failed access attempts
        failed_attempts_by_user = db.query(
            ModelAccessLog.user_id,
            func.count(ModelAccessLog.id).label('failed_count')
        ).filter(
            and_(
                ModelAccessLog.tenant_id == tenant_id,
                ModelAccessLog.created_at >= cutoff_time,
                ModelAccessLog.access_result == AccessResult.DENIED.value,
                ModelAccessLog.is_deleted == False
            )
        ).group_by(
            ModelAccessLog.user_id
        ).having(
            func.count(ModelAccessLog.id) > max_failed_attempts
        ).all()
        
        for user_id, failed_count in failed_attempts_by_user:
            alerts.append({
                "alert_type": "excessive_failed_attempts",
                "severity": "medium",
                "description": f"User has {failed_count} failed access attempts in last {hours_back} hours",
                "user_id": user_id,
                "event_count": failed_count
            })
        
        # 2. Users accessing from too many different IP addresses
        ip_variety_by_user = db.query(
            ModelAccessLog.user_id,
            func.count(func.distinct(ModelAccessLog.ip_address)).label('ip_count')
        ).filter(
            and_(
                ModelAccessLog.tenant_id == tenant_id,
                ModelAccessLog.created_at >= cutoff_time,
                ModelAccessLog.ip_address.isnot(None),
                ModelAccessLog.is_deleted == False
            )
        ).group_by(
            ModelAccessLog.user_id
        ).having(
            func.count(func.distinct(ModelAccessLog.ip_address)) > max_different_ips
        ).all()
        
        for user_id, ip_count in ip_variety_by_user:
            alerts.append({
                "alert_type": "multiple_ip_addresses",
                "severity": "high",
                "description": f"User accessed from {ip_count} different IP addresses in last {hours_back} hours",
                "user_id": user_id,
                "event_count": ip_count
            })
        
        # 3. High-value operations (DELETE, PERMISSION_CHANGE) with failures
        sensitive_failures = db.query(ModelAccessLog).filter(
            and_(
                ModelAccessLog.tenant_id == tenant_id,
                ModelAccessLog.created_at >= cutoff_time,
                ModelAccessLog.access_result.in_([AccessResult.DENIED.value, AccessResult.ERROR.value]),
                ModelAccessLog.access_type.in_([
                    AccessType.DELETE.value, 
                    AccessType.PERMISSION_CHANGE.value
                ]),
                ModelAccessLog.is_deleted == False
            )
        ).all()
        
        for log_entry in sensitive_failures:
            alerts.append({
                "alert_type": "sensitive_operation_failure",
                "severity": "high",
                "description": f"Failed {log_entry.access_type} operation on model",
                "user_id": log_entry.user_id,
                "model_id": log_entry.model_id,
                "access_type": log_entry.access_type,
                "access_result": log_entry.access_result,
                "event_count": 1
            })
        
        return alerts
    
    def bulk_log_access(
        self,
        db: Session,
        log_entries: List[Dict[str, Any]],
        tenant_id: UUID
    ) -> Tuple[List[UUID], List[Dict[str, Any]]]:
        """
        Create multiple access log entries in bulk.
        
        Returns:
            tuple: (successful_ids, failed_entries)
        """
        successful_ids = []
        failed_entries = []
        
        for entry_data in log_entries:
            try:
                # Ensure tenant_id is set
                entry_data["tenant_id"] = tenant_id
                
                # Validate required fields
                required_fields = ["model_id", "user_id", "access_type", "access_result"]
                for field in required_fields:
                    if field not in entry_data:
                        raise ValueError(f"Missing required field: {field}")
                
                # Create the log entry
                log_entry = self.create(db, obj_in=entry_data, tenant_id=tenant_id)
                successful_ids.append(log_entry.id)
                
            except Exception as e:
                failed_entries.append({
                    "data": entry_data,
                    "error": str(e)
                })
        
        return successful_ids, failed_entries
    
    def cleanup_old_logs(
        self,
        db: Session,
        tenant_id: UUID,
        *,
        days_to_keep: int = 90
    ) -> int:
        """
        Clean up access logs older than specified days.
        
        Returns:
            Number of logs deleted
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        
        old_logs = db.query(ModelAccessLog).filter(
            and_(
                ModelAccessLog.tenant_id == tenant_id,
                ModelAccessLog.created_at < cutoff_date,
                ModelAccessLog.is_deleted == False
            )
        ).all()
        
        count = 0
        for log_entry in old_logs:
            log_entry.is_deleted = True
            log_entry.updated_at = datetime.now(timezone.utc)
            db.add(log_entry)
            count += 1
        
        if count > 0:
            db.flush()
        
        return count