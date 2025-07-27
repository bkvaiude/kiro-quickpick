"""Batch operations for improved database performance."""

import logging
from typing import List, Dict, Any, Optional, TypeVar, Generic, Callable
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, update, delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert as pg_insert

from .models import UserCreditsDB, CreditTransactionDB, UserConsentDB, QueryCacheDB
from .performance import monitor_query_performance

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BatchOperationError(Exception):
    """Exception raised when batch operations fail."""
    pass


class BatchProcessor(Generic[T]):
    """Generic batch processor for database operations."""
    
    def __init__(self, session: AsyncSession, model_class: type, batch_size: int = 100):
        self.session = session
        self.model_class = model_class
        self.batch_size = batch_size
    
    async def batch_insert(self, records: List[Dict[str, Any]]) -> int:
        """Insert multiple records in batches."""
        if not records:
            return 0
        
        total_inserted = 0
        
        async with monitor_query_performance(
            self.session, 
            "BATCH_INSERT", 
            self.model_class.__tablename__
        ):
            try:
                # Process in batches
                for i in range(0, len(records), self.batch_size):
                    batch = records[i:i + self.batch_size]
                    
                    stmt = insert(self.model_class).values(batch)
                    result = await self.session.execute(stmt)
                    total_inserted += result.rowcount
                
                await self.session.flush()
                logger.info(f"Batch inserted {total_inserted} records into {self.model_class.__tablename__}")
                return total_inserted
                
            except SQLAlchemyError as e:
                logger.error(f"Batch insert failed for {self.model_class.__tablename__}: {e}")
                await self.session.rollback()
                raise BatchOperationError(f"Batch insert failed: {e}") from e
    
    async def batch_upsert(self, records: List[Dict[str, Any]], conflict_columns: List[str]) -> int:
        """Upsert (insert or update) multiple records in batches."""
        if not records:
            return 0
        
        total_upserted = 0
        
        async with monitor_query_performance(
            self.session, 
            "BATCH_UPSERT", 
            self.model_class.__tablename__
        ):
            try:
                # Process in batches
                for i in range(0, len(records), self.batch_size):
                    batch = records[i:i + self.batch_size]
                    
                    # Use PostgreSQL's ON CONFLICT for upsert
                    stmt = pg_insert(self.model_class).values(batch)
                    
                    # Create update dict excluding conflict columns
                    update_dict = {
                        col.name: stmt.excluded[col.name] 
                        for col in self.model_class.__table__.columns 
                        if col.name not in conflict_columns
                    }
                    
                    stmt = stmt.on_conflict_do_update(
                        index_elements=conflict_columns,
                        set_=update_dict
                    )
                    
                    result = await self.session.execute(stmt)
                    total_upserted += result.rowcount
                
                await self.session.flush()
                logger.info(f"Batch upserted {total_upserted} records into {self.model_class.__tablename__}")
                return total_upserted
                
            except SQLAlchemyError as e:
                logger.error(f"Batch upsert failed for {self.model_class.__tablename__}: {e}")
                await self.session.rollback()
                raise BatchOperationError(f"Batch upsert failed: {e}") from e
    
    async def batch_update(
        self, 
        updates: List[Dict[str, Any]], 
        key_column: str = 'id'
    ) -> int:
        """Update multiple records in batches."""
        if not updates:
            return 0
        
        total_updated = 0
        
        async with monitor_query_performance(
            self.session, 
            "BATCH_UPDATE", 
            self.model_class.__tablename__
        ):
            try:
                # Process in batches
                for i in range(0, len(updates), self.batch_size):
                    batch = updates[i:i + self.batch_size]
                    
                    # Group updates by the values being updated
                    update_groups = {}
                    for record in batch:
                        key_value = record[key_column]
                        update_values = {k: v for k, v in record.items() if k != key_column}
                        
                        # Create a hashable key for grouping
                        update_key = tuple(sorted(update_values.items()))
                        
                        if update_key not in update_groups:
                            update_groups[update_key] = {
                                'values': dict(update_key),
                                'keys': []
                            }
                        update_groups[update_key]['keys'].append(key_value)
                    
                    # Execute grouped updates
                    for group in update_groups.values():
                        key_column_obj = getattr(self.model_class, key_column)
                        stmt = update(self.model_class).where(
                            key_column_obj.in_(group['keys'])
                        ).values(**group['values'])
                        
                        result = await self.session.execute(stmt)
                        total_updated += result.rowcount
                
                await self.session.flush()
                logger.info(f"Batch updated {total_updated} records in {self.model_class.__tablename__}")
                return total_updated
                
            except SQLAlchemyError as e:
                logger.error(f"Batch update failed for {self.model_class.__tablename__}: {e}")
                await self.session.rollback()
                raise BatchOperationError(f"Batch update failed: {e}") from e
    
    async def batch_delete(self, key_values: List[Any], key_column: str = 'id') -> int:
        """Delete multiple records in batches."""
        if not key_values:
            return 0
        
        total_deleted = 0
        
        async with monitor_query_performance(
            self.session, 
            "BATCH_DELETE", 
            self.model_class.__tablename__
        ):
            try:
                # Process in batches
                for i in range(0, len(key_values), self.batch_size):
                    batch = key_values[i:i + self.batch_size]
                    
                    key_column_obj = getattr(self.model_class, key_column)
                    stmt = delete(self.model_class).where(key_column_obj.in_(batch))
                    
                    result = await self.session.execute(stmt)
                    total_deleted += result.rowcount
                
                await self.session.flush()
                logger.info(f"Batch deleted {total_deleted} records from {self.model_class.__tablename__}")
                return total_deleted
                
            except SQLAlchemyError as e:
                logger.error(f"Batch delete failed for {self.model_class.__tablename__}: {e}")
                await self.session.rollback()
                raise BatchOperationError(f"Batch delete failed: {e}") from e


class CreditBatchOperations:
    """Specialized batch operations for credit-related tables."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.credit_processor = BatchProcessor(session, UserCreditsDB)
        self.transaction_processor = BatchProcessor(session, CreditTransactionDB)
    
    async def batch_reset_credits(
        self, 
        user_ids: List[str], 
        reset_timestamp: datetime
    ) -> int:
        """Batch reset credits for multiple users with transaction logging."""
        if not user_ids:
            return 0
        
        try:
            # First, get current credit info for users
            result = await self.session.execute(
                select(UserCreditsDB).where(UserCreditsDB.user_id.in_(user_ids))
            )
            current_credits = {row.user_id: row for row in result.scalars()}
            
            # Prepare credit updates
            credit_updates = []
            transaction_records = []
            
            for user_id in user_ids:
                if user_id in current_credits:
                    user_credit = current_credits[user_id]
                    
                    # Prepare credit update
                    credit_updates.append({
                        'user_id': user_id,
                        'available_credits': user_credit.max_credits,
                        'last_reset_timestamp': reset_timestamp,
                        'updated_at': datetime.utcnow()
                    })
                    
                    # Prepare transaction record
                    credits_added = user_credit.max_credits - user_credit.available_credits
                    if credits_added > 0:
                        transaction_records.append({
                            'user_id': user_id,
                            'transaction_type': 'reset',
                            'amount': credits_added,
                            'timestamp': reset_timestamp,
                            'description': f'Daily credit reset: {credits_added} credits added'
                        })
            
            # Execute batch operations
            updated_count = 0
            if credit_updates:
                updated_count = await self.credit_processor.batch_update(
                    credit_updates, 
                    key_column='user_id'
                )
            
            if transaction_records:
                await self.transaction_processor.batch_insert(transaction_records)
            
            logger.info(f"Batch reset credits for {updated_count} users")
            return updated_count
            
        except Exception as e:
            logger.error(f"Batch credit reset failed: {e}")
            await self.session.rollback()
            raise BatchOperationError(f"Batch credit reset failed: {e}") from e
    
    async def batch_deduct_credits(
        self, 
        user_credit_deductions: List[Dict[str, Any]]
    ) -> int:
        """Batch deduct credits for multiple users with transaction logging."""
        if not user_credit_deductions:
            return 0
        
        try:
            user_ids = [item['user_id'] for item in user_credit_deductions]
            
            # Get current credit info
            result = await self.session.execute(
                select(UserCreditsDB).where(UserCreditsDB.user_id.in_(user_ids))
            )
            current_credits = {row.user_id: row for row in result.scalars()}
            
            # Prepare updates and transactions
            credit_updates = []
            transaction_records = []
            
            for deduction in user_credit_deductions:
                user_id = deduction['user_id']
                amount = deduction['amount']
                description = deduction.get('description', 'Credit deduction')
                
                if user_id in current_credits:
                    user_credit = current_credits[user_id]
                    new_available = max(0, user_credit.available_credits - amount)
                    
                    credit_updates.append({
                        'user_id': user_id,
                        'available_credits': new_available,
                        'updated_at': datetime.utcnow()
                    })
                    
                    transaction_records.append({
                        'user_id': user_id,
                        'transaction_type': 'deduct',
                        'amount': -amount,  # Negative for deduction
                        'timestamp': datetime.utcnow(),
                        'description': description
                    })
            
            # Execute batch operations
            updated_count = 0
            if credit_updates:
                updated_count = await self.credit_processor.batch_update(
                    credit_updates, 
                    key_column='user_id'
                )
            
            if transaction_records:
                await self.transaction_processor.batch_insert(transaction_records)
            
            logger.info(f"Batch deducted credits for {updated_count} users")
            return updated_count
            
        except Exception as e:
            logger.error(f"Batch credit deduction failed: {e}")
            await self.session.rollback()
            raise BatchOperationError(f"Batch credit deduction failed: {e}") from e


class CacheBatchOperations:
    """Specialized batch operations for cache management."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.cache_processor = BatchProcessor(session, QueryCacheDB)
    
    async def batch_cache_results(
        self, 
        cache_entries: List[Dict[str, Any]]
    ) -> int:
        """Batch cache multiple query results."""
        if not cache_entries:
            return 0
        
        try:
            # Use upsert to handle conflicts
            upserted_count = await self.cache_processor.batch_upsert(
                cache_entries, 
                conflict_columns=['query_hash']
            )
            
            logger.info(f"Batch cached {upserted_count} query results")
            return upserted_count
            
        except Exception as e:
            logger.error(f"Batch cache operation failed: {e}")
            await self.session.rollback()
            raise BatchOperationError(f"Batch cache operation failed: {e}") from e
    
    async def batch_cleanup_expired_cache(self, batch_size: int = 1000) -> int:
        """Clean up expired cache entries in batches."""
        try:
            current_time = datetime.utcnow()
            total_deleted = 0
            
            while True:
                # Get a batch of expired entries
                result = await self.session.execute(
                    select(QueryCacheDB.query_hash)
                    .where(QueryCacheDB.expires_at <= current_time)
                    .limit(batch_size)
                )
                
                expired_hashes = [row.query_hash for row in result.scalars()]
                
                if not expired_hashes:
                    break
                
                # Delete this batch
                deleted_count = await self.cache_processor.batch_delete(
                    expired_hashes, 
                    key_column='query_hash'
                )
                
                total_deleted += deleted_count
                
                # If we deleted fewer than batch_size, we're done
                if deleted_count < batch_size:
                    break
            
            logger.info(f"Batch cleaned up {total_deleted} expired cache entries")
            return total_deleted
            
        except Exception as e:
            logger.error(f"Batch cache cleanup failed: {e}")
            await self.session.rollback()
            raise BatchOperationError(f"Batch cache cleanup failed: {e}") from e


class ConsentBatchOperations:
    """Specialized batch operations for consent management."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.consent_processor = BatchProcessor(session, UserConsentDB)
    
    async def batch_update_marketing_consent(
        self, 
        user_ids: List[str], 
        marketing_consent: bool
    ) -> int:
        """Batch update marketing consent for multiple users."""
        if not user_ids:
            return 0
        
        try:
            consent_updates = [
                {
                    'user_id': user_id,
                    'marketing_consent': marketing_consent,
                    'updated_at': datetime.utcnow()
                }
                for user_id in user_ids
            ]
            
            updated_count = await self.consent_processor.batch_update(
                consent_updates, 
                key_column='user_id'
            )
            
            logger.info(f"Batch updated marketing consent for {updated_count} users")
            return updated_count
            
        except Exception as e:
            logger.error(f"Batch consent update failed: {e}")
            await self.session.rollback()
            raise BatchOperationError(f"Batch consent update failed: {e}") from e
    
    async def batch_create_default_consents(
        self, 
        user_ids: List[str]
    ) -> int:
        """Batch create default consent records for new users."""
        if not user_ids:
            return 0
        
        try:
            current_time = datetime.utcnow()
            consent_records = [
                {
                    'user_id': user_id,
                    'terms_accepted': True,
                    'marketing_consent': False,
                    'timestamp': current_time,
                    'updated_at': current_time
                }
                for user_id in user_ids
            ]
            
            # Use upsert to handle potential conflicts
            upserted_count = await self.consent_processor.batch_upsert(
                consent_records, 
                conflict_columns=['user_id']
            )
            
            logger.info(f"Batch created default consents for {upserted_count} users")
            return upserted_count
            
        except Exception as e:
            logger.error(f"Batch consent creation failed: {e}")
            await self.session.rollback()
            raise BatchOperationError(f"Batch consent creation failed: {e}") from e


# Factory functions for easy access
def create_credit_batch_ops(session: AsyncSession) -> CreditBatchOperations:
    """Create credit batch operations instance."""
    return CreditBatchOperations(session)


def create_cache_batch_ops(session: AsyncSession) -> CacheBatchOperations:
    """Create cache batch operations instance."""
    return CacheBatchOperations(session)


def create_consent_batch_ops(session: AsyncSession) -> ConsentBatchOperations:
    """Create consent batch operations instance."""
    return ConsentBatchOperations(session)