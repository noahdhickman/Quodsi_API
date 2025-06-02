# Part 3: API Endpoint Logging

**Duration:** 15-20 minutes  
**Objective:** Learn how to add comprehensive logging to your existing API endpoints, completing the request-to-database logging flow.

**Prerequisites:** Parts 1 & 2 completed - Infrastructure and services have logging

---

## Overview

This guide teaches you how to add logging to your **existing** API endpoints without rewriting them. You'll learn patterns for endpoint logging that create complete request traceability from API call to database and back.

---

## Step 1: API Endpoint Logging Patterns

### 1.1 Basic Endpoint Setup Pattern
**For every endpoint file, add these imports:**

```python
from app.core.logging_config import get_logger

logger = get_logger(__name__)
```

### 1.2 The Three Phases of Endpoint Logging

| Phase | When | What to Log |
|-------|------|-------------|
| **Entry** | Request received | Endpoint name, input data, request ID |
| **Success** | Operation completed | Results, generated IDs, status |
| **Error** | Exception caught | Error type, context, request ID |

---

## Step 2: Request Entry Logging Pattern

### 2.1 Basic Request Logging
**Pattern:** Log when a request is received with key context

```python
@router.post("/registration/tenant")
async def register_tenant(
    request: Request,
    registration_data: TenantRegistrationRequest,
    db: Session = Depends(get_db)
):
    # Get request ID from middleware
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Log request entry with context
    logger.info(
        "Tenant registration request received",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "email": registration_data.admin_email,
                "company_name": registration_data.name,
                "endpoint": "/registration/tenant",
                "method": "POST"
            }
        }
    )
    
    # ... your existing business logic ...
```

**Apply this pattern to:** Every endpoint method in your routers.

### 2.2 Request Context Fields
**Always include these fields in endpoint entry logs:**

```python
"extra_fields": {
    "request_id": request_id,           # For request correlation
    "endpoint": "/path/to/endpoint",    # Which endpoint was called
    "method": "POST|GET|PUT|DELETE",    # HTTP method
    "user_id": str(user.id),           # If authenticated
    "tenant_id": str(tenant.id),       # If tenant context
    # Key input fields (email, name, IDs, etc.)
}
```

---

## Step 3: Success Response Logging Pattern

### 3.1 Successful Operation Logging
**Pattern:** Log successful completion with results

```python
@router.post("/registration/tenant")
async def register_tenant(...):
    logger.info("Tenant registration request received", extra={...})
    
    try:
        # Your existing business logic
        result = await user_service.register_user_and_tenant(
            db=db,
            reg_in=registration_data,
            request_id=request_id  # Pass request_id to service
        )
        
        # Log successful completion
        logger.info(
            "Tenant registration completed successfully",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "user_id": str(result["admin_user_id"]),
                    "tenant_id": str(result["tenant_id"]),
                    "email": result["admin_email"],
                    "tenant_name": result["tenant_name"],
                    "endpoint": "/registration/tenant",
                    "status": "success"
                }
            }
        )
        
        return create_success_response(result)
        
    except Exception as e:
        # Error handling (covered in next section)
        pass
```

**Apply this pattern to:** Any endpoint that creates, updates, or processes data.

---

## Step 4: Error Handling Logging Pattern

### 4.1 Comprehensive Error Logging
**Pattern:** Different log levels for different error types

```python
@router.post("/registration/tenant")
async def register_tenant(...):
    logger.info("Tenant registration request received", extra={...})
    
    try:
        # Your existing business logic
        result = await user_service.register_user_and_tenant(...)
        logger.info("Registration completed successfully", extra={...})
        return create_success_response(result)
        
    except ValueError as e:
        # Business logic errors (validation, duplicates, etc.)
        logger.warning(
            f"Registration failed - validation error: {str(e)}",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "email": registration_data.admin_email,
                    "company_name": registration_data.name,
                    "error_type": "validation_error",
                    "endpoint": "/registration/tenant"
                }
            }
        )
        return create_error_response(
            code="VALIDATION_ERROR",
            message=str(e),
            request_id=request_id
        )
    
    except Exception as e:
        # Unexpected system errors
        logger.error(
            f"Registration failed - unexpected error: {str(e)}",
            exc_info=True,  # Include stack trace
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "email": registration_data.admin_email,
                    "error_type": "internal_error",
                    "endpoint": "/registration/tenant"
                }
            }
        )
        return create_error_response(
            code="INTERNAL_ERROR",
            message="Internal server error during registration",
            request_id=request_id
        )
```

**Error Logging Guidelines:**
- **WARNING:** Business rule violations, validation errors, expected failures
- **ERROR:** System errors, database failures, unexpected exceptions
- **Always include:** `exc_info=True` for ERROR logs to capture stack traces
- **Always include:** Request ID in error responses for correlation

---

## Step 5: Authentication Endpoint Logging

### 5.1 Mock Authentication Logging
**Enhance your existing `app/api/deps.py` authentication:**

```python
async def get_current_mock_user(request: Request) -> Optional[User]:
    """Your existing mock authentication with added logging"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Get mock headers
    mock_user_id = request.headers.get("X-Mock-User-Id")
    mock_tenant_id = request.headers.get("X-Mock-Tenant-Id")
    
    logger.debug(
        "Authentication attempt",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "has_user_id": bool(mock_user_id),
                "has_tenant_id": bool(mock_tenant_id),
                "path": str(request.url.path)
            }
        }
    )
    
    if not mock_user_id or not mock_tenant_id:
        logger.warning(
            "Authentication failed - missing headers",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "path": str(request.url.path),
                    "missing_headers": [
                        h for h in ["X-Mock-User-Id", "X-Mock-Tenant-Id"] 
                        if not request.headers.get(h)
                    ]
                }
            }
        )
        # Your existing HTTPException handling
        
    # Your existing mock user creation logic
    
    logger.debug(
        "Authentication successful",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "user_id": mock_user_id,
                "tenant_id": mock_tenant_id,
                "path": str(request.url.path)
            }
        }
    )
    
    return mock_user
```

---

## Step 6: Practical Implementation Guide

### 6.1 Update Your Registration Endpoints
**In your existing registration router (e.g., `app/api/routers/registration.py`):**

1. **Add logging imports** at the top
2. **Add request entry logging** to each endpoint method
3. **Add success logging** before returning responses
4. **Add error logging** in exception handlers
5. **Pass request_id** to service method calls

### 6.2 Update Your User Profile Endpoints
**In your existing user profile router (e.g., `app/api/routers/user_profile.py`):**

1. **Add logging to GET endpoints:**
```python
@router.get("/me")
async def get_current_user_profile(
    request: Request,
    current_user: User = Depends(get_current_mock_user)
):
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.info(
        "User profile request",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "user_id": str(current_user.id),
                "endpoint": "/users/me"
            }
        }
    )
    
    # Your existing logic
```

2. **Add logging to PUT endpoints:**
```python
@router.put("/me")
async def update_user_profile(
    request: Request,
    profile_update: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_mock_user),
    db: Session = Depends(get_db)
):
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.info(
        "User profile update request",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "user_id": str(current_user.id),
                "fields_to_update": list(profile_update.dict(exclude_unset=True).keys()),
                "endpoint": "/users/me"
            }
        }
    )
    
    # Your existing logic with success/error logging
```

### 6.3 Service Integration
**Update your service calls to pass request_id:**

```python
# In your endpoints, pass request_id to services
result = await user_service.register_user_and_tenant(
    db=db,
    reg_in=registration_data,
    request_id=request_id  # Add this parameter
)

# In your services, accept and use request_id
def register_user_and_tenant(self, db: Session, *, reg_in: UserRegistrationRequest, request_id: str = "unknown"):
    logger.info("Starting registration", extra={"extra_fields": {"request_id": request_id, ...}})
```

---

## Step 7: Testing Your API Logging

### 7.1 Test Complete Request Flow
```bash
# Test your existing registration endpoint
curl -X POST http://localhost:8000/api/v1/auth/registration/tenant \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Company",
    "domain": "testco",
    "admin_email": "admin@testco.com",
    "admin_password": "password123",
    "admin_display_name": "Test Admin"
  }'
```

**Expected Log Flow:**
1. **Middleware:** "Request received"
2. **Endpoint:** "Tenant registration request received"
3. **Service:** "Starting user and tenant registration"
4. **Repository:** "Creating new tenant"
5. **Repository:** "Tenant created successfully"
6. **Repository:** "Creating user for tenant"
7. **Repository:** "User created successfully"
8. **Service:** "User registration completed successfully"
9. **Endpoint:** "Tenant registration completed successfully"
10. **Middleware:** "Request completed"

### 7.2 Test Authenticated Endpoints
```bash
# Test your existing user profile endpoint
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "X-Mock-User-Id: 12345" \
  -H "X-Mock-Tenant-Id: 67890"
```

### 7.3 Test Error Scenarios
```bash
# Test missing authentication
curl -X GET http://localhost:8000/api/v1/users/me

# Test duplicate registration
# (run the same registration request twice)
```

---

## Step 8: Log Analysis

### 8.1 Successful Request Pattern
Look for this pattern in your logs:
```
[INFO] Request received (middleware)
[INFO] [Endpoint] request received (endpoint entry)
[INFO] Starting [operation] (service entry)
[DEBUG] Creating [entity] (repository)
[INFO] [Entity] created successfully (repository)
[INFO] [Operation] completed successfully (service)
[INFO] [Endpoint] completed successfully (endpoint)
[INFO] Request completed (middleware)
```

### 8.2 Error Request Pattern
Look for this pattern for errors:
```
[INFO] Request received (middleware)
[INFO] [Endpoint] request received (endpoint entry)
[INFO] Starting [operation] (service entry)
[WARNING] Business rule violation (repository)
[ERROR] [Operation] failed (service)
[WARNING] [Endpoint] failed - validation error (endpoint)
[INFO] Request completed with error (middleware)
```

---

## Verification Checklist

- [ ] ✅ Added logging imports to existing endpoint files
- [ ] ✅ Applied request entry logging to all endpoints
- [ ] ✅ Applied success logging to all endpoints
- [ ] ✅ Applied error logging with appropriate levels
- [ ] ✅ Enhanced authentication dependency with logging
- [ ] ✅ Request IDs flow through all layers (middleware → endpoint → service → repository)
- [ ] ✅ All logs include relevant context in `extra_fields`
- [ ] ✅ Error responses include request_id for correlation
- [ ] ✅ Can trace complete request flow through logs
- [ ] ✅ Both success and error scenarios are properly logged

---

## Key Principles

### 1. Request Correlation
Every log entry for a single request should have the same `request_id` for easy tracing.

### 2. Layered Logging
- **Middleware:** Request/response timing and basic info
- **Endpoint:** Business operation start/end and error handling
- **Service:** Business logic flow and decisions
- **Repository:** Data access operations and constraints

### 3. Contextual Information
Always include enough context to understand what happened without looking at other systems.

### 4. Error Response Correlation
Include `request_id` in error responses so users can reference it when reporting issues.

---

## What's Next

You now have complete request-to-database logging integrated with your existing API! The next step is to learn testing strategies and performance best practices.

**Next:** [Part 4: Testing and Best Practices](./080_Logging_Integration_Part4_Testing.md)
