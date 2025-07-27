from typing import Dict, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings, logger
from app.models.credit import UserCredits, CreditTransaction, CreditStatus
from app.database.repositories.credit_repository import CreditRepository
from app.database.models import UserCreditsDB, CreditTransactionDB
from app.database.manager import get_db_session


class CreditService:
    """
    Service for managing message credits for both guest and registered users
    """
    
    def __init__(self):
        self.config = settings.credit_system
    
    async def get_user_credits(self, user_id: str, is_guest: bool = False, session: Optional[AsyncSession] = None) -> UserCredits:
        """
        Gets or creates user credit information
        
        Args:
            user_id: The user identifier (session ID for guests, auth0 ID for registered)
            is_guest: Whether the user is a guest user
            session: Optional database session (will create one if not provided)
            
        Returns:
            UserCredits: The user's credit information
        """

        # Use provided session or create a new one
        if session:
            repo = CreditRepository(session)
            user_credits_db = await repo.get_user_credits(user_id)
        else:
            async for db_session in get_db_session():
                repo = CreditRepository(db_session)
                user_credits_db = await repo.get_user_credits(user_id)
                break
        
        if user_credits_db is None:
            # Create new user credits
            max_credits = (
                self.config.max_guest_credits if is_guest 
                else self.config.max_registered_credits
            )
            
            new_credits_db = UserCreditsDB(
                user_id=user_id,
                is_guest=is_guest,
                available_credits=max_credits,
                max_credits=max_credits,
                last_reset_timestamp=datetime.utcnow()
            )
            
            # Save to database
            if session:
                repo = CreditRepository(session)
                user_credits_db = await repo.create_user_credits(new_credits_db)
                
                # Log credit allocation
                await self._log_transaction(
                    user_id=user_id,
                    transaction_type="allocate",
                    amount=max_credits,
                    description=f"Initial credit allocation for {'guest' if is_guest else 'registered'} user",
                    session=session
                )
            else:
                async for db_session in get_db_session():
                    repo = CreditRepository(db_session)
                    user_credits_db = await repo.create_user_credits(new_credits_db)
                    
                    # Log credit allocation
                    await self._log_transaction(
                        user_id=user_id,
                        transaction_type="allocate",
                        amount=max_credits,
                        description=f"Initial credit allocation for {'guest' if is_guest else 'registered'} user",
                        session=db_session
                    )
                    break
            
            logger.info(f"Created new credit account for {'guest' if is_guest else 'registered'} user {user_id}: {max_credits} credits")
        
        # Convert database model to Pydantic model
        return UserCredits(
            user_id=user_credits_db.user_id,
            is_guest=user_credits_db.is_guest,
            available_credits=user_credits_db.available_credits,
            max_credits=user_credits_db.max_credits,
            last_reset_timestamp=user_credits_db.last_reset_timestamp
        )
    
    async def check_credits(self, user_id: str, is_guest: bool = False, session: Optional[AsyncSession] = None) -> int:
        """
        Checks available credits for a user
        
        Args:
            user_id: The user identifier
            is_guest: Whether the user is a guest user
            session: Optional database session (will create one if not provided)
            
        Returns:
            int: Number of available credits
        """
        user_credits = await self.get_user_credits(user_id, is_guest, session)
        
        # For registered users, check if credits need to be reset
        if not is_guest:
            user_credits = await self._check_and_reset_credits(user_credits, session)
        
        return user_credits.available_credits
    
    async def deduct_credit(self, user_id: str, is_guest: bool = False, amount: int = 1, session: Optional[AsyncSession] = None) -> bool:
        """
        Deducts credits from a user's balance
        
        Args:
            user_id: The user identifier
            is_guest: Whether the user is a guest user
            amount: Number of credits to deduct (default: 1)
            session: Optional database session (will create one if not provided)
            
        Returns:
            bool: True if successful, False if insufficient credits or invalid amount
        """
        # Validate amount
        if amount < 0:
            logger.warning(f"Invalid credit deduction amount for user {user_id}: {amount} (cannot be negative)")
            return False
        
        # Handle zero amount case
        if amount == 0:
            logger.debug(f"Zero credit deduction for user {user_id}, no action taken")
            return True
        
        user_credits = await self.get_user_credits(user_id, is_guest, session)
        
        # For registered users, check if credits need to be reset
        if not is_guest:
            user_credits = await self._check_and_reset_credits(user_credits, session)
        
        # Check if user has sufficient credits
        if user_credits.available_credits < amount:
            logger.warning(f"Insufficient credits for user {user_id}: {user_credits.available_credits} < {amount}")
            return False
        
        # Deduct credits in database
        new_available_credits = user_credits.available_credits - amount
        
        if session:
            repo = CreditRepository(session)
            await repo.update_user_credits(user_id, available_credits=new_available_credits)
            
            # Log transaction
            await self._log_transaction(
                user_id=user_id,
                transaction_type="deduct",
                amount=-amount,  # Negative amount for deduction
                description="Credit deducted for message",
                session=session
            )
        else:
            async for db_session in get_db_session():
                repo = CreditRepository(db_session)
                await repo.update_user_credits(user_id, available_credits=new_available_credits)
                
                # Log transaction
                await self._log_transaction(
                    user_id=user_id,
                    transaction_type="deduct",
                    amount=-amount,  # Negative amount for deduction
                    description="Credit deducted for message",
                    session=db_session
                )
                break
        
        logger.debug(f"Deducted {amount} credit(s) from user {user_id}, remaining: {new_available_credits}")
        
        return True
    
    async def reset_credits(self, user_id: Optional[str] = None, session: Optional[AsyncSession] = None) -> None:
        """
        Resets credits for a specific user or all registered users
        
        Args:
            user_id: The user identifier (if None, resets all registered users)
            session: Optional database session (will create one if not provided)
        """
        if user_id:
            # Reset specific user
            if session:
                repo = CreditRepository(session)
                user_credits_db = await repo.get_user_credits(user_id)
                
                if user_credits_db and not user_credits_db.is_guest:
                    old_credits = user_credits_db.available_credits
                    reset_timestamp = datetime.utcnow()
                    
                    await repo.update_user_credits(
                        user_id,
                        available_credits=user_credits_db.max_credits,
                        last_reset_timestamp=reset_timestamp
                    )
                    
                    await self._log_transaction(
                        user_id=user_id,
                        transaction_type="reset",
                        amount=user_credits_db.max_credits - old_credits,
                        description="Daily credit reset",
                        session=session
                    )
                    
                    logger.info(f"Reset credits for user {user_id}: {old_credits} -> {user_credits_db.max_credits}")
            else:
                async for db_session in get_db_session():
                    repo = CreditRepository(db_session)
                    user_credits_db = await repo.get_user_credits(user_id)
                    
                    if user_credits_db and not user_credits_db.is_guest:
                        old_credits = user_credits_db.available_credits
                        reset_timestamp = datetime.utcnow()
                        
                        await repo.update_user_credits(
                            user_id,
                            available_credits=user_credits_db.max_credits,
                            last_reset_timestamp=reset_timestamp
                        )
                        
                        await self._log_transaction(
                            user_id=user_id,
                            transaction_type="reset",
                            amount=user_credits_db.max_credits - old_credits,
                            description="Daily credit reset",
                            session=db_session
                        )
                        
                        logger.info(f"Reset credits for user {user_id}: {old_credits} -> {user_credits_db.max_credits}")
                    break
        else:
            # Reset all registered users using batch operation
            reset_timestamp = datetime.utcnow()
            
            if session:
                repo = CreditRepository(session)
                users_needing_reset = await repo.get_users_needing_reset(self.config.credit_reset_interval_hours)
                
                if users_needing_reset:
                    user_ids = [user.user_id for user in users_needing_reset if not user.is_guest]
                    reset_count = await repo.batch_reset_credits(user_ids, reset_timestamp)
                    
                    # Log transactions for each reset user
                    for user in users_needing_reset:
                        if not user.is_guest:
                            await self._log_transaction(
                                user_id=user.user_id,
                                transaction_type="reset",
                                amount=user.max_credits - user.available_credits,
                                description="Daily credit reset (batch)",
                                session=session
                            )
                    
                    logger.info(f"Reset credits for {reset_count} registered users")
            else:
                async for db_session in get_db_session():
                    repo = CreditRepository(db_session)
                    users_needing_reset = await repo.get_users_needing_reset(self.config.credit_reset_interval_hours)
                    
                    if users_needing_reset:
                        user_ids = [user.user_id for user in users_needing_reset if not user.is_guest]
                        reset_count = await repo.batch_reset_credits(user_ids, reset_timestamp)
                        
                        # Log transactions for each reset user
                        for user in users_needing_reset:
                            if not user.is_guest:
                                await self._log_transaction(
                                    user_id=user.user_id,
                                    transaction_type="reset",
                                    amount=user.max_credits - user.available_credits,
                                    description="Daily credit reset (batch)",
                                    session=db_session
                                )
                        
                        logger.info(f"Reset credits for {reset_count} registered users")
                    break
    
    async def get_credit_status(self, user_id: str, is_guest: bool = False, session: Optional[AsyncSession] = None) -> CreditStatus:
        """
        Gets comprehensive credit status for a user
        
        Args:
            user_id: The user identifier
            is_guest: Whether the user is a guest user
            session: Optional database session (will create one if not provided)
            
        Returns:
            CreditStatus: Comprehensive credit status information
        """
        user_credits = await self.get_user_credits(user_id, is_guest, session)
        
        # For registered users, check if credits need to be reset
        if not is_guest:
            user_credits = await self._check_and_reset_credits(user_credits, session)
        
        # Calculate next reset time for registered users
        next_reset_time = None
        if not is_guest:
            next_reset_time = user_credits.last_reset_timestamp + timedelta(
                hours=self.config.credit_reset_interval_hours
            )
        
        return CreditStatus(
            available_credits=user_credits.available_credits,
            max_credits=user_credits.max_credits,
            is_guest=is_guest,
            can_reset=not is_guest,  # Only registered users can have credits reset
            next_reset_time=next_reset_time
        )
    
    async def _check_and_reset_credits(self, user_credits: UserCredits, session: Optional[AsyncSession] = None) -> UserCredits:
        """
        Checks if registered user credits need to be reset and resets them if necessary
        
        Args:
            user_credits: The user's credit information
            session: Optional database session (will create one if not provided)
            
        Returns:
            UserCredits: Updated user credits (may be the same if no reset needed)
        """
        if user_credits.is_guest:
            return user_credits
        
        # Check if reset interval has passed
        reset_interval = timedelta(hours=self.config.credit_reset_interval_hours)
        if datetime.utcnow() - user_credits.last_reset_timestamp >= reset_interval:
            old_credits = user_credits.available_credits
            reset_timestamp = datetime.utcnow()
            
            if session:
                repo = CreditRepository(session)
                await repo.update_user_credits(
                    user_credits.user_id,
                    available_credits=user_credits.max_credits,
                    last_reset_timestamp=reset_timestamp
                )
                
                await self._log_transaction(
                    user_id=user_credits.user_id,
                    transaction_type="reset",
                    amount=user_credits.max_credits - old_credits,
                    description="Automatic daily credit reset",
                    session=session
                )
            else:
                async for db_session in get_db_session():
                    repo = CreditRepository(db_session)
                    await repo.update_user_credits(
                        user_credits.user_id,
                        available_credits=user_credits.max_credits,
                        last_reset_timestamp=reset_timestamp
                    )
                    
                    await self._log_transaction(
                        user_id=user_credits.user_id,
                        transaction_type="reset",
                        amount=user_credits.max_credits - old_credits,
                        description="Automatic daily credit reset",
                        session=db_session
                    )
                    break
            
            # Update the in-memory object
            user_credits.available_credits = user_credits.max_credits
            user_credits.last_reset_timestamp = reset_timestamp
            
            logger.info(f"Auto-reset credits for user {user_credits.user_id}: {old_credits} -> {user_credits.available_credits}")
        
        return user_credits
    
    async def _log_transaction(self, user_id: str, transaction_type: str, amount: int, description: str = None, session: Optional[AsyncSession] = None) -> None:
        """
        Logs a credit transaction
        
        Args:
            user_id: The user identifier
            transaction_type: Type of transaction ('deduct', 'reset', 'allocate')
            amount: Amount of credits involved
            description: Optional description of the transaction
            session: Optional database session (will create one if not provided)
        """
        transaction_db = CreditTransactionDB(
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            timestamp=datetime.utcnow()
        )
        
        if session:
            repo = CreditRepository(session)
            await repo.create_transaction(transaction_db)
        else:
            async for db_session in get_db_session():
                repo = CreditRepository(db_session)
                await repo.create_transaction(transaction_db)
                break
    
    async def get_user_transactions(self, user_id: str, limit: int = 100, session: Optional[AsyncSession] = None) -> List[CreditTransaction]:
        """
        Gets recent transactions for a user
        
        Args:
            user_id: The user identifier
            limit: Maximum number of transactions to return
            session: Optional database session (will create one if not provided)
            
        Returns:
            List[CreditTransaction]: Recent transactions for the user
        """
        if session:
            repo = CreditRepository(session)
            transactions_db = await repo.get_user_transactions(user_id, limit=limit)
        else:
            async for db_session in get_db_session():
                repo = CreditRepository(db_session)
                transactions_db = await repo.get_user_transactions(user_id, limit=limit)
                break
        
        # Convert database models to Pydantic models
        return [
            CreditTransaction(
                user_id=t.user_id,
                transaction_type=t.transaction_type,
                amount=t.amount,
                timestamp=t.timestamp,
                description=t.description
            )
            for t in transactions_db
        ]


# Create a singleton instance of the credit service
credit_service = CreditService()

# Backward compatibility wrapper functions for synchronous usage
# These should be used sparingly and only during migration
async def get_credit_service_instance() -> CreditService:
    """Get the credit service instance (async-compatible)."""
    return credit_service