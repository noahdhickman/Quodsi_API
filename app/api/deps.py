# app/api/deps.py
from typing import Optional
from uuid import UUID
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.tenant import Tenant
from pydantic import BaseModel

class MockCurrentUser(BaseModel):
    """Mock user for development authentication"""
    user_id: UUID
    tenant_id: UUID
    email: str
    display_name: str

# Default test user for easy development
DEFAULT_TEST_USER = MockCurrentUser(
    user_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
    tenant_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
    email="test@example.com",
    display_name="Test User"
)

async def get_current_user_mock(
    x_mock_user_id: Optional[str] = Header(None, alias="X-Mock-User-Id"),
    x_mock_tenant_id: Optional[str] = Header(None, alias="X-Mock-Tenant-Id"),
    x_mock_email: Optional[str] = Header(None, alias="X-Mock-Email"),
    x_mock_display_name: Optional[str] = Header(None, alias="X-Mock-Display-Name")
) -> MockCurrentUser:
    """
    Mock authentication dependency for development.
    
    Uses headers to simulate authenticated user, falls back to default test user.
    """
    try:
        # Use provided headers or fall back to defaults
        user_id = UUID(x_mock_user_id) if x_mock_user_id else DEFAULT_TEST_USER.user_id
        tenant_id = UUID(x_mock_tenant_id) if x_mock_tenant_id else DEFAULT_TEST_USER.tenant_id
        email = x_mock_email or DEFAULT_TEST_USER.email
        display_name = x_mock_display_name or DEFAULT_TEST_USER.display_name
        
        return MockCurrentUser(
            user_id=user_id,
            tenant_id=tenant_id,
            email=email,
            display_name=display_name
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid UUID format in authentication headers: {str(e)}"
        )

async def get_current_user_from_db(
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current user from database using mock authentication.
    
    This validates that the mock user actually exists in the database.
    """
    user = db.query(User).filter(
        User.id == current_user.user_id,
        User.tenant_id == current_user.tenant_id,
        User.is_deleted == False
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User {current_user.user_id} not found in tenant {current_user.tenant_id}"
        )
    
    return user

async def get_current_tenant(
    current_user: MockCurrentUser = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
) -> Tenant:
    """
    Get the current tenant from database using mock authentication.
    """
    tenant = db.query(Tenant).filter(
        Tenant.id == current_user.tenant_id,
        Tenant.is_deleted == False
    ).first()
    
    if not tenant:
        raise HTTPException(
            status_code=404,
            detail=f"Tenant {current_user.tenant_id} not found"
        )
    
    return tenant