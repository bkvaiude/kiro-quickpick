from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_consent import UserConsent, UserConsentCreate, UserConsentUpdate
from app.services.user_consent_service import user_consent_service
from app.middleware.auth import get_current_user_id
from app.database.manager import get_db_session
from app.middleware.database_error_handlers import handle_database_errors

router = APIRouter()


@router.post("/", response_model=UserConsent)
@handle_database_errors
async def create_consent(
    consent_data: UserConsentCreate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Create a new user consent record.
    
    Args:
        consent_data: The consent data to store
        user_id: The ID of the current user (from JWT token)
        session: Database session
        
    Returns:
        The created user consent record
    """
    # Check if consent already exists
    existing_consent = await user_consent_service.get_consent(user_id, session)
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
    
    return await user_consent_service.create_consent(user_id, consent_data, session)


@router.get("/me", response_model=UserConsent)
@handle_database_errors
async def get_my_consent(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get the current user's consent record.
    
    Args:
        user_id: The ID of the current user (from JWT token)
        session: Database session
        
    Returns:
        The user consent record
    """
    consent = await user_consent_service.get_consent(user_id, session)
    if not consent:
        raise HTTPException(
            status_code=404,
            detail="Consent record not found"
        )
    
    return consent


@router.put("/me", response_model=UserConsent)
@handle_database_errors
async def update_my_consent(
    consent_data: UserConsentUpdate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Update the current user's consent record.
    
    Args:
        consent_data: The consent data to update
        user_id: The ID of the current user (from JWT token)
        session: Database session
        
    Returns:
        The updated user consent record
    """
    updated_consent = await user_consent_service.update_consent(user_id, consent_data, session)
    if not updated_consent:
        raise HTTPException(
            status_code=404,
            detail="Consent record not found"
        )
    
    return updated_consent


@router.get("/admin/all", response_model=List[UserConsent])
@handle_database_errors
async def list_all_consents(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session)
):
    """
    List all user consent records (admin only).
    
    Args:
        user_id: The ID of the current user (from JWT token)
        session: Database session
        
    Returns:
        A list of all user consent records
    """
    # In a real application, you would check if the user is an admin
    # For now, we'll just return all consents
    return await user_consent_service.list_consents(session)