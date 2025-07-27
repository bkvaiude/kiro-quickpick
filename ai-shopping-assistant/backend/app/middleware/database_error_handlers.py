"""Database error handlers for API endpoints."""

import logging
from typing import Dict, Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import (
    SQLAlchemyError, 
    IntegrityError, 
    OperationalError, 
    DisconnectionError,
    TimeoutError as SQLTimeoutError,
    StatementError,
    DataError,
    DatabaseError
)
from asyncpg.exceptions import (
    PostgresError,
    ConnectionDoesNotExistError,
    ConnectionFailureError,
    TooManyConnectionsError,
    CannotConnectNowError,
    UniqueViolationError,
    ForeignKeyViolationError,
    CheckViolationError,
    NotNullViolationError
)

from app.database.repositories.base import (
    RepositoryError, 
    RepositoryIntegrityError, 
    RepositoryOperationalError
)

logger = logging.getLogger(__name__)


class DatabaseErrorHandler:
    """Centralized database error handling for API endpoints."""
    
    @staticmethod
    def get_error_details(error: Exception) -> Dict[str, Any]:
        """
        Extract error details from database exceptions.
        
        Args:
            error: The database exception
            
        Returns:
            Dictionary with error details
        """
        error_details = {
            "error_type": "database_error",
            "error_description": "A database error occurred",
            "retry_after": None,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
        
        # Handle SQLAlchemy errors
        if isinstance(error, IntegrityError):
            error_details.update({
                "error_type": "integrity_error",
                "error_description": "Data integrity constraint violation",
                "status_code": status.HTTP_400_BAD_REQUEST
            })
            
            # Check for specific constraint violations
            error_str = str(error).lower()
            if "unique" in error_str or "duplicate" in error_str:
                error_details["error_description"] = "Duplicate data - record already exists"
            elif "foreign key" in error_str:
                error_details["error_description"] = "Invalid reference - related record not found"
            elif "not null" in error_str:
                error_details["error_description"] = "Required field is missing"
            elif "check" in error_str:
                error_details["error_description"] = "Data validation failed"
                
        elif isinstance(error, (OperationalError, DisconnectionError)):
            error_details.update({
                "error_type": "connection_error",
                "error_description": "Database connection issue - please try again",
                "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
                "retry_after": 30
            })
            
        elif isinstance(error, SQLTimeoutError):
            error_details.update({
                "error_type": "timeout_error",
                "error_description": "Database operation timed out - please try again",
                "status_code": status.HTTP_504_GATEWAY_TIMEOUT,
                "retry_after": 10
            })
            
        elif isinstance(error, (StatementError, DataError)):
            error_details.update({
                "error_type": "data_error",
                "error_description": "Invalid data format or query",
                "status_code": status.HTTP_400_BAD_REQUEST
            })
            
        elif isinstance(error, DatabaseError):
            error_details.update({
                "error_type": "database_error",
                "error_description": "Database system error",
                "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
                "retry_after": 60
            })
        
        # Handle asyncpg-specific errors
        elif isinstance(error, UniqueViolationError):
            error_details.update({
                "error_type": "duplicate_error",
                "error_description": "Record already exists",
                "status_code": status.HTTP_409_CONFLICT
            })
            
        elif isinstance(error, ForeignKeyViolationError):
            error_details.update({
                "error_type": "reference_error",
                "error_description": "Invalid reference - related record not found",
                "status_code": status.HTTP_400_BAD_REQUEST
            })
            
        elif isinstance(error, (CheckViolationError, NotNullViolationError)):
            error_details.update({
                "error_type": "validation_error",
                "error_description": "Data validation failed",
                "status_code": status.HTTP_400_BAD_REQUEST
            })
            
        elif isinstance(error, (ConnectionDoesNotExistError, ConnectionFailureError)):
            error_details.update({
                "error_type": "connection_error",
                "error_description": "Database connection lost - please try again",
                "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
                "retry_after": 30
            })
            
        elif isinstance(error, TooManyConnectionsError):
            error_details.update({
                "error_type": "capacity_error",
                "error_description": "Service temporarily overloaded - please try again",
                "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
                "retry_after": 60
            })
            
        elif isinstance(error, CannotConnectNowError):
            error_details.update({
                "error_type": "maintenance_error",
                "error_description": "Database maintenance in progress - please try again",
                "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
                "retry_after": 120
            })
        
        # Handle repository-specific errors
        elif isinstance(error, RepositoryIntegrityError):
            error_details.update({
                "error_type": "integrity_error",
                "error_description": "Data integrity constraint violation",
                "status_code": status.HTTP_400_BAD_REQUEST
            })
            
        elif isinstance(error, RepositoryOperationalError):
            error_details.update({
                "error_type": "operational_error",
                "error_description": "Database operational error - please try again",
                "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
                "retry_after": 30
            })
            
        elif isinstance(error, RepositoryError):
            error_details.update({
                "error_type": "repository_error",
                "error_description": "Data access error",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
            })
        
        return error_details
    
    @staticmethod
    def create_error_response(error: Exception, request_path: str = None) -> JSONResponse:
        """
        Create a standardized error response for database errors.
        
        Args:
            error: The database exception
            request_path: The request path for logging
            
        Returns:
            JSONResponse with standardized error format
        """
        error_details = DatabaseErrorHandler.get_error_details(error)
        
        # Log the error with appropriate level
        log_message = f"Database error on {request_path or 'unknown path'}: {str(error)}"
        
        if error_details["status_code"] >= 500:
            logger.error(log_message, exc_info=True)
        elif error_details["status_code"] >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # Build response content
        response_content = {
            "detail": error_details["error_description"],
            "error_type": error_details["error_type"]
        }
        
        # Add retry information if applicable
        if error_details["retry_after"]:
            response_content["retry_after"] = error_details["retry_after"]
        
        # Create response with appropriate headers
        headers = {}
        if error_details["retry_after"]:
            headers["Retry-After"] = str(error_details["retry_after"])
        
        return JSONResponse(
            status_code=error_details["status_code"],
            content=response_content,
            headers=headers
        )


# Exception handlers for FastAPI
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy errors."""
    return DatabaseErrorHandler.create_error_response(exc, request.url.path)


async def postgres_error_handler(request: Request, exc: PostgresError) -> JSONResponse:
    """Handle asyncpg PostgreSQL errors."""
    return DatabaseErrorHandler.create_error_response(exc, request.url.path)


async def repository_error_handler(request: Request, exc: RepositoryError) -> JSONResponse:
    """Handle repository layer errors."""
    return DatabaseErrorHandler.create_error_response(exc, request.url.path)


async def repository_integrity_error_handler(request: Request, exc: RepositoryIntegrityError) -> JSONResponse:
    """Handle repository integrity errors."""
    return DatabaseErrorHandler.create_error_response(exc, request.url.path)


async def repository_operational_error_handler(request: Request, exc: RepositoryOperationalError) -> JSONResponse:
    """Handle repository operational errors."""
    return DatabaseErrorHandler.create_error_response(exc, request.url.path)


# Utility function for wrapping database operations in endpoints
def handle_database_errors(func):
    """
    Decorator to handle database errors in API endpoints.
    
    Usage:
        @handle_database_errors
        async def my_endpoint():
            # Database operations here
            pass
    """
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except (SQLAlchemyError, PostgresError, RepositoryError) as e:
            # Let the registered exception handlers deal with these
            raise
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            raise
    
    return wrapper