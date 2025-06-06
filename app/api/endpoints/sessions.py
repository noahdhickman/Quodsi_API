# app/api/endpoints/sessions.py

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import logging

from app.db.database import get_db
from app.services.user_service import UserService, get_user_service
from app.schemas.user_session import (
    SessionCreateRequest,
    SessionResponse,
    SessionHistoryResponse,
    SessionEndRequest,
    ActiveSessionsResponse,
)
from app.core.dependencies import get_current_user
from app.db.models.user import User

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/sessions", tags=["Session Management"])
security = HTTPBearer()


# Helper function to extract client info from request
def get_client_info(request: Request) -> dict:
    """Extract client information from request headers"""
    return {
        "user_agent": request.headers.get("user-agent", ""),
        "ip_address": request.client.host if request.client else None,
        "client_type": request.headers.get("x-client-type", "web"),
    }


@router.post(
    "/start", response_model=SessionResponse, status_code=status.HTTP_201_CREATED
)
async def start_session(
    session_data: SessionCreateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Start a new user session.

    Creates a new session record and updates user's last activity.
    """
    try:
        # Extract client information from request
        client_info = get_client_info(request)

        # Start the session
        new_session = user_service.record_session_start(
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            client_type=session_data.client_type or client_info["client_type"],
            session_type=session_data.session_type,
            client_info=client_info["user_agent"],
            ip_address=client_info["ip_address"],
        )

        logger.info(f"Session started for user {current_user.id}: {new_session.id}")

        return SessionResponse(
            id=new_session.id,
            user_id=new_session.user_id,
            tenant_id=new_session.tenant_id,
            client_type=new_session.client_type,
            session_type=new_session.session_type,
            started_at=new_session.started_at,
            is_active=new_session.is_active,
            ip_address=new_session.ip_address,
        )

    except Exception as e:
        logger.error(f"Failed to start session for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start session: {str(e)}",
        )


@router.post("/end/{session_id}", response_model=SessionResponse)
async def end_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    End a specific session.

    Marks the session as ended and calculates duration.
    """
    try:
        ended_session = user_service.record_session_end(
            session_id=session_id,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
        )

        if not ended_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or already ended",
            )

        logger.info(f"Session ended for user {current_user.id}: {session_id}")

        return SessionResponse(
            id=ended_session.id,
            user_id=ended_session.user_id,
            tenant_id=ended_session.tenant_id,
            client_type=ended_session.client_type,
            session_type=ended_session.session_type,
            started_at=ended_session.started_at,
            ended_at=ended_session.ended_at,
            duration_minutes=ended_session.duration_minutes,
            is_active=ended_session.is_active,
            ip_address=ended_session.ip_address,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end session: {str(e)}",
        )


@router.get("/active", response_model=ActiveSessionsResponse)
async def get_active_sessions(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get all active sessions for the current user.
    """
    try:
        active_sessions = user_service.get_user_active_sessions(
            user_id=current_user.id, tenant_id=current_user.tenant_id
        )

        sessions_data = [
            SessionResponse(
                id=session.id,
                user_id=session.user_id,
                tenant_id=session.tenant_id,
                client_type=session.client_type,
                session_type=session.session_type,
                started_at=session.started_at,
                last_activity_at=session.last_activity_at,
                is_active=session.is_active,
                ip_address=session.ip_address,
            )
            for session in active_sessions
        ]

        return ActiveSessionsResponse(
            user_id=current_user.id,
            active_count=len(sessions_data),
            sessions=sessions_data,
        )

    except Exception as e:
        logger.error(
            f"Failed to get active sessions for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve active sessions: {str(e)}",
        )


@router.get("/history", response_model=SessionHistoryResponse)
async def get_session_history(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get paginated session history for the current user.
    """
    try:
        sessions, total_count = user_service.get_user_session_history(
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            skip=skip,
            limit=limit,
        )

        sessions_data = [
            SessionResponse(
                id=session.id,
                user_id=session.user_id,
                tenant_id=session.tenant_id,
                client_type=session.client_type,
                session_type=session.session_type,
                started_at=session.started_at,
                ended_at=session.ended_at,
                duration_minutes=session.duration_minutes,
                is_active=session.is_active,
                ip_address=session.ip_address,
            )
            for session in sessions
        ]

        return SessionHistoryResponse(
            user_id=current_user.id,
            total_count=total_count,
            page_size=limit,
            page_offset=skip,
            sessions=sessions_data,
        )

    except Exception as e:
        logger.error(
            f"Failed to get session history for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session history: {str(e)}",
        )


@router.post("/end-all", response_model=dict)
async def end_all_sessions(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    End all active sessions for the current user (logout from all devices).
    """
    try:
        ended_sessions = user_service.end_all_user_sessions(
            user_id=current_user.id, tenant_id=current_user.tenant_id
        )

        logger.info(
            f"All sessions ended for user {current_user.id}. Count: {len(ended_sessions)}"
        )

        return {
            "message": "All sessions ended successfully",
            "ended_sessions_count": len(ended_sessions),
            "user_id": str(current_user.id),
        }

    except Exception as e:
        logger.error(f"Failed to end all sessions for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end all sessions: {str(e)}",
        )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_details(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get details of a specific session.
    """
    try:
        session = user_service.get_session_by_id(
            session_id=session_id, tenant_id=current_user.tenant_id
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
            )

        # Verify the session belongs to the current user
        if session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session",
            )

        return SessionResponse(
            id=session.id,
            user_id=session.user_id,
            tenant_id=session.tenant_id,
            client_type=session.client_type,
            session_type=session.session_type,
            started_at=session.started_at,
            ended_at=session.ended_at,
            duration_minutes=session.duration_minutes,
            last_activity_at=session.last_activity_at,
            is_active=session.is_active,
            ip_address=session.ip_address,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session: {str(e)}",
        )


# Health check endpoint for session service
@router.get("/health", response_model=dict)
async def session_health_check():
    """
    Health check for session management endpoints.
    """
    return {
        "status": "healthy",
        "service": "session_management",
        "endpoints": [
            "POST /sessions/start",
            "POST /sessions/end/{session_id}",
            "GET /sessions/active",
            "GET /sessions/history",
            "POST /sessions/end-all",
            "GET /sessions/{session_id}",
        ],
    }
