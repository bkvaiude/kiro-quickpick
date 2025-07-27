from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from app.middleware.auth import get_current_user, get_optional_user
from app.middleware.credit_middleware import get_credit_status
from app.services.credit_service import credit_service
from app.database.manager import get_db_session
from app.middleware.database_error_handlers import handle_database_errors

router = APIRouter()

@router.get("/me")
@handle_database_errors
async def get_user_profile(
    request: Request, 
    user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get the current user's profile information including credit status
    
    This endpoint requires authentication and returns the user's profile information
    from the JWT token along with their current credit status.
    """
    # Get user's credit status using the middleware function
    credit_info = await get_credit_status(request, user, session)
    
    return {
        "user_id": user.get("sub"),
        "email": user.get("email"),
        "name": user.get("name"),
        "picture": user.get("picture"),
        "credits": {
            "available_credits": credit_info["available_credits"],
            "max_credits": credit_info["max_credits"],
            "is_guest": credit_info["is_guest"],
            "can_reset": credit_info["can_reset"],
            "next_reset_time": credit_info["next_reset_time"]
        }
    }

@router.get("/credits")
@handle_database_errors
async def get_user_credits(
    request: Request, 
    user: Dict[str, Any] = Depends(get_optional_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get credit balance for the current user (authenticated or guest)
    
    This endpoint returns detailed credit information for both authenticated and guest users.
    For authenticated users, it returns their daily credit allocation and reset information.
    For guest users, it returns their remaining one-time credits.
    """
    return await get_credit_status(request, user, session)

@router.get("/credits/status")
@handle_database_errors
async def get_credit_status_endpoint(
    request: Request, 
    user: Dict[str, Any] = Depends(get_optional_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get credit status for the current user (authenticated or guest)
    
    This endpoint returns credit information for both authenticated and guest users.
    For authenticated users, it returns their daily credit allocation.
    For guest users, it returns their remaining one-time credits.
    
    Note: This is an alias for /user/credits for backward compatibility.
    """
    return await get_credit_status(request, user, session)