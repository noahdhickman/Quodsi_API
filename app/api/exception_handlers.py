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