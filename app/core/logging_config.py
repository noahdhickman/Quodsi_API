"""
Comprehensive logging configuration for Quodsi FastAPI application.
Provides structured JSON logging, request tracing, and exception handling.
"""

import logging
import json
import sys
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from uuid import uuid4
from typing import Optional

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record):
        json_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception information if present
        if record.exc_info:
            json_obj["exception"] = self.formatException(record.exc_info)

        # Add additional fields from extra parameters
        if hasattr(record, "extra_fields"):
            json_obj.update(record.extra_fields)

        return json.dumps(json_obj)


def setup_logging(
    app_name: str = "quodsi-api",
    log_level: str = "INFO",
    json_format: bool = True,
    log_to_file: bool = True,
    log_to_console: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """Configure logging for the FastAPI application"""
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove existing handlers to prevent duplicates
    logger.handlers = []

    # Create formatters
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler with rotation
    if log_to_file:
        log_file = LOGS_DIR / f"{app_name}.log"
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_file_size, backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Error file handler
        error_file = LOGS_DIR / f"{app_name}_error.log"
        error_handler = RotatingFileHandler(
            error_file, maxBytes=max_file_size, backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)


class LoggingMiddleware:
    """Middleware to log request and response information"""

    def __init__(self, app):
        self.app = app
        self.logger = get_logger("quodsi.request")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope, receive=receive)
        request_id = str(uuid4())

        # Store request ID in state for use in routes
        request.state.request_id = request_id

        # Log request
        start_time = time.time()
        self.logger.info(
            "Request received",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                }
            },
        )

        # Process the request
        response_status = None

        async def send_wrapper(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            response_status = 500
            self.logger.error(
                f"Unhandled exception in middleware: {str(e)}",
                exc_info=True,
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                    }
                },
            )
            raise
        finally:
            # Log response
            end_time = time.time()
            duration = end_time - start_time
            self.logger.info(
                "Request completed",
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response_status,
                        "duration_ms": round(duration * 1000, 2),
                    }
                },
            )


async def log_exceptions(request: Request, exc: Exception):
    """Global exception handler with logging"""
    logger = get_logger("quodsi.exceptions")
    request_id = getattr(request.state, "request_id", "unknown")

    if isinstance(exc, HTTPException):
        status_code = exc.status_code
        error_type = "HTTPException"
        detail = exc.detail
    elif isinstance(exc, RequestValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        error_type = "ValidationError"
        detail = exc.errors()
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_type = "InternalError"
        detail = str(exc)

    logger.error(
        f"{error_type}: {detail}",
        exc_info=exc,
        extra={
            "extra_fields": {
                "request_id": request_id,
                "error_type": error_type,
                "status_code": status_code,
                "path": request.url.path,
                "method": request.method,
                "detail": detail,
            }
        },
    )

    # Prepare consistent error response
    return {
        "error": {
            "code": status_code,
            "type": error_type,
            "message": detail,
            "request_id": request_id,
        }
    }
