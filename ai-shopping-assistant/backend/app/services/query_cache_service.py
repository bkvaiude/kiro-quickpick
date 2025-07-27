import hashlib
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.config import settings
from app.database.manager import database_manager
from app.database.repositories.cache_repository import CacheRepository
from app.database.models import QueryCacheDB
import logging

logger = logging.getLogger(__name__)


class QueryCacheService:
    """Service for managing server-side query caching with PostgreSQL persistence"""
    
    def __init__(self):
        # Statistics tracking (in-memory for performance)
        self._cache_hits = 0
        self._cache_misses = 0
    
    def generate_query_hash(self, query: str, conversation_context: Optional[str] = None) -> str:
        """
        Generate a consistent hash for a query string and optional conversation context.
        
        Args:
            query: The user's query string
            conversation_context: Optional conversation context
            
        Returns:
            A consistent hash string for the query
        """
        # Create a consistent representation of the query data
        # Normalize context: empty/whitespace strings should be treated as None
        normalized_context = None
        if conversation_context and conversation_context.strip():
            normalized_context = conversation_context.strip()
        
        query_data = {
            "query": query.strip().lower(),  # Normalize query
            "context": normalized_context
        }
        
        # Convert to JSON with sorted keys for consistency
        query_json = json.dumps(query_data, sort_keys=True, ensure_ascii=True)
        
        # Generate SHA-256 hash
        hash_object = hashlib.sha256(query_json.encode('utf-8'))
        return hash_object.hexdigest()
    

    
    async def get_cache_size_info(self) -> Dict[str, Any]:
        """
        Get detailed cache size information.
        
        Returns:
            Dictionary with cache size information
        """
        try:
            session = await database_manager.get_session()
            try:
                cache_repo = CacheRepository(session)
                size_info = await cache_repo.get_cache_size_info()
                return size_info
            finally:
                await session.close()
        except Exception as e:
            logger.error(f"Error getting cache size info: {e}")
            return {
                'entry_count': 0,
                'table_size_human': 'Unknown',
                'table_size_bytes': 0,
                'error': str(e)
            }
    
    async def get_cache_expiry_distribution(self) -> Dict[str, Any]:
        """
        Get distribution of cache entries by expiry time ranges.
        
        Returns:
            Dictionary with expiry distribution
        """
        try:
            session = await database_manager.get_session()
            try:
                cache_repo = CacheRepository(session)
                distribution = await cache_repo.get_cache_expiry_distribution()
                return distribution
            finally:
                await session.close()
        except Exception as e:
            logger.error(f"Error getting cache expiry distribution: {e}")
            return {
                'distribution': {},
                'total_entries': 0,
                'error': str(e)
            }
    
    async def cleanup_old_cache(self, days: int = 7) -> int:
        """
        Remove cache entries older than specified days.
        
        Args:
            days: Number of days to keep cache entries (default: 7)
            
        Returns:
            Number of old entries removed
        """
        try:
            session = await database_manager.get_session()
            try:
                cache_repo = CacheRepository(session)
                deleted_count = await cache_repo.cleanup_old_cache(days)
                await session.commit()
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} cache entries older than {days} days")
                
                return deleted_count
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()
        except Exception as e:
            logger.error(f"Error cleaning up old cache: {e}")
            return 0
    
    async def cleanup_cache_by_size_limit(self, max_entries: int) -> int:
        """
        Remove oldest cache entries to stay within size limit.
        
        Args:
            max_entries: Maximum number of cache entries to keep
            
        Returns:
            Number of entries removed
        """
        try:
            session = await database_manager.get_session()
            try:
                cache_repo = CacheRepository(session)
                deleted_count = await cache_repo.cleanup_cache_by_size_limit(max_entries)
                await session.commit()
                
                if deleted_count > 0:
                    logger.info(f"Removed {deleted_count} oldest cache entries to maintain size limit")
                
                return deleted_count
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()
        except Exception as e:
            logger.error(f"Error cleaning up cache by size limit: {e}")
            return 0
    
    # Backward compatibility methods for existing tests
    # These methods maintain the original synchronous interface
    
    def get_cached_result(self, query_hash: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached result if it exists and hasn't expired.
        Maintains backward compatibility with synchronous interface.
        
        Args:
            query_hash: The hash of the query
            
        Returns:
            Cached result if valid, None otherwise
        """
        import asyncio
        try:
            # Try to use existing event loop or create a new one
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, create a task
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self._get_cached_result_async(query_hash))
                        return future.result(timeout=10)  # 10 second timeout
                else:
                    return loop.run_until_complete(self._get_cached_result_async(query_hash))
            except RuntimeError:
                # No event loop, create one
                return asyncio.run(self._get_cached_result_async(query_hash))
        except Exception as e:
            logger.error(f"Error in cache access: {e}")
            self._cache_misses += 1
            return None
    
    async def _get_cached_result_async(self, query_hash: str) -> Optional[Dict[str, Any]]:
        """Internal async method for getting cached results."""
        try:
            session = await database_manager.get_session()
            try:
                cache_repo = CacheRepository(session)
                cached_entry = await cache_repo.get_cached_result(query_hash)
                
                if cached_entry:
                    self._cache_hits += 1
                    logger.debug(f"Cache hit for query hash: {query_hash}")
                    return cached_entry.result
                else:
                    self._cache_misses += 1
                    logger.debug(f"Cache miss for query hash: {query_hash}")
                    return None
            finally:
                await session.close()
        except Exception as e:
            logger.error(f"Error retrieving cached result for hash {query_hash}: {e}")
            self._cache_misses += 1
            return None
    
    def cache_result(self, query_hash: str, result: Dict[str, Any]) -> None:
        """
        Store a query result in the cache with TTL.
        Maintains backward compatibility with synchronous interface.
        
        Args:
            query_hash: The hash of the query
            result: The result to cache
        """
        import asyncio
        try:
            # Try to use existing event loop or create a new one
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, create a task
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self._cache_result_async(query_hash, result))
                        future.result(timeout=10)  # 10 second timeout
                else:
                    loop.run_until_complete(self._cache_result_async(query_hash, result))
            except RuntimeError:
                # No event loop, create one
                asyncio.run(self._cache_result_async(query_hash, result))
        except Exception as e:
            logger.error(f"Error in cache write: {e}")
    
    async def _cache_result_async(self, query_hash: str, result: Dict[str, Any]) -> None:
        """Internal async method for caching results."""
        try:
            current_time = datetime.utcnow()
            expires_at = current_time + timedelta(minutes=settings.credit_system.cache_validity_minutes)
            
            cache_entry = QueryCacheDB(
                query_hash=query_hash,
                result=result,
                cached_at=current_time,
                expires_at=expires_at
            )
            
            session = await database_manager.get_session()
            try:
                cache_repo = CacheRepository(session)
                await cache_repo.cache_result(cache_entry)
                await session.commit()
                
                logger.debug(f"Cached result for query hash: {query_hash}, expires at: {expires_at}")
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()
        except Exception as e:
            logger.error(f"Error caching result for hash {query_hash}: {e}")
            raise
    
    def clear_expired_cache(self) -> int:
        """
        Remove all expired cache entries.
        Maintains backward compatibility with synchronous interface.
        
        Returns:
            Number of entries removed
        """
        import asyncio
        try:
            # Try to use existing event loop or create a new one
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, create a task
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self._clear_expired_cache_async())
                        return future.result(timeout=10)  # 10 second timeout
                else:
                    return loop.run_until_complete(self._clear_expired_cache_async())
            except RuntimeError:
                # No event loop, create one
                return asyncio.run(self._clear_expired_cache_async())
        except Exception as e:
            logger.error(f"Error in cache cleanup: {e}")
            return 0
    
    async def _clear_expired_cache_async(self) -> int:
        """Internal async method for clearing expired cache."""
        try:
            session = await database_manager.get_session()
            try:
                cache_repo = CacheRepository(session)
                deleted_count = await cache_repo.cleanup_expired_cache()
                await session.commit()
                
                if deleted_count > 0:
                    logger.info(f"Cleared {deleted_count} expired cache entries")
                
                return deleted_count
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()
        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics including database statistics.
        Maintains backward compatibility with synchronous interface.
        
        Returns:
            Dictionary with cache statistics
        """
        import asyncio
        try:
            # Try to use existing event loop or create a new one
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, create a task
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self._get_cache_stats_async())
                        return future.result(timeout=10)  # 10 second timeout
                else:
                    return loop.run_until_complete(self._get_cache_stats_async())
            except RuntimeError:
                # No event loop, create one
                return asyncio.run(self._get_cache_stats_async())
        except Exception as e:
            logger.error(f"Error getting cache statistics: {e}")
            # Return basic fallback stats
            total_requests = self._cache_hits + self._cache_misses
            hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
            return {
                'cache_hits': self._cache_hits,
                'cache_misses': self._cache_misses,
                'hit_rate_percent': round(hit_rate, 2),
                'total_requests': total_requests,
                'cache_size': 0,
                'active_entries': 0,
                'expired_entries': 0,
                'error': str(e)
            }
    
    async def _get_cache_stats_async(self) -> Dict[str, Any]:
        """Internal async method for getting cache statistics."""
        try:
            session = await database_manager.get_session()
            try:
                cache_repo = CacheRepository(session)
                db_stats = await cache_repo.get_cache_statistics()
                
                # Combine in-memory statistics with database statistics
                total_requests = self._cache_hits + self._cache_misses
                hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
                
                return {
                    # In-memory statistics (session-based)
                    'cache_hits': self._cache_hits,
                    'cache_misses': self._cache_misses,
                    'hit_rate_percent': round(hit_rate, 2),
                    'total_requests': total_requests,
                    
                    # Database statistics (persistent)
                    'cache_size': db_stats.get('total_entries', 0),
                    'active_entries': db_stats.get('active_entries', 0),
                    'expired_entries': db_stats.get('expired_entries', 0),
                    'oldest_entry': db_stats.get('oldest_entry'),
                    'newest_entry': db_stats.get('newest_entry'),
                    'average_ttl_seconds': db_stats.get('average_ttl_seconds', 0)
                }
            finally:
                await session.close()
        except Exception as e:
            logger.error(f"Error getting cache statistics: {e}")
            # Fallback to basic in-memory stats
            total_requests = self._cache_hits + self._cache_misses
            hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'cache_hits': self._cache_hits,
                'cache_misses': self._cache_misses,
                'hit_rate_percent': round(hit_rate, 2),
                'total_requests': total_requests,
                'cache_size': 0,
                'active_entries': 0,
                'expired_entries': 0,
                'error': str(e)
            }
    
    def clear_cache(self) -> None:
        """
        Clear all cache entries.
        Maintains backward compatibility with synchronous interface.
        """
        import asyncio
        try:
            # Try to use existing event loop or create a new one
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, create a task
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self._clear_cache_async())
                        future.result(timeout=10)  # 10 second timeout
                else:
                    loop.run_until_complete(self._clear_cache_async())
            except RuntimeError:
                # No event loop, create one
                asyncio.run(self._clear_cache_async())
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            # Reset in-memory stats as fallback
            self._cache_hits = 0
            self._cache_misses = 0
    
    async def _clear_cache_async(self) -> None:
        """Internal async method for clearing cache."""
        try:
            session = await database_manager.get_session()
            try:
                cache_repo = CacheRepository(session)
                deleted_count = await cache_repo.clear_cache()
                await session.commit()
                
                # Reset in-memory statistics
                self._cache_hits = 0
                self._cache_misses = 0
                
                logger.info(f"Cache cleared: {deleted_count} entries removed")
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            raise


# Create singleton instance
query_cache_service = QueryCacheService()