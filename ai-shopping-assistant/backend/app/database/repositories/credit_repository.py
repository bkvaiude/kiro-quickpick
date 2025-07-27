"""Credit repository for managing user credits and credit transactions."""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc, and_, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from .base import BaseRepository, RepositoryError, RepositoryIntegrityError
from ..models import UserCreditsDB, CreditTransactionDB

logger = logging.getLogger(__name__)


class CreditRepository(BaseRepository[UserCreditsDB]):
    """Repository for managing user credits and credit transactions."""
    
    def __init__(self, session: AsyncSession):
        """Initialize the credit repository."""
        super().__init__(session, UserCreditsDB)
    
    # User Credits CRUD Operations
    
    async def get_user_credits(self, user_id: str) -> Optional[UserCreditsDB]:
        """
        Get user credit information by user ID.
        
        Args:
            user_id: The user identifier
            
        Returns:
            User credits if found, None otherwise
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            result = await self.session.execute(
                select(UserCreditsDB).where(UserCreditsDB.user_id == user_id)
            )
            user_credits = result.scalar_one_or_none()
            
            if user_credits:
                logger.debug(f"Retrieved credits for user {user_id}: {user_credits.available_credits}/{user_credits.max_credits}")
            else:
                logger.debug(f"No credits found for user {user_id}")
            
            return user_credits
        except SQLAlchemyError as e:
            logger.error(f"Failed to get user credits for {user_id}: {e}")
            raise RepositoryError(f"Failed to get user credits: {e}") from e
    
    async def create_user_credits(self, user_credits: UserCreditsDB) -> UserCreditsDB:
        """
        Create new user credit record.
        
        Args:
            user_credits: The user credits instance to create
            
        Returns:
            The created user credits
            
        Raises:
            RepositoryIntegrityError: If user already exists
            RepositoryError: If creation fails
        """
        try:
            created_credits = await self.create(user_credits)
            logger.info(f"Created credits for user {user_credits.user_id}: {user_credits.available_credits}/{user_credits.max_credits}")
            return created_credits
        except RepositoryIntegrityError:
            logger.warning(f"User credits already exist for user {user_credits.user_id}")
            raise
        except Exception as e:
            logger.error(f"Failed to create user credits for {user_credits.user_id}: {e}")
            raise RepositoryError(f"Failed to create user credits: {e}") from e
    
    async def update_user_credits(self, user_id: str, **updates) -> Optional[UserCreditsDB]:
        """
        Update user credit information.
        
        Args:
            user_id: The user identifier
            **updates: Fields to update
            
        Returns:
            Updated user credits if found, None otherwise
            
        Raises:
            RepositoryIntegrityError: If integrity constraints are violated
            RepositoryError: If update fails
        """
        try:
            # Add updated_at timestamp
            updates['updated_at'] = datetime.utcnow()
            
            updated_credits = await self.update_by_id(user_id, **updates)
            
            if updated_credits:
                logger.debug(f"Updated credits for user {user_id}: {updates}")
            else:
                logger.warning(f"No user credits found to update for user {user_id}")
            
            return updated_credits
        except Exception as e:
            logger.error(f"Failed to update user credits for {user_id}: {e}")
            raise
    
    async def delete_user_credits(self, user_id: str) -> bool:
        """
        Delete user credit record.
        
        Args:
            user_id: The user identifier
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            RepositoryError: If deletion fails
        """
        try:
            deleted = await self.delete_by_id(user_id)
            
            if deleted:
                logger.info(f"Deleted credits for user {user_id}")
            else:
                logger.debug(f"No user credits found to delete for user {user_id}")
            
            return deleted
        except Exception as e:
            logger.error(f"Failed to delete user credits for {user_id}: {e}")
            raise
    
    # Credit Transaction Operations
    
    async def create_transaction(self, transaction: CreditTransactionDB) -> CreditTransactionDB:
        """
        Create a new credit transaction record.
        
        Args:
            transaction: The transaction instance to create
            
        Returns:
            The created transaction
            
        Raises:
            RepositoryError: If creation fails
        """
        try:
            self.session.add(transaction)
            await self.flush()
            await self.refresh(transaction)
            
            logger.debug(f"Created transaction for user {transaction.user_id}: "
                        f"{transaction.transaction_type} {transaction.amount}")
            return transaction
        except SQLAlchemyError as e:
            logger.error(f"Failed to create transaction: {e}")
            await self.rollback()
            raise RepositoryError(f"Failed to create transaction: {e}") from e
    
    async def get_user_transactions(
        self, 
        user_id: str, 
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        transaction_type: Optional[str] = None
    ) -> List[CreditTransactionDB]:
        """
        Get transaction history for a user.
        
        Args:
            user_id: The user identifier
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            transaction_type: Filter by transaction type (optional)
            
        Returns:
            List of transactions ordered by timestamp (newest first)
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            query = select(CreditTransactionDB).where(CreditTransactionDB.user_id == user_id)
            
            # Add transaction type filter if specified
            if transaction_type:
                query = query.where(CreditTransactionDB.transaction_type == transaction_type)
            
            # Order by timestamp descending (newest first)
            query = query.order_by(desc(CreditTransactionDB.timestamp))
            
            # Apply pagination
            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)
            
            result = await self.session.execute(query)
            transactions = result.scalars().all()
            
            logger.debug(f"Retrieved {len(transactions)} transactions for user {user_id}")
            return list(transactions)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get transactions for user {user_id}: {e}")
            raise RepositoryError(f"Failed to get user transactions: {e}") from e
    
    async def get_transaction_by_id(self, transaction_id: int) -> Optional[CreditTransactionDB]:
        """
        Get a specific transaction by ID.
        
        Args:
            transaction_id: The transaction ID
            
        Returns:
            Transaction if found, None otherwise
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            result = await self.session.execute(
                select(CreditTransactionDB).where(CreditTransactionDB.id == transaction_id)
            )
            transaction = result.scalar_one_or_none()
            
            if transaction:
                logger.debug(f"Retrieved transaction {transaction_id}")
            else:
                logger.debug(f"No transaction found with ID {transaction_id}")
            
            return transaction
        except SQLAlchemyError as e:
            logger.error(f"Failed to get transaction {transaction_id}: {e}")
            raise RepositoryError(f"Failed to get transaction: {e}") from e
    
    async def get_transactions_by_date_range(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
        transaction_type: Optional[str] = None
    ) -> List[CreditTransactionDB]:
        """
        Get transactions within a date range for a user.
        
        Args:
            user_id: The user identifier
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            transaction_type: Filter by transaction type (optional)
            
        Returns:
            List of transactions within the date range
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            query = select(CreditTransactionDB).where(
                and_(
                    CreditTransactionDB.user_id == user_id,
                    CreditTransactionDB.timestamp >= start_date,
                    CreditTransactionDB.timestamp <= end_date
                )
            )
            
            if transaction_type:
                query = query.where(CreditTransactionDB.transaction_type == transaction_type)
            
            query = query.order_by(desc(CreditTransactionDB.timestamp))
            
            result = await self.session.execute(query)
            transactions = result.scalars().all()
            
            logger.debug(f"Retrieved {len(transactions)} transactions for user {user_id} "
                        f"between {start_date} and {end_date}")
            return list(transactions)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get transactions by date range for user {user_id}: {e}")
            raise RepositoryError(f"Failed to get transactions by date range: {e}") from e
    
    # Cleanup and Maintenance Operations
    
    async def cleanup_old_transactions(self, days: int = 90) -> int:
        """
        Clean up old transaction records.
        
        Args:
            days: Number of days to keep transactions (default: 90)
            
        Returns:
            Number of transactions deleted
            
        Raises:
            RepositoryError: If cleanup fails
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Delete old transactions
            result = await self.session.execute(
                delete(CreditTransactionDB).where(CreditTransactionDB.timestamp < cutoff_date)
            )
            
            deleted_count = result.rowcount
            await self.flush()
            
            logger.info(f"Cleaned up {deleted_count} transactions older than {days} days")
            return deleted_count
        except SQLAlchemyError as e:
            logger.error(f"Failed to cleanup old transactions: {e}")
            await self.rollback()
            raise RepositoryError(f"Failed to cleanup old transactions: {e}") from e
    
    async def get_transaction_statistics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get transaction statistics for a user.
        
        Args:
            user_id: The user identifier
            days: Number of days to analyze (default: 30)
            
        Returns:
            Dictionary with transaction statistics
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get transaction counts and totals by type
            result = await self.session.execute(
                select(
                    CreditTransactionDB.transaction_type,
                    func.count(CreditTransactionDB.id).label('count'),
                    func.sum(CreditTransactionDB.amount).label('total_amount')
                )
                .where(
                    and_(
                        CreditTransactionDB.user_id == user_id,
                        CreditTransactionDB.timestamp >= cutoff_date
                    )
                )
                .group_by(CreditTransactionDB.transaction_type)
            )
            
            statistics = {
                'period_days': days,
                'transactions_by_type': {},
                'total_transactions': 0,
                'net_credit_change': 0
            }
            
            for row in result:
                transaction_type = row.transaction_type
                count = row.count
                total_amount = row.total_amount or 0
                
                statistics['transactions_by_type'][transaction_type] = {
                    'count': count,
                    'total_amount': total_amount
                }
                statistics['total_transactions'] += count
                statistics['net_credit_change'] += total_amount
            
            logger.debug(f"Generated transaction statistics for user {user_id}: {statistics}")
            return statistics
        except SQLAlchemyError as e:
            logger.error(f"Failed to get transaction statistics for user {user_id}: {e}")
            raise RepositoryError(f"Failed to get transaction statistics: {e}") from e
    
    # Batch Operations
    
    async def get_users_needing_reset(self, reset_threshold_hours: int = 24) -> List[UserCreditsDB]:
        """
        Get users whose credits need to be reset based on last reset timestamp.
        
        Args:
            reset_threshold_hours: Hours since last reset to trigger reset (default: 24)
            
        Returns:
            List of user credits that need reset
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            threshold_time = datetime.utcnow() - timedelta(hours=reset_threshold_hours)
            
            result = await self.session.execute(
                select(UserCreditsDB).where(UserCreditsDB.last_reset_timestamp < threshold_time)
            )
            
            users_needing_reset = result.scalars().all()
            logger.debug(f"Found {len(users_needing_reset)} users needing credit reset")
            return list(users_needing_reset)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get users needing reset: {e}")
            raise RepositoryError(f"Failed to get users needing reset: {e}") from e
    
    async def batch_reset_credits(self, user_ids: List[str], reset_timestamp: datetime) -> int:
        """
        Batch reset credits for multiple users.
        
        Args:
            user_ids: List of user IDs to reset
            reset_timestamp: Timestamp to set as last reset time
            
        Returns:
            Number of users updated
            
        Raises:
            RepositoryError: If batch update fails
        """
        try:
            if not user_ids:
                return 0
            
            result = await self.session.execute(
                update(UserCreditsDB)
                .where(UserCreditsDB.user_id.in_(user_ids))
                .values(
                    available_credits=UserCreditsDB.max_credits,
                    last_reset_timestamp=reset_timestamp,
                    updated_at=datetime.utcnow()
                )
            )
            
            updated_count = result.rowcount
            await self.flush()
            
            logger.info(f"Batch reset credits for {updated_count} users")
            return updated_count
        except SQLAlchemyError as e:
            logger.error(f"Failed to batch reset credits: {e}")
            await self.rollback()
            raise RepositoryError(f"Failed to batch reset credits: {e}") from e
    
    async def get_credit_summary(self) -> Dict[str, Any]:
        """
        Get overall credit system summary statistics.
        
        Returns:
            Dictionary with credit system statistics
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            # Get user counts and credit totals
            result = await self.session.execute(
                select(
                    func.count(UserCreditsDB.user_id).label('total_users'),
                    func.count().filter(UserCreditsDB.is_guest == True).label('guest_users'),
                    func.count().filter(UserCreditsDB.is_guest == False).label('registered_users'),
                    func.sum(UserCreditsDB.available_credits).label('total_available_credits'),
                    func.sum(UserCreditsDB.max_credits).label('total_max_credits'),
                    func.avg(UserCreditsDB.available_credits).label('avg_available_credits')
                )
            )
            
            row = result.first()
            
            summary = {
                'total_users': row.total_users or 0,
                'guest_users': row.guest_users or 0,
                'registered_users': row.registered_users or 0,
                'total_available_credits': row.total_available_credits or 0,
                'total_max_credits': row.total_max_credits or 0,
                'avg_available_credits': float(row.avg_available_credits or 0)
            }
            
            logger.debug(f"Generated credit system summary: {summary}")
            return summary
        except SQLAlchemyError as e:
            logger.error(f"Failed to get credit summary: {e}")
            raise RepositoryError(f"Failed to get credit summary: {e}") from e