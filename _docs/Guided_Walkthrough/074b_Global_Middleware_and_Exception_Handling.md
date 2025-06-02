# Module 7.4b: Global Middleware and Exception Handling

## Purpose
Implement comprehensive global middleware and exception handling for consistent error responses and request logging across the entire API.

## Prerequisites
- Completed Module 7.4a (Centralized API Router Structure)
- All service layers implemented

---

## Part 2: Global Middleware and Exception Handling

### 2.1 Enhanced Exception Handlers

Update `app/api/exception_handlers.py`:

```python
# app/api/exception_handlers.py
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from datetime import datetime

from app.api.response_helpers import (
    create_error_response, 
    create_validation_error_response
)

# Configure logging
logger = logging.getLogger(__name__)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.warning(f"Validation error on {request.url}: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_validation_error_response(exc.errors())
    )

async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """Handle direct Pydantic validation errors"""
    logger.warning(f"Pydantic validation error on {request.url}: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_validation_error_response(exc.errors())
    )

async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors"""
    logger.error(f"Database integrity error on {request.url}: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=create_error_response(
            code="INTEGRITY_ERROR",
            message="Data integrity constraint violation"
        )
    )

async def operational_error_handler(request: Request, exc: OperationalError):
    """Handle database operational errors"""
    logger.error(f"Database operational error on {request.url}: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=create_error_response(
            code="DATABASE_ERROR",
            message="Database service temporarily unavailable"
        )
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with standard format"""
    logger.warning(f"HTTP exception on {request.url}: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            code="HTTP_ERROR",
            message=exc.detail
        )
    )

async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle Starlette HTTP exceptions"""
    logger.warning(f"Starlette HTTP exception on {request.url}: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            code="HTTP_ERROR",
            message=exc.detail
        )
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.error(f"Unhandled exception on {request.url}: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            code="INTERNAL_ERROR",
            message="An internal server error occurred"
        )
    )
```

### 2.2 Request Logging Middleware

Create `app/api/middleware.py`:

```python
# app/api/middleware.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
import uuid
from typing import Callable

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all incoming requests and responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # Log request start
        start_time = time.time()
        logger.info(
            f"Request {request_id} started: {request.method} {request.url} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log successful response
            logger.info(
                f"Request {request_id} completed: "
                f"{response.status_code} in {process_time:.3f}s"
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate processing time for failed requests
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request {request_id} failed: "
                f"{str(e)} in {process_time:.3f}s",
                exc_info=True
            )
            
            # Re-raise to let exception handlers deal with it
            raise

class TenantContextMiddleware(BaseHTTPMiddleware):
    """Middleware to add tenant context to requests"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract tenant ID from mock auth headers
        tenant_id = request.headers.get("X-Mock-Tenant-Id")
        
        if tenant_id:
            request.state.tenant_id = tenant_id
            logger.debug(f"Request tenant context: {tenant_id}")
        
        response = await call_next(request)
        return response
```

---

## Summary

This module implements comprehensive middleware and exception handling:

### ✅ **Implemented Components:**

1. **Enhanced Exception Handlers**: Proper handling for all types of exceptions
2. **Request Logging Middleware**: Detailed logging with request IDs and timing
3. **Tenant Context Middleware**: Automatic tenant context extraction from headers
4. **Structured Error Responses**: Consistent error format across all endpoints

### 🧪 **Testing:**

The middleware and exception handlers will be automatically applied to all requests. Test by making various API calls and checking the logs and error responses.

### 📚 **Next Steps:**

Continue to Module 7.4c: Complete Main Application Setup to integrate these components into the main application.
