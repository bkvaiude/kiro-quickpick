from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.credit_service import credit_service
from app.middleware.auth import get_optional_user
from app.database.manager import get_db_session
from app.config import logger
import uuid


class CreditExhaustedException(Exception):
    """Custom exception for credit exhaustion"""
    def __init__(self, detail: str, available_credits: int = 0, max_credits: int = 0, is_guest: bool = True):
        self.detail = detail
        self.available_credits = available_credits
        self.max_credits = max_credits
        self.is_guest = is_guest
        super().__init__(detail)


class CreditMiddleware:
    """
    Middleware for validating and managing message credits
    """
    
    def __init__(self):
        self.credit_service = credit_service
    
    def get_user_identifier(self, request: Request, user: Optional[Dict[str, Any]]) -> tuple[str, bool]:
        """
        Get user identifier and determine if user is guest
        
        Args:
            request: The FastAPI request object
            user: The authenticated user information (None for guests)
            
        Returns:
            tuple: (user_id, is_guest)
        """
        if user and user.get("sub"):
            # Authenticated user
            return user["sub"], False
        else:
            # Guest user - use session ID or create one
            session_id = request.headers.get("x-session-id")
            if not session_id:
                raise HTTPException(
                    status_code=503,
                    detail="Invalid x-session-id or guest id"
                )
            return session_id, True
    
    async def validate_credits(self, request: Request, user: Optional[Dict[str, Any]] = Depends(get_optional_user), session: AsyncSession = Depends(get_db_session)) -> Dict[str, Any]:
        """
        Validates that the user has sufficient credits for the request
        
        Args:
            request: The FastAPI request object
            user: The authenticated user information (None for guests)
            session: Database session for credit operations
            
        Returns:
            dict: Credit information for the user
            
        Raises:
            CreditExhaustedException: If the user has insufficient credits
        """
        user_id, is_guest = self.get_user_identifier(request, user)
        
        try:
            # Check available credits
            available_credits = await self.credit_service.check_credits(user_id, is_guest, session)
            
            if available_credits <= 0:
                # Get full credit status for error response
                credit_status = await self.credit_service.get_credit_status(user_id, is_guest, session)
                
                logger.warning(f"Credit exhausted for {'guest' if is_guest else 'registered'} user {user_id}")
                
                raise CreditExhaustedException(
                    detail="Insufficient credits to process request",
                    available_credits=credit_status.available_credits,
                    max_credits=credit_status.max_credits,
                    is_guest=is_guest
                )
            
            # Return credit information for use in the endpoint
            return {
                "user_id": user_id,
                "is_guest": is_guest,
                "available_credits": available_credits
            }
        except CreditExhaustedException:
            # Re-raise credit exhaustion exceptions
            raise
        except Exception as e:
            logger.error(f"Database error during credit validation for user {user_id}: {e}")
            # In case of database connectivity issues, we could implement fallback logic here
            # For now, we'll raise an HTTP exception
            raise HTTPException(
                status_code=503,
                detail="Service temporarily, unavailable. Please try again later."
            )
    
    async def deduct_credit(self, request: Request, user: Optional[Dict[str, Any]] = Depends(get_optional_user), amount: int = 1, session: AsyncSession = Depends(get_db_session)) -> bool:
        """
        Deducts credits from the user's balance
        
        Args:
            request: The FastAPI request object
            user: The authenticated user information (None for guests)
            amount: Number of credits to deduct
            session: Database session for credit operations
            
        Returns:
            bool: True if successful
            
        Raises:
            CreditExhaustedException: If the user has insufficient credits
        """
        user_id, is_guest = self.get_user_identifier(request, user)
        
        try:
            # Attempt to deduct credits
            success = await self.credit_service.deduct_credit(user_id, is_guest, amount, session)
            
            if not success:
                # Get credit status for error response
                credit_status = await self.credit_service.get_credit_status(user_id, is_guest, session)
                
                logger.warning(f"Failed to deduct {amount} credit(s) for {'guest' if is_guest else 'registered'} user {user_id}")
                
                raise CreditExhaustedException(
                    detail=f"Insufficient credits to deduct {amount} credit(s)",
                    available_credits=credit_status.available_credits,
                    max_credits=credit_status.max_credits,
                    is_guest=is_guest
                )
            
            logger.debug(f"Successfully deducted {amount} credit(s) from {'guest' if is_guest else 'registered'} user {user_id}")
            return True
        except CreditExhaustedException:
            # Re-raise credit exhaustion exceptions
            raise
        except Exception as e:
            logger.error(f"Database error during credit deduction for user {user_id}: {e}")
            # In case of database connectivity issues, we could implement fallback logic here
            # For now, we'll raise an HTTP exception
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable.. Please try again later."
            )
    
    async def get_credit_status(self, request: Request, user: Optional[Dict[str, Any]] = Depends(get_optional_user), session: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """
        Gets comprehensive credit status for the user
        
        Args:
            request: The FastAPI request object
            user: The authenticated user information (None for guests)
            session: Database session for credit operations
            
        Returns:
            dict: Credit status information
        """
        user_id, is_guest = self.get_user_identifier(request, user)
        
        try:
            credit_status = await self.credit_service.get_credit_status(user_id, is_guest, session)
            
            return {
                "user_id": user_id,
                "available_credits": credit_status.available_credits,
                "max_credits": credit_status.max_credits,
                "is_guest": credit_status.is_guest,
                "can_reset": credit_status.can_reset,
                "next_reset_time": credit_status.next_reset_time.isoformat() if credit_status.next_reset_time else None
            }
        except Exception as e:
            logger.error(f"Database error during credit status retrieval for user {user_id}: {e}")
            # In case of database connectivity issues, we could implement fallback logic here
            # For now, we'll raise an HTTP exception
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable... Please try again later."
            )


# Create a singleton instance
credit_middleware = CreditMiddleware()

# Dependency functions for use in FastAPI endpoints
async def validate_credits(request: Request, user: Optional[Dict[str, Any]] = Depends(get_optional_user), session: AsyncSession = Depends(get_db_session)) -> Dict[str, Any]:
    """Dependency for validating credits before processing requests"""
    return await credit_middleware.validate_credits(request, user, session)

async def deduct_credit(request: Request, user: Optional[Dict[str, Any]] = Depends(get_optional_user), session: AsyncSession = Depends(get_db_session)) -> bool:
    """Dependency for deducting a single credit"""
    return await credit_middleware.deduct_credit(request, user, amount=1, session=session)

async def get_credit_status(request: Request, user: Optional[Dict[str, Any]] = Depends(get_optional_user), session: AsyncSession = Depends(get_db_session)) -> Dict[str, Any]:
    """Dependency for getting credit status"""
    return await credit_middleware.get_credit_status(request, user, session)


# Error handler for credit exhaustion
async def credit_exhausted_handler(request: Request, exc: CreditExhaustedException) -> JSONResponse:
    """
    Handle credit exhaustion errors
    
    Args:
        request: The FastAPI request object
        exc: The credit exhaustion exception
        
    Returns:
        JSONResponse: A standardized error response
    """
    logger.info(f"Credit exhausted: {exc.detail}")
    
    error_response = {
        "detail": exc.detail,
        "error_type": "credits_exhausted",
        "available_credits": exc.available_credits,
        "max_credits": exc.max_credits,
        "is_guest": exc.is_guest
    }
    
    if exc.is_guest:
        error_response["error_description"] = (
            "You have reached the limit for message credits. "
            "Please log in to get more credits and continue using the service."
        )
    else:
        error_response["error_description"] = (
            "You have used all your daily credits. "
            "Your credits will be reset in 24 hours, or you can upgrade your plan for more credits."
        )
    
    return JSONResponse(
        status_code=429,  # Too Many Requests
        content=error_response
    )