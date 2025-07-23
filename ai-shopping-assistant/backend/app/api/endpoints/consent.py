from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.models.user_consent import UserConsent, UserConsentCreate, UserConsentUpdate
from app.services.user_consent_service import UserConsentService
from app.middleware.auth import get_current_user_id

router = APIRouter()


@router.post("/", response_model=UserConsent)
async def create_consent(
    consent_data: UserConsentCreate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Create a new user consent record.
    
    Args:
        consent_data: The consent data to store
        user_id: The ID of the current user (from JWT token)
        
    Returns:
        The created user consent record
    """
    # Check if consent already exists
    existing_consent = UserConsentService.get_consent(user_id)
    if existing_consent:
        raise HTTPException(
            status_code=400,
            detail="Consent record already exists for this user"
        )
    
    # Ensure terms are accepted
    if not consent_data.terms_accepted:
        raise HTTPException(
            status_code=400,
            detail="Terms of Use and Privacy Policy must be accepted"
        )
    
    return UserConsentService.create_consent(user_id, consent_data)


@router.get("/me", response_model=UserConsent)
async def get_my_consent(user_id: str = Depends(get_current_user_id)):
    """
    Get the current user's consent record.
    
    Args:
        user_id: The ID of the current user (from JWT token)
        
    Returns:
        The user consent record
    """
    consent = UserConsentService.get_consent(user_id)
    if not consent:
        raise HTTPException(
            status_code=404,
            detail="Consent record not found"
        )
    
    return consent


@router.put("/me", response_model=UserConsent)
async def update_my_consent(
    consent_data: UserConsentUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Update the current user's consent record.
    
    Args:
        consent_data: The consent data to update
        user_id: The ID of the current user (from JWT token)
        
    Returns:
        The updated user consent record
    """
    updated_consent = UserConsentService.update_consent(user_id, consent_data)
    if not updated_consent:
        raise HTTPException(
            status_code=404,
            detail="Consent record not found"
        )
    
    return updated_consent


@router.get("/admin/all", response_model=List[UserConsent])
async def list_all_consents(user_id: str = Depends(get_current_user_id)):
    """
    List all user consent records (admin only).
    
    Args:
        user_id: The ID of the current user (from JWT token)
        
    Returns:
        A list of all user consent records
    """
    # In a real application, you would check if the user is an admin
    # For now, we'll just return all consents
    return UserConsentService.list_consents()