from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.db.models.user_session import UserSession
from app.repositories.base import BaseRepository


class UserSessionRepository(BaseRepository[UserSession]):
    """Repository for managing user session data operations."""
    
    def __init__(self):
        super().__init__(UserSession)
    
    def start_session(
        self, 
        db: Session, 
        user_id: UUID, 
        tenant_id: UUID, 
        client_type: str,
        session_type: str = "web",
        client_info: Optional[str] = None, 
        ip_address: Optional[str] = None
    ) -> UserSession:
        """
        Create and save a new user session.
        
        Args:
            db: Database session
            user_id: ID of the user starting the session
            tenant_id: Tenant ID for isolation
            client_type: Type of client (browser, mobile_app, etc.)
            session_type: Type of session (web, api, mobile)
            client_info: Additional client information (browser version, etc.)
            ip_address: Client's IP address
            
        Returns:
            The created UserSession object
        """
        session_data = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "client_type": client_type,
            "session_type": session_type,
            "client_info": client_info,
            "ip_address": ip_address,
            # ended_at and duration_minutes remain NULL for active session
        }
        
        return self.create(db, **session_data)
    
    def end_session(
        self, 
        db: Session, 
        session_id: UUID, 
        tenant_id: UUID
    ) -> Optional[UserSession]:
        """
        End an active session by setting ended_at and calculating duration.
        
        Args:
            db: Database session
            session_id: ID of the session to end
            tenant_id: Tenant ID for isolation
            
        Returns:
            The updated UserSession object, or None if not found
        """
        # Find the active session for this tenant
        session = db.query(UserSession).filter(
            and_(
                UserSession.id == session_id,
                UserSession.tenant_id == tenant_id,
                UserSession.ended_at.is_(None)  # Only end active sessions
            )
        ).first()
        
        if not session:
            return None
        
        # Set end time and calculate duration
        now = datetime.utcnow()
        session.ended_at = now
        session.duration_minutes = session.calculate_duration_minutes()
        
        db.commit()
        db.refresh(session)
        
        return session
    
    def get_active_sessions_for_user(
        self, 
        db: Session, 
        user_id: UUID, 
        tenant_id: UUID
    ) -> List[UserSession]:
        """
        Get all active (non-ended) sessions for a specific user.
        
        Args:
            db: Database session
            user_id: ID of the user
            tenant_id: Tenant ID for isolation
            
        Returns:
            List of active UserSession objects
        """
        return db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.tenant_id == tenant_id,
                UserSession.ended_at.is_(None)  # Active sessions only
            )
        ).order_by(desc(UserSession.created_at)).all()
    
    def get_session_history_for_user(
        self, 
        db: Session, 
        user_id: UUID, 
        tenant_id: UUID, 
        skip: int = 0, 
        limit: int = 50
    ) -> List[UserSession]:
        """
        Get paginated session history for a user (both active and ended sessions).
        
        Args:
            db: Database session
            user_id: ID of the user
            tenant_id: Tenant ID for isolation
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of UserSession objects, ordered by most recent first
        """
        return db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.tenant_id == tenant_id
            )
        ).order_by(desc(UserSession.created_at)).offset(skip).limit(limit).all()
    
    def count_sessions_for_user(
        self, 
        db: Session, 
        user_id: UUID, 
        tenant_id: UUID
    ) -> int:
        """
        Count total number of sessions for a user.
        
        Args:
            db: Database session
            user_id: ID of the user
            tenant_id: Tenant ID for isolation
            
        Returns:
            Total count of sessions
        """
        return db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.tenant_id == tenant_id
            )
        ).count()
    
    def get_session_by_id(
        self, 
        db: Session, 
        session_id: UUID, 
        tenant_id: UUID
    ) -> Optional[UserSession]:
        """
        Get a specific session by ID with tenant isolation.
        
        Args:
            db: Database session
            session_id: ID of the session
            tenant_id: Tenant ID for isolation
            
        Returns:
            UserSession object or None if not found
        """
        return db.query(UserSession).filter(
            and_(
                UserSession.id == session_id,
                UserSession.tenant_id == tenant_id
            )
        ).first()
    
    def end_all_active_sessions_for_user(
        self, 
        db: Session, 
        user_id: UUID, 
        tenant_id: UUID
    ) -> List[UserSession]:
        """
        End all active sessions for a user (useful for logout from all devices).
        
        Args:
            db: Database session
            user_id: ID of the user
            tenant_id: Tenant ID for isolation
            
        Returns:
            List of ended UserSession objects
        """
        active_sessions = self.get_active_sessions_for_user(db, user_id, tenant_id)
        ended_sessions = []
        
        now = datetime.utcnow()
        for session in active_sessions:
            session.ended_at = now
            session.duration_minutes = session.calculate_duration_minutes()
            ended_sessions.append(session)
        
        if ended_sessions:
            db.commit()
            for session in ended_sessions:
                db.refresh(session)
        
        return ended_sessions