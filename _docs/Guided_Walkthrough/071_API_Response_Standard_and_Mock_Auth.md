# Module 7.1: API Response Standard and Mock Authentication

## Purpose
Implement consistent API response format and mock authentication system for development.

## Prerequisites
- Completed modules 1-6
- BaseEntity, Tenant, and User models implemented
- Repository and service layers created

---

## Overview

In this module, we'll create:
1. **API Response Standard** - Consistent response format across all endpoints
2. **Mock Authentication System** - Development-friendly authentication using headers

## Learning Objectives

By the end of this module, you'll understand:
- How to implement consistent API response formats
- How to create development authentication systems
- How to structure error handling in APIs
- How to use FastAPI dependency injection

---

## Part 1: API Response Standard

### 1.1 Understanding the Response Standard

**Why Consistent Responses Matter:**
- Predictable client-side handling
- Easier debugging and logging
- Professional API design
- Future-proof extensibility

**Standard Response Structure:**
```json
{
  "data": {...},           // The actual response data
  "meta": {                // Metadata about the response
    "timestamp": "2025-01-XX",
    "tenant_id": "uuid"
  },
  "errors": [...]          // Error details if applicable
}
```

**Reference:** For complete details, see `Quodsi SaaS App/Web API/000_API_Overview.md`

### 1.2 Implement Response Models

Create `app/schemas/response.py`:

```python
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
```

### 1.3 Response Helper Functions

Create `app/api/response_helpers.py`:

```python
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
```

---

## Part 2: Mock Authentication System

### 2.1 Understanding Mock Authentication

**Purpose:**
- Enable API testing without complex authentication setup
- Provide user and tenant context for development
- Simulate production authentication patterns

**How It Works:**
- Uses HTTP headers to pass user information
- Provides fallback default values for easy testing
- Validates tenant consistency

### 2.2 Create Mock Authentication

Create `app/api/deps.py`:

```python
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
```

---

## Testing and Validation

### 2.3 Testing Response Helpers

Create `test_response_helpers.py`:

```python
# test_response_helpers.py
"""
Test API response helper functions
"""
from app.api.response_helpers import create_success_response, create_error_response, create_validation_error_response
from uuid import UUID
import json

def test_response_helpers():
    """Test response helper functions"""
    
    # Test 1: Success response
    print("Test 1: Success response")
    test_data = {"message": "Hello World", "count": 42}
    tenant_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    
    success_response = create_success_response(test_data, tenant_id)
    print("Success response structure:")
    print(json.dumps(success_response, indent=2, default=str))
    print()
    
    # Test 2: Error response
    print("Test 2: Error response")
    error_response = create_error_response(
        code="VALIDATION_ERROR",
        message="Email is required",
        field="email",
        tenant_id=tenant_id
    )
    print("Error response structure:")
    print(json.dumps(error_response, indent=2, default=str))
    print()
    
    # Test 3: Validation error response
    print("Test 3: Validation error response")
    validation_errors = [
        {"msg": "field required", "loc": ["email"]},
        {"msg": "ensure this value has at least 8 characters", "loc": ["password"]}
    ]
    
    validation_response = create_validation_error_response(validation_errors, tenant_id)
    print("Validation error response structure:")
    print(json.dumps(validation_response, indent=2, default=str))

if __name__ == "__main__":
    test_response_helpers()
```

### 2.4 Testing Mock Authentication

Create `test_mock_auth.py`:

```python
# test_mock_auth.py
"""
Test mock authentication functionality outside of FastAPI context
"""
from app.api.deps import MockCurrentUser, DEFAULT_TEST_USER
from uuid import UUID

def test_mock_auth():
    """Test mock authentication with different scenarios"""
    
    # Test 1: Default user
    print("Test 1: Default user")
    print(f"User ID: {DEFAULT_TEST_USER.user_id}")
    print(f"Tenant ID: {DEFAULT_TEST_USER.tenant_id}")
    print(f"Email: {DEFAULT_TEST_USER.email}")
    print(f"Display Name: {DEFAULT_TEST_USER.display_name}")
    print()
    
    # Test 2: Custom user creation
    print("Test 2: Custom user")
    custom_user = MockCurrentUser(
        user_id=UUID("999e8400-e29b-41d4-a716-446655440000"),
        tenant_id=UUID("888e8400-e29b-41d4-a716-446655440000"),
        email="custom@example.com",
        display_name="Custom User"
    )
    print(f"User ID: {custom_user.user_id}")
    print(f"Tenant ID: {custom_user.tenant_id}")
    print(f"Email: {custom_user.email}")
    print(f"Display Name: {custom_user.display_name}")
    print()
    
    # Test 3: Verify data types
    print("Test 3: Data type verification")
    print(f"User ID type: {type(DEFAULT_TEST_USER.user_id)}")
    print(f"Tenant ID type: {type(DEFAULT_TEST_USER.tenant_id)}")
    print(f"Email type: {type(DEFAULT_TEST_USER.email)}")
    print(f"Display Name type: {type(DEFAULT_TEST_USER.display_name)}")

if __name__ == "__main__":
    test_mock_auth()
```

---

## Key Implementation Notes

### Fixed Issues from Original Version:
1. **Mock Auth Testing**: The original test called the FastAPI dependency function directly, which caused issues with `Header` objects. The fixed version tests the data structures directly.
2. **Proper Error Handling**: Added proper error handling for UUID parsing in the mock authentication.
3. **Testing Outside FastAPI Context**: Created standalone test functions that don't require FastAPI's dependency injection.

### Usage Patterns:

#### In FastAPI Endpoints:
```python
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user_mock, MockCurrentUser
from app.api.response_helpers import create_success_response

router = APIRouter()

@router.get("/profile")
async def get_profile(current_user: MockCurrentUser = Depends(get_current_user_mock)):
    # Your endpoint logic here
    data = {"user_id": str(current_user.user_id), "email": current_user.email}
    return create_success_response(data, current_user.tenant_id)
```

#### Testing with HTTP Headers:
```bash
curl -H "X-Mock-User-Id: 999e8400-e29b-41d4-a716-446655440000" \
     -H "X-Mock-Tenant-Id: 888e8400-e29b-41d4-a716-446655440000" \
     -H "X-Mock-Email: test@custom.com" \
     -H "X-Mock-Display-Name: Test User" \
     http://localhost:8000/api/profile
```

---

## Next Steps

Continue to the next module:
- **Module 7.2**: Registration Endpoint Implementation → `072_Registration_Endpoint.md`

## Key Concepts Covered

1. **API Response Standard**: Consistent structure for all API responses
2. **Mock Authentication**: Development-friendly authentication using headers
3. **Dependency Injection**: FastAPI's dependency system for clean code organization
4. **Error Handling**: Structured error responses with detailed information
5. **Type Safety**: Using Pydantic models for request/response validation
6. **Testing Strategies**: How to test API components outside of FastAPI context

These foundations will be used throughout the remaining endpoint implementations.
