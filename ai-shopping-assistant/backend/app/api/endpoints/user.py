from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.middleware.auth import get_current_user

router = APIRouter()

@router.get("/me")
async def get_user_profile(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get the current user's profile information
    
    This endpoint requires authentication and returns the user's profile information
    from the JWT token.
    """
    return {
        "user_id": user.get("sub"),
        "email": user.get("email"),
        "name": user.get("name"),
        "picture": user.get("picture")
    }

@router.get("/remaining-actions")
async def get_remaining_actions():
    """
    This endpoint is always accessible and returns information about remaining actions
    for both authenticated and guest users.
    
    For authenticated users, it returns "unlimited".
    For guest users, it returns the number of remaining actions.
    """
    # This endpoint doesn't use the JWT validation middleware directly
    # It's handled by the frontend based on the authentication state
    return {
        "message": "This endpoint would return remaining actions information"
    }