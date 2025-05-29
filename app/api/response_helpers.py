# app/api/response_helpers.py
from typing import Any, Dict, List, Optional
from uuid import UUID
from app.schemas.response import StandardResponse, ErrorDetail

def create_success_response(
    data: Any, 
    tenant_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """Create a standardized success response"""
    response = StandardResponse.success(data=data, tenant_id=tenant_id)
    return response.dict(exclude_none=True)

def create_error_response(
    code: str,
    message: str,
    field: Optional[str] = None,
    tenant_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """Create a standardized error response"""
    error = ErrorDetail(code=code, message=message, field=field)
    response = StandardResponse.error(errors=[error], tenant_id=tenant_id)
    return response.dict(exclude_none=True)

def create_validation_error_response(
    validation_errors: List[Dict[str, Any]],
    tenant_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """Create a response for validation errors"""
    errors = [
        ErrorDetail(
            code="VALIDATION_ERROR",
            message=str(error.get("msg", "Validation failed")),
            field=".".join(str(loc) for loc in error.get("loc", []))
        )
        for error in validation_errors
    ]
    response = StandardResponse.error(errors=errors, tenant_id=tenant_id)
    return response.dict(exclude_none=True)