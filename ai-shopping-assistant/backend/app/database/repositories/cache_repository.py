"""Cache repository for managing query cache operations."""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc, and_, func, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from .base import BaseRepository, RepositoryError, RepositoryIntegrityError
from ..models import QueryCacheDB

logger = logging.getLogger(__name__)


class CacheRepository(BaseRepository[QueryCacheDB]):
    """Repository for managing query cache storage and retrieval."""
    
    def __init__(self, session: AsyncSession):
        """Initialize the cache repository."""
        super().__init__(session, QueryCacheDB)
    
    # Cache Storage and Retrieval Operations
    
    async def get_cached_result(self, query_hash: str) -> Optional[QueryCacheDB]:
        """
        Get cached result by query hash, automatically filtering expired entries.
        
        Args:
            query_hash: The query hash identifier
            
        Returns:
            Cached result if found and not expired, None otherwise
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            current_time = datetime.utcnow()
            
            result = await self.session.execute(
                select(QueryCacheDB).where(
                    and_(
                        QueryCacheDB.query_hash == query_hash,
                        QueryCacheDB.expires_at > current_time
                    )
                )
            )
            
            cached_result = result.scalar_one_or_none()
            
            if cached_result:
                logger.debug(f"Cache hit for query hash {query_hash}")
            else:
                logger.debug(f"Cache miss for query hash {query_hash}")
            
            return cached_result
        except SQLAlchemyError as e:
            logger.error(f"Failed to get cached result for hash {query_hash}: {e}")
            raise RepositoryError(f"Failed to get cached result: {e}") from e
    
    async def cache_result(self, cache_entry: QueryCacheDB) -> QueryCacheDB:
        """
        Store a result in the cache.
        
        Args:
            cache_entry: The cache entry to store
            
        Returns:
            The stored cache entry
            
        Raises:
            RepositoryError: If caching fails
        """
        try:
            # Use upsert logic - try to update first, then insert if not exists
            existing_entry = await self.session.execute(
                select(QueryCacheDB).where(QueryCacheDB.query_hash == cache_entry.query_hash)
            )
            existing = existing_entry.scalar_one_or_none()
            
            if existing:
                # Update existing entry
                updated_entry = await self.update_by_id(
                    cache_entry.query_hash,
                    result=cache_entry.result,
                    cached_at=cache_entry.cached_at,
                    expires_at=cache_entry.expires_at
                )
                logger.debug(f"Updated cache entry for hash {cache_entry.query_hash}")
                return updated_entry
            else:
                # Create new entry
                created_entry = await self.create(cache_entry)
                logger.debug(f"Created cache entry for hash {cache_entry.query_hash}")
                return created_entry
                
        except Exception as e:
            logger.error(f"Failed to cache result for hash {cache_entry.query_hash}: {e}")
            raise RepositoryError(f"Failed to cache result: {e}") from e
    
    async def invalidate_cache_entry(self, query_hash: str) -> bool:
        """
        Invalidate (delete) a specific cache entry.
        
        Args:
            query_hash: The query hash to invalidate
            
        Returns:
            True if entry was deleted, False if not found
            
        Raises:
            RepositoryError: If invalidation fails
        """
        try:
            deleted = await self.delete_by_id(query_hash)
            
            if deleted:
                logger.debug(f"Invalidated cache entry for hash {query_hash}")
            else:
                logger.debug(f"No cache entry found to invalidate for hash {query_hash}")
            
            return deleted
        except Exception as e:
            logger.error(f"Failed to invalidate cache entry for hash {query_hash}: {e}")
            raise
    
    async def get_cache_entry_info(self, query_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a cache entry including expiration status.
        
        Args:
            query_hash: The query hash identifier
            
        Returns:
            Dictionary with cache entry information, None if not found
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            result = await self.session.execute(
                select(QueryCacheDB).where(QueryCacheDB.query_hash == query_hash)
            )
            
            cache_entry = result.scalar_one_or_none()
            
            if not cache_entry:
                return None
            
            current_time = datetime.utcnow()
            is_expired = cache_entry.expires_at <= current_time
            time_to_expiry = cache_entry.expires_at - current_time
            
            info = {
                'query_hash': cache_entry.query_hash,
                'cached_at': cache_entry.cached_at,
                'expires_at': cache_entry.expires_at,
                'is_expired': is_expired,
                'time_to_expiry_seconds': time_to_expiry.total_seconds() if not is_expired else 0,
                'result_size_bytes': len(str(cache_entry.result).encode('utf-8'))
            }
            
            logger.debug(f"Retrieved cache info for hash {query_hash}: expired={is_expired}")
            return info
        except SQLAlchemyError as e:
            logger.error(f"Failed to get cache entry info for hash {query_hash}: {e}")
            raise RepositoryError(f"Failed to get cache entry info: {e}") from e
    
    # Cache Cleanup and Maintenance Operations
    
    async def cleanup_expired_cache(self) -> int:
        """
        Remove expired cache entries.
        
        Returns:
            Number of expired entries removed
            
        Raises:
            RepositoryError: If cleanup fails
        """
        try:
            current_time = datetime.utcnow()
            
            result = await self.session.execute(
                delete(QueryCacheDB).where(QueryCacheDB.expires_at <= current_time)
            )
            
            deleted_count = result.rowcount
            await self.flush()
            
            logger.info(f"Cleaned up {deleted_count} expired cache entries")
            return deleted_count
        except SQLAlchemyError as e:
            logger.error(f"Failed to cleanup expired cache: {e}")
            await self.rollback()
            raise RepositoryError(f"Failed to cleanup expired cache: {e}") from e
    
    async def cleanup_old_cache(self, days: int = 7) -> int:
        """
        Remove cache entries older than specified days, regardless of expiration.
        
        Args:
            days: Number of days to keep cache entries (default: 7)
            
        Returns:
            Number of old entries removed
            
        Raises:
            RepositoryError: If cleanup fails
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = await self.session.execute(
                delete(QueryCacheDB).where(QueryCacheDB.cached_at < cutoff_date)
            )
            
            deleted_count = result.rowcount
            await self.flush()
            
            logger.info(f"Cleaned up {deleted_count} cache entries older than {days} days")
            return deleted_count
        except SQLAlchemyError as e:
            logger.error(f"Failed to cleanup old cache: {e}")
            await self.rollback()
            raise RepositoryError(f"Failed to cleanup old cache: {e}") from e
    
    async def clear_cache(self) -> int:
        """
        Clear all cache entries.
        
        Returns:
            Number of entries cleared
            
        Raises:
            RepositoryError: If clearing fails
        """
        try:
            result = await self.session.execute(delete(QueryCacheDB))
            
            deleted_count = result.rowcount
            await self.flush()
            
            logger.info(f"Cleared all cache entries: {deleted_count} entries removed")
            return deleted_count
        except SQLAlchemyError as e:
            logger.error(f"Failed to clear cache: {e}")
            await self.rollback()
            raise RepositoryError(f"Failed to clear cache: {e}") from e
    
    async def cleanup_cache_by_size_limit(self, max_entries: int) -> int:
        """
        Remove oldest cache entries to stay within size limit.
        
        Args:
            max_entries: Maximum number of cache entries to keep
            
        Returns:
            Number of entries removed
            
        Raises:
            RepositoryError: If cleanup fails
        """
        try:
            # Count current entries
            count_result = await self.session.execute(
                select(func.count(QueryCacheDB.query_hash))
            )
            current_count = count_result.scalar()
            
            if current_count <= max_entries:
                logger.debug(f"Cache size ({current_count}) within limit ({max_entries})")
                return 0
            
            # Calculate how many to remove
            entries_to_remove = current_count - max_entries
            
            # Get oldest entries to remove
            oldest_entries = await self.session.execute(
                select(QueryCacheDB.query_hash)
                .order_by(QueryCacheDB.cached_at)
                .limit(entries_to_remove)
            )
            
            hashes_to_remove = [row.query_hash for row in oldest_entries]
            
            if hashes_to_remove:
                result = await self.session.execute(
                    delete(QueryCacheDB).where(QueryCacheDB.query_hash.in_(hashes_to_remove))
                )
                
                deleted_count = result.rowcount
                await self.flush()
                
                logger.info(f"Removed {deleted_count} oldest cache entries to maintain size limit")
                return deleted_count
            
            return 0
        except SQLAlchemyError as e:
            logger.error(f"Failed to cleanup cache by size limit: {e}")
            await self.rollback()
            raise RepositoryError(f"Failed to cleanup cache by size limit: {e}") from e
    
    # Cache Analytics and Statistics
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics and analytics.
        
        Returns:
            Dictionary with cache statistics
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            current_time = datetime.utcnow()
            
            # Get overall cache statistics
            result = await self.session.execute(
                select(
                    func.count(QueryCacheDB.query_hash).label('total_entries'),
                    func.count().filter(QueryCacheDB.expires_at > current_time).label('active_entries'),
                    func.count().filter(QueryCacheDB.expires_at <= current_time).label('expired_entries'),
                    func.min(QueryCacheDB.cached_at).label('oldest_entry'),
                    func.max(QueryCacheDB.cached_at).label('newest_entry'),
                    func.avg(
                        func.extract('epoch', QueryCacheDB.expires_at - QueryCacheDB.cached_at)
                    ).label('avg_ttl_seconds')
                )
            )
            
            row = result.first()
            
            total_entries = row.total_entries or 0
            active_entries = row.active_entries or 0
            expired_entries = row.expired_entries or 0
            
            statistics = {
                'total_entries': total_entries,
                'active_entries': active_entries,
                'expired_entries': expired_entries,
                'hit_rate_potential': (active_entries / total_entries * 100) if total_entries > 0 else 0,
                'oldest_entry': row.oldest_entry.isoformat() if row.oldest_entry else None,
                'newest_entry': row.newest_entry.isoformat() if row.newest_entry else None,
                'average_ttl_seconds': float(row.avg_ttl_seconds or 0)
            }
            
            logger.debug(f"Generated cache statistics: {statistics}")
            return statistics
        except SQLAlchemyError as e:
            logger.error(f"Failed to get cache statistics: {e}")
            raise RepositoryError(f"Failed to get cache statistics: {e}") from e
    
    async def get_cache_size_info(self) -> Dict[str, Any]:
        """
        Get information about cache storage size.
        
        Returns:
            Dictionary with cache size information
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            # Note: This is a PostgreSQL-specific query for getting storage size
            # For other databases, this might need to be adapted
            result = await self.session.execute(
                text("""
                    SELECT 
                        COUNT(*) as entry_count,
                        pg_size_pretty(pg_total_relation_size('query_cache')) as table_size,
                        pg_total_relation_size('query_cache') as table_size_bytes
                    FROM query_cache
                """)
            )
            
            row = result.first()
            
            size_info = {
                'entry_count': row.entry_count if row else 0,
                'table_size_human': row.table_size if row else 'Unknown',
                'table_size_bytes': row.table_size_bytes if row else 0
            }
            
            logger.debug(f"Generated cache size info: {size_info}")
            return size_info
        except SQLAlchemyError as e:
            logger.warning(f"Failed to get cache size info (may not be PostgreSQL): {e}")
            # Fallback to basic count
            try:
                count_result = await self.session.execute(
                    select(func.count(QueryCacheDB.query_hash))
                )
                return {
                    'entry_count': count_result.scalar() or 0,
                    'table_size_human': 'Unknown',
                    'table_size_bytes': 0
                }
            except SQLAlchemyError as fallback_error:
                logger.error(f"Failed to get basic cache count: {fallback_error}")
                raise RepositoryError(f"Failed to get cache size info: {fallback_error}") from fallback_error
    
    async def get_cache_expiry_distribution(self) -> Dict[str, Any]:
        """
        Get distribution of cache entries by expiry time ranges.
        
        Returns:
            Dictionary with expiry distribution
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            current_time = datetime.utcnow()
            
            # Define time ranges
            ranges = [
                ('expired', current_time - timedelta(days=365), current_time),
                ('expires_1h', current_time, current_time + timedelta(hours=1)),
                ('expires_24h', current_time + timedelta(hours=1), current_time + timedelta(hours=24)),
                ('expires_7d', current_time + timedelta(hours=24), current_time + timedelta(days=7)),
                ('expires_later', current_time + timedelta(days=7), current_time + timedelta(days=365))
            ]
            
            distribution = {}
            
            for range_name, start_time, end_time in ranges:
                result = await self.session.execute(
                    select(func.count(QueryCacheDB.query_hash))
                    .where(
                        and_(
                            QueryCacheDB.expires_at > start_time,
                            QueryCacheDB.expires_at <= end_time
                        )
                    )
                )
                
                count = result.scalar() or 0
                distribution[range_name] = count
            
            logger.debug(f"Generated cache expiry distribution: {distribution}")
            return {
                'distribution': distribution,
                'total_entries': sum(distribution.values())
            }
        except SQLAlchemyError as e:
            logger.error(f"Failed to get cache expiry distribution: {e}")
            raise RepositoryError(f"Failed to get cache expiry distribution: {e}") from e
    
    # Advanced Cache Operations
    
    async def get_recently_cached_entries(
        self,
        hours: int = 24,
        limit: Optional[int] = None
    ) -> List[QueryCacheDB]:
        """
        Get recently cached entries.
        
        Args:
            hours: Number of hours to look back (default: 24)
            limit: Maximum number of entries to return
            
        Returns:
            List of recently cached entries
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            query = select(QueryCacheDB).where(
                QueryCacheDB.cached_at >= cutoff_time
            ).order_by(desc(QueryCacheDB.cached_at))
            
            if limit:
                query = query.limit(limit)
            
            result = await self.session.execute(query)
            entries = result.scalars().all()
            
            logger.debug(f"Retrieved {len(entries)} recently cached entries from last {hours} hours")
            return list(entries)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get recently cached entries: {e}")
            raise RepositoryError(f"Failed to get recently cached entries: {e}") from e
    
    async def extend_cache_expiry(
        self,
        query_hash: str,
        additional_seconds: int
    ) -> Optional[QueryCacheDB]:
        """
        Extend the expiry time of a cache entry.
        
        Args:
            query_hash: The query hash to extend
            additional_seconds: Number of seconds to add to expiry time
            
        Returns:
            Updated cache entry if found, None otherwise
            
        Raises:
            RepositoryError: If update fails
        """
        try:
            # Get current entry
            current_entry = await self.get_cached_result(query_hash)
            if not current_entry:
                logger.debug(f"No cache entry found to extend for hash {query_hash}")
                return None
            
            # Calculate new expiry time
            new_expiry = current_entry.expires_at + timedelta(seconds=additional_seconds)
            
            # Update the entry
            updated_entry = await self.update_by_id(
                query_hash,
                expires_at=new_expiry
            )
            
            if updated_entry:
                logger.debug(f"Extended cache expiry for hash {query_hash} by {additional_seconds} seconds")
            
            return updated_entry
        except Exception as e:
            logger.error(f"Failed to extend cache expiry for hash {query_hash}: {e}")
            raise
    
    async def batch_invalidate_cache(self, query_hashes: List[str]) -> int:
        """
        Invalidate multiple cache entries in batch.
        
        Args:
            query_hashes: List of query hashes to invalidate
            
        Returns:
            Number of entries invalidated
            
        Raises:
            RepositoryError: If batch invalidation fails
        """
        try:
            if not query_hashes:
                return 0
            
            result = await self.session.execute(
                delete(QueryCacheDB).where(QueryCacheDB.query_hash.in_(query_hashes))
            )
            
            deleted_count = result.rowcount
            await self.flush()
            
            logger.info(f"Batch invalidated {deleted_count} cache entries")
            return deleted_count
        except SQLAlchemyError as e:
            logger.error(f"Failed to batch invalidate cache entries: {e}")
            await self.rollback()
            raise RepositoryError(f"Failed to batch invalidate cache entries: {e}") from e