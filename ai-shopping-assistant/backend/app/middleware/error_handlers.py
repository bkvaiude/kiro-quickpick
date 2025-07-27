from fastapi import Request, status
from fastapi.responses import JSONResponse
from jose import JWTError
from app.middleware.auth import JWTValidationError
from app.middleware.credit_middleware import CreditExhaustedException, credit_exhausted_handler
from app.config import logger

async def jwt_error_handler(request: Request, exc: JWTError) -> JSONResponse:
    """
    Handle JWT validation errors
    
    Args:
        request: The FastAPI request object
        exc: The JWT error exception
        
    Returns:
        JSONResponse: A standardized error response
    """
    logger.warning(f"JWT validation error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "detail": "Invalid authentication token",
            "error_type": "token_invalid",
            "error_description": str(exc)
        },
        headers={"WWW-Authenticate": "Bearer"}
    )

async def jwt_expired_handler(request: Request, exc: JWTValidationError) -> JSONResponse:
    """
    Handle JWT expiration errors
    
    Args:
        request: The FastAPI request object
        exc: The JWT validation error exception
        
    Returns:
        JSONResponse: A standardized error response
    """
    if "expired" in str(exc).lower():
        logger.info(f"JWT token expired: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "detail": "Authentication token has expired",
                "error_type": "token_expired",
                "error_description": "Your session has expired. Please log in again."
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
    return await jwt_error_handler(request, exc)

async def missing_token_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle missing authentication token errors
    
    Args:
        request: The FastAPI request object
        exc: The exception
        
    Returns:
        JSONResponse: A standardized error response
    """
    if "Missing authentication token" in str(exc):
        logger.info("Request missing authentication token")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "detail": "Authentication required",
                "error_type": "token_missing",
                "error_description": "This endpoint requires authentication. Please log in."
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)}
    )

async def guest_limit_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle guest credit limit errors
    
    Args:
        request: The FastAPI request object
        exc: The exception
        
    Returns:
        JSONResponse: A standardized error response
    """
    if "Guest credit limit reached" in str(exc):
        logger.info("Guest credit limit reached")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "detail": "Guest credit limit reached",
                "error_type": "guest_limit_reached",
                "error_description": "You have reached the limit for message credits. Please log in to continue."
            }
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)}
    )