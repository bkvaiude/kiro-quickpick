from datetime import datetime
from typing import Dict, List, Optional
from app.models.user_consent import UserConsent, UserConsentCreate, UserConsentUpdate

# In-memory storage for user consent
# In a real application, this would be stored in a database
user_consents: Dict[str, UserConsent] = {}


class UserConsentService:
    """Service for managing user consent information."""
    
    @staticmethod
    def create_consent(user_id: str, consent_data: UserConsentCreate) -> UserConsent:
        """
        Create a new user consent record.
        
        Args:
            user_id: The ID of the user
            consent_data: The consent data to store
            
        Returns:
            The created user consent record
        """
        consent = UserConsent(
            user_id=user_id,
            terms_accepted=consent_data.terms_accepted,
            marketing_consent=consent_data.marketing_consent,
            timestamp=datetime.utcnow()
        )
        
        user_consents[user_id] = consent
        return consent
    
    @staticmethod
    def get_consent(user_id: str) -> Optional[UserConsent]:
        """
        Get a user's consent record.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            The user consent record, or None if not found
        """
        return user_consents.get(user_id)
    
    @staticmethod
    def update_consent(user_id: str, consent_data: UserConsentUpdate) -> Optional[UserConsent]:
        """
        Update a user's consent record.
        
        Args:
            user_id: The ID of the user
            consent_data: The consent data to update
            
        Returns:
            The updated user consent record, or None if not found
        """
        consent = user_consents.get(user_id)
        if not consent:
            return None
        
        if consent_data.marketing_consent is not None:
            consent.marketing_consent = consent_data.marketing_consent
            consent.timestamp = datetime.utcnow()
        
        user_consents[user_id] = consent
        return consent
    
    @staticmethod
    def list_consents() -> List[UserConsent]:
        """
        List all user consent records.
        
        Returns:
            A list of all user consent records
        """
        return list(user_consents.values())