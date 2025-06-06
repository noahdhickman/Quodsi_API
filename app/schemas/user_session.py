# app/schemas/user_session.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class SessionCreateRequest(BaseModel):
    """Request schema for creating a new session"""

    client_type: Optional[str] = Field(
        default="web", description="Type of client (web, mobile, desktop)"
    )
    session_type: str = Field(
        default="web", description="Type of session (web, api, mobile)"
    )
    client_info: Optional[str] = Field(
        default=None, description="Additional client information"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "client_type": "web",
                "session_type": "web",
                "client_info": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            }
        }


class SessionEndRequest(BaseModel):
    """Request schema for ending a session"""

    reason: Optional[str] = Field(
        default="user_logout", description="Reason for ending session"
    )

    class Config:
        json_schema_extra = {"example": {"reason": "user_logout"}}


class SessionResponse(BaseModel):
    """Response schema for session data"""

    id: UUID
    user_id: UUID
    tenant_id: UUID
    client_type: str
    session_type: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    is_active: bool
    ip_address: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "456e7890-e89b-12d3-a456-426614174001",
                "tenant_id": "789e0123-e89b-12d3-a456-426614174002",
                "client_type": "web",
                "session_type": "web",
                "started_at": "2025-06-02T09:00:00Z",
                "ended_at": None,
                "last_activity_at": "2025-06-02T09:30:00Z",
                "duration_minutes": None,
                "is_active": True,
                "ip_address": "192.168.1.100",
            }
        }


class ActiveSessionsResponse(BaseModel):
    """Response schema for active sessions list"""

    user_id: UUID
    active_count: int
    sessions: List[SessionResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "456e7890-e89b-12d3-a456-426614174001",
                "active_count": 2,
                "sessions": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "user_id": "456e7890-e89b-12d3-a456-426614174001",
                        "tenant_id": "789e0123-e89b-12d3-a456-426614174002",
                        "client_type": "web",
                        "session_type": "web",
                        "started_at": "2025-06-02T09:00:00Z",
                        "is_active": True,
                    }
                ],
            }
        }


class SessionHistoryResponse(BaseModel):
    """Response schema for session history with pagination"""

    user_id: UUID
    total_count: int
    page_size: int
    page_offset: int
    sessions: List[SessionResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "456e7890-e89b-12d3-a456-426614174001",
                "total_count": 25,
                "page_size": 10,
                "page_offset": 0,
                "sessions": [],
            }
        }


class SessionStatistics(BaseModel):
    """Session statistics for analytics"""

    total_sessions: int
    active_sessions: int
    total_usage_minutes: int
    average_session_duration: float
    most_used_client_type: str
    last_session_date: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "total_sessions": 47,
                "active_sessions": 2,
                "total_usage_minutes": 1250,
                "average_session_duration": 26.6,
                "most_used_client_type": "web",
                "last_session_date": "2025-06-02T09:00:00Z",
            }
        }


class SessionActivityUpdate(BaseModel):
    """Request schema for updating session activity"""

    activity_data: Optional[dict] = Field(default={}, description="Activity metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "activity_data": {
                    "page_views": 15,
                    "actions_performed": 8,
                    "last_page": "/dashboard",
                }
            }
        }
