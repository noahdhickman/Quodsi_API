# app/schemas/response.py
from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Generic, TypeVar
from datetime import datetime
from uuid import UUID

# Generic type for response data
T = TypeVar('T')

class ResponseMeta(BaseModel):
    """Standard metadata for all API responses"""
    timestamp: datetime
    tenant_id: Optional[UUID] = None
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class ErrorDetail(BaseModel):
    """Error detail structure"""
    code: str
    message: str
    field: Optional[str] = None  # For validation errors
    
class StandardResponse(BaseModel, Generic[T]):
    """Standard wrapper for all API responses"""
    data: Optional[T] = None
    meta: ResponseMeta
    errors: Optional[List[ErrorDetail]] = None
    
    @classmethod
    def success(cls, data: T, tenant_id: Optional[UUID] = None):
        """Create a successful response"""
        return cls(
            data=data,
            meta=ResponseMeta(
                timestamp=datetime.utcnow(),
                tenant_id=tenant_id
            )
        )
    
    @classmethod
    def error(cls, errors: List[ErrorDetail], tenant_id: Optional[UUID] = None):
        """Create an error response"""
        return cls(
            meta=ResponseMeta(
                timestamp=datetime.utcnow(),
                tenant_id=tenant_id
            ),
            errors=errors
        )

# Convenience response types
class UserResponse(StandardResponse[Dict[str, Any]]):
    pass

class TenantResponse(StandardResponse[Dict[str, Any]]):
    pass

class SuccessResponse(StandardResponse[Dict[str, str]]):
    pass