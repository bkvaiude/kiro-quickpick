from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import logger
from app.models.user_consent import UserConsent, UserConsentCreate, UserConsentUpdate
from app.database.repositories.consent_repository import ConsentRepository
from app.database.models import UserConsentDB
from app.database.manager import get_db_session


class UserConsentService:
    """Service for managing user consent information."""
    
    async def create_consent(self, user_id: str, consent_data: UserConsentCreate, session: Optional[AsyncSession] = None) -> UserConsent:
        """
        Create a new user consent record.
        
        Args:
            user_id: The ID of the user
            consent_data: The consent data to store
            session: Optional database session (will create one if not provided)
            
        Returns:
            The created user consent record
        """
        # Create database model
        consent_db = UserConsentDB(
            user_id=user_id,
            terms_accepted=consent_data.terms_accepted,
            marketing_consent=consent_data.marketing_consent,
            timestamp=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to database
        if session:
            repo = ConsentRepository(session)
            created_consent_db = await repo.create_consent(consent_db)
        else:
            async for db_session in get_db_session():
                repo = ConsentRepository(db_session)
                created_consent_db = await repo.create_consent(consent_db)
                break
        
        logger.info(f"Created consent record for user {user_id}: terms={consent_data.terms_accepted}, marketing={consent_data.marketing_consent}")
        
        # Convert database model to Pydantic model
        return UserConsent(
            user_id=created_consent_db.user_id,
            terms_accepted=created_consent_db.terms_accepted,
            marketing_consent=created_consent_db.marketing_consent,
            timestamp=created_consent_db.timestamp
        )
    
    async def get_consent(self, user_id: str, session: Optional[AsyncSession] = None) -> Optional[UserConsent]:
        """
        Get a user's consent record.
        
        Args:
            user_id: The ID of the user
            session: Optional database session (will create one if not provided)
            
        Returns:
            The user consent record, or None if not found
        """
        # Get from database
        if session:
            repo = ConsentRepository(session)
            consent_db = await repo.get_consent(user_id)
        else:
            async for db_session in get_db_session():
                repo = ConsentRepository(db_session)
                consent_db = await repo.get_consent(user_id)
                break
        
        if consent_db is None:
            return None
        
        # Convert database model to Pydantic model
        return UserConsent(
            user_id=consent_db.user_id,
            terms_accepted=consent_db.terms_accepted,
            marketing_consent=consent_db.marketing_consent,
            timestamp=consent_db.timestamp
        )
    
    async def update_consent(self, user_id: str, consent_data: UserConsentUpdate, session: Optional[AsyncSession] = None) -> Optional[UserConsent]:
        """
        Update a user's consent record.
        
        Args:
            user_id: The ID of the user
            consent_data: The consent data to update
            session: Optional database session (will create one if not provided)
            
        Returns:
            The updated user consent record, or None if not found
        """
        # Prepare update data
        updates = {}
        if consent_data.marketing_consent is not None:
            updates['marketing_consent'] = consent_data.marketing_consent
        
        if not updates:
            # No updates to make, just return current consent
            return await self.get_consent(user_id, session)
        
        # Update in database
        if session:
            repo = ConsentRepository(session)
            updated_consent_db = await repo.update_consent(user_id, **updates)
        else:
            async for db_session in get_db_session():
                repo = ConsentRepository(db_session)
                updated_consent_db = await repo.update_consent(user_id, **updates)
                break
        
        if updated_consent_db is None:
            logger.warning(f"Attempted to update consent for non-existent user {user_id}")
            return None
        
        logger.debug(f"Updated consent for user {user_id}: {updates}")
        
        # Convert database model to Pydantic model
        return UserConsent(
            user_id=updated_consent_db.user_id,
            terms_accepted=updated_consent_db.terms_accepted,
            marketing_consent=updated_consent_db.marketing_consent,
            timestamp=updated_consent_db.timestamp
        )
    
    async def list_consents(self, session: Optional[AsyncSession] = None) -> List[UserConsent]:
        """
        List all user consent records.
        
        Args:
            session: Optional database session (will create one if not provided)
            
        Returns:
            A list of all user consent records
        """
        # Get from database
        if session:
            repo = ConsentRepository(session)
            consents_db = await repo.list_consents()
        else:
            async for db_session in get_db_session():
                repo = ConsentRepository(db_session)
                consents_db = await repo.list_consents()
                break
        
        # Convert database models to Pydantic models
        return [
            UserConsent(
                user_id=consent_db.user_id,
                terms_accepted=consent_db.terms_accepted,
                marketing_consent=consent_db.marketing_consent,
                timestamp=consent_db.timestamp
            )
            for consent_db in consents_db
        ]


# Create a singleton instance of the user consent service
user_consent_service = UserConsentService()

# Backward compatibility wrapper functions for synchronous usage
# These should be used sparingly and only during migration
async def get_user_consent_service_instance() -> UserConsentService:
    """Get the user consent service instance (async-compatible)."""
    return user_consent_service