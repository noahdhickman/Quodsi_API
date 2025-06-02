from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from typing import Optional

from app.db.models.base_entity import BaseEntity


class UserSession(BaseEntity):
    """
    Model for tracking individual user sessions.
    
    This table tracks when users log in/out, what devices they use,
    and session duration for analytics and security purposes.
    """
    __tablename__ = "user_sessions"

    # Foreign key to users table
    user_id = Column(
        UNIQUEIDENTIFIER, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Session end time (NULL while session is active)
    ended_at = Column(DateTime, nullable=True)
    
    # Duration of session in minutes (calculated when session ends)
    duration_minutes = Column(Integer, nullable=True)
    
    # Type of session (e.g., 'web', 'api', 'mobile')
    session_type = Column(String(50), nullable=False, default='web')
    
    # Client type (e.g., 'browser', 'mobile_app', 'api_client')
    client_type = Column(String(100), nullable=False)
    
    # Additional client information (browser version, device info, etc.)
    client_info = Column(Text, nullable=True)
    
    # IP address of the client
    ip_address = Column(String(45), nullable=True)  # 45 chars supports IPv6
    
    # Relationship back to User model
    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, session_type='{self.session_type}', active={self.ended_at is None})>"
    
    @property
    def is_active(self) -> bool:
        """Check if the session is currently active (not ended)."""
        return self.ended_at is None
    
    def calculate_duration_minutes(self) -> Optional[int]:
        """Calculate session duration in minutes from created_at to ended_at."""
        if self.ended_at is None:
            return None
        
        duration = self.ended_at - self.created_at
        return int(duration.total_seconds() / 60)