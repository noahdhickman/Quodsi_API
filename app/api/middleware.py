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