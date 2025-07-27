"""Comprehensive end-to-end tests for PostgreSQL performance and functionality."""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database.manager import database_manager, get_db_session
from app.database.models import UserCreditsDB, CreditTransactionDB, UserConsentDB, QueryCacheDB
from app.database.repositories.credit_repository import CreditRepository
from app.database.repositories.consent_repository import ConsentRepository
from app.database.repositories.cache_repository import CacheRepository
from app.database.batch_operations import (
    CreditBatchOperations, CacheBatchOperations, ConsentBatchOperations
)
from app.database.performance import run_performance_analysis, performance_monitor
from app.services.credit_service import CreditService
from app.services.user_consent_service import UserConsentService
from app.services.query_cache_service import QueryCacheService

# Configure pytest for async tests
pytest_plugins = ('pytest_asyncio',)


@pytest.mark.asyncio
class TestPostgreSQLPerformance:
    """Test PostgreSQL performance and optimization features."""
    
    @pytest.fixture(autouse=True)
    async def setup_database(self):
        """Set up database for testing."""
        await database_manager.initialize()
        yield
        # Cleanup is handled by pytest fixtures
    
    @pytest.fixture
    async def db_session(self):
        """Get database session for testing."""
        session = await database_manager.get_session()
        try:
            yield session
        finally:
            await session.close()
    
    async def test_database_connection_performance(self, db_session: AsyncSession):
        """Test database connection performance and pool efficiency."""
        # Test multiple concurrent connections
        start_time = time.time()
        
        async def test_connection():
            result = await db_session.execute(text("SELECT 1"))
            return result.scalar()
        
        # Test concurrent connections
        tasks = [test_connection() for _ in range(20)]
        results = await asyncio.gather(*tasks)
        
        connection_time = time.time() - start_time
        
        # All connections should succeed
        assert all(result == 1 for result in results)
        
        # Connection time should be reasonable (less than 2 seconds for 20 connections)
        assert connection_time < 2.0, f"Connection time too slow: {connection_time}s"
        
        # Check connection pool info
        pool_info = await database_manager.get_connection_info()
        assert pool_info["status"] == "initialized"
        print(f"Connection pool info: {pool_info}")
    
    async def test_index_performance(self, db_session: AsyncSession):
        """Test that indexes are being used effectively."""
        # Create test data
        credit_repo = CreditRepository(db_session)
        
        # Create multiple users with credits
        test_users = []
        for i in range(100):
            user_id = f"test_user_{i}"
            user_credits = UserCreditsDB(
                user_id=user_id,
                is_guest=i % 2 == 0,
                available_credits=i % 10,
                max_credits=10,
                last_reset_timestamp=datetime.utcnow() - timedelta(hours=i % 24)
            )
            await credit_repo.create_user_credits(user_credits)
            test_users.append(user_id)
        
        await db_session.commit()
        
        # Test query performance with indexes
        start_time = time.time()
        
        # Query that should use user_id index
        user_credits = await credit_repo.get_user_credits("test_user_50")
        assert user_credits is not None
        
        # Query that should use composite index
        guest_users = await db_session.execute(
            text("SELECT COUNT(*) FROM user_credits WHERE is_guest = true")
        )
        guest_count = guest_users.scalar()
        assert guest_count > 0
        
        query_time = time.time() - start_time
        
        # Queries should be fast with proper indexes
        assert query_time < 0.1, f"Query time too slow: {query_time}s"
        
        # Cleanup
        for user_id in test_users:
            await credit_repo.delete_user_credits(user_id)
        await db_session.commit()
    
    async def test_batch_operations_performance(self, db_session: AsyncSession):
        """Test batch operations performance."""
        batch_ops = CreditBatchOperations(db_session)
        
        # Test batch credit reset
        user_ids = [f"batch_user_{i}" for i in range(50)]
        
        # Create users first
        credit_repo = CreditRepository(db_session)
        for user_id in user_ids:
            user_credits = UserCreditsDB(
                user_id=user_id,
                is_guest=False,
                available_credits=5,
                max_credits=10,
                last_reset_timestamp=datetime.utcnow() - timedelta(hours=25)
            )
            await credit_repo.create_user_credits(user_credits)
        
        await db_session.commit()
        
        # Test batch reset performance
        start_time = time.time()
        reset_count = await batch_ops.batch_reset_credits(user_ids, datetime.utcnow())
        batch_time = time.time() - start_time
        
        assert reset_count == len(user_ids)
        assert batch_time < 1.0, f"Batch operation too slow: {batch_time}s"
        
        # Verify credits were reset
        for user_id in user_ids:
            user_credits = await credit_repo.get_user_credits(user_id)
            assert user_credits.available_credits == 10
        
        # Cleanup
        for user_id in user_ids:
            await credit_repo.delete_user_credits(user_id)
        await db_session.commit()
    
    async def test_cache_performance(self, db_session: AsyncSession):
        """Test query cache performance."""
        cache_repo = CacheRepository(db_session)
        cache_ops = CacheBatchOperations(db_session)
        
        # Create test cache entries
        cache_entries = []
        for i in range(100):
            cache_entry = {
                'query_hash': f'test_hash_{i}',
                'result': {'test': f'result_{i}', 'data': list(range(i))},
                'cached_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(hours=1)
            }
            cache_entries.append(cache_entry)
        
        # Test batch cache insertion performance
        start_time = time.time()
        cached_count = await cache_ops.batch_cache_results(cache_entries)
        cache_time = time.time() - start_time
        
        assert cached_count == len(cache_entries)
        assert cache_time < 2.0, f"Cache batch operation too slow: {cache_time}s"
        
        # Test cache retrieval performance
        start_time = time.time()
        
        # Test multiple cache lookups
        for i in range(0, 20, 2):  # Test every other entry
            cached_result = await cache_repo.get_cached_result(f'test_hash_{i}')
            assert cached_result is not None
            assert cached_result.result['test'] == f'result_{i}'
        
        lookup_time = time.time() - start_time
        assert lookup_time < 0.5, f"Cache lookup too slow: {lookup_time}s"
        
        # Test cache cleanup performance
        start_time = time.time()
        cleanup_count = await cache_ops.batch_cleanup_expired_cache()
        cleanup_time = time.time() - start_time
        
        # Should be fast even if no expired entries
        assert cleanup_time < 1.0, f"Cache cleanup too slow: {cleanup_time}s"
        
        # Cleanup
        await cache_repo.clear_cache()
        await db_session.commit()
    
    async def test_concurrent_operations(self, db_session: AsyncSession):
        """Test concurrent database operations."""
        credit_repo = CreditRepository(db_session)
        
        # Create a test user
        user_id = "concurrent_test_user"
        user_credits = UserCreditsDB(
            user_id=user_id,
            is_guest=False,
            available_credits=100,
            max_credits=100
        )
        await credit_repo.create_user_credits(user_credits)
        await db_session.commit()
        
        # Test concurrent credit deductions
        async def deduct_credit():
            async for session in get_db_session():
                repo = CreditRepository(session)
                user = await repo.get_user_credits(user_id)
                if user and user.available_credits > 0:
                    await repo.update_user_credits(
                        user_id, 
                        available_credits=user.available_credits - 1
                    )
                    await session.commit()
                    return True
                return False
        
        # Run concurrent deductions
        start_time = time.time()
        tasks = [deduct_credit() for _ in range(20)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        concurrent_time = time.time() - start_time
        
        # Check that operations completed reasonably fast
        assert concurrent_time < 5.0, f"Concurrent operations too slow: {concurrent_time}s"
        
        # Check final credit count
        final_user = await credit_repo.get_user_credits(user_id)
        successful_deductions = sum(1 for r in results if r is True)
        expected_credits = 100 - successful_deductions
        
        assert final_user.available_credits == expected_credits
        
        # Cleanup
        await credit_repo.delete_user_credits(user_id)
        await db_session.commit()
    
    async def test_performance_monitoring(self, db_session: AsyncSession):
        """Test performance monitoring functionality."""
        # Run some database operations to generate metrics
        credit_repo = CreditRepository(db_session)
        
        # Create test user
        user_id = "perf_test_user"
        user_credits = UserCreditsDB(
            user_id=user_id,
            is_guest=False,
            available_credits=10,
            max_credits=10
        )
        await credit_repo.create_user_credits(user_credits)
        
        # Perform various operations
        await credit_repo.get_user_credits(user_id)
        await credit_repo.update_user_credits(user_id, available_credits=5)
        
        # Create some transactions
        for i in range(5):
            transaction = CreditTransactionDB(
                user_id=user_id,
                transaction_type='deduct',
                amount=-1,
                description=f'Test transaction {i}'
            )
            await credit_repo.create_transaction(transaction)
        
        await db_session.commit()
        
        # Get performance summary
        perf_summary = await performance_monitor.get_performance_summary(hours=1)
        
        assert perf_summary['total_queries'] > 0
        assert perf_summary['avg_execution_time_ms'] >= 0
        assert 'by_query_type' in perf_summary
        
        # Get slowest queries
        slowest_queries = await performance_monitor.get_slowest_queries(limit=5)
        assert isinstance(slowest_queries, list)
        
        # Run performance analysis
        analysis = await run_performance_analysis(db_session)
        
        assert 'timestamp' in analysis
        assert 'performance_summary' in analysis
        assert 'recommendations' in analysis
        
        # Cleanup
        await credit_repo.delete_user_credits(user_id)
        await db_session.commit()


@pytest.mark.asyncio
class TestEndToEndFunctionality:
    """Test complete application functionality with PostgreSQL."""
    
    @pytest.fixture(autouse=True)
    async def setup_database(self):
        """Set up database for testing."""
        await database_manager.initialize()
        yield
    
    @pytest.fixture
    async def db_session(self):
        """Get database session for testing."""
        session = await database_manager.get_session()
        try:
            yield session
        finally:
            await session.close()
    
    async def test_credit_service_integration(self, db_session: AsyncSession):
        """Test CreditService with PostgreSQL backend."""
        credit_service = CreditService()
        
        # Test guest user credit management
        guest_user_id = "guest_123"
        
        # Initialize guest credits
        await credit_service.initialize_user_credits(guest_user_id, is_guest=True)
        
        # Check initial credits
        credits = await credit_service.get_user_credits(guest_user_id)
        assert credits['available_credits'] == 10  # Default guest credits
        assert credits['is_guest'] is True
        
        # Deduct credits
        success = await credit_service.deduct_credit(guest_user_id, "Test query")
        assert success is True
        
        # Check updated credits
        credits = await credit_service.get_user_credits(guest_user_id)
        assert credits['available_credits'] == 9
        
        # Test registered user
        reg_user_id = "registered_456"
        await credit_service.initialize_user_credits(reg_user_id, is_guest=False)
        
        credits = await credit_service.get_user_credits(reg_user_id)
        assert credits['available_credits'] == 50  # Default registered credits
        assert credits['is_guest'] is False
        
        # Test credit reset
        await credit_service.reset_daily_credits()
        
        # Check that credits were reset
        guest_credits = await credit_service.get_user_credits(guest_user_id)
        reg_credits = await credit_service.get_user_credits(reg_user_id)
        
        assert guest_credits['available_credits'] == 10
        assert reg_credits['available_credits'] == 50
    
    async def test_consent_service_integration(self, db_session: AsyncSession):
        """Test UserConsentService with PostgreSQL backend."""
        consent_service = UserConsentService()
        
        user_id = "consent_test_user"
        
        # Test consent creation
        await consent_service.record_user_consent(
            user_id=user_id,
            terms_accepted=True,
            marketing_consent=False
        )
        
        # Check consent
        consent = await consent_service.get_user_consent(user_id)
        assert consent is not None
        assert consent['terms_accepted'] is True
        assert consent['marketing_consent'] is False
        
        # Update consent
        await consent_service.update_user_consent(
            user_id=user_id,
            marketing_consent=True
        )
        
        # Check updated consent
        consent = await consent_service.get_user_consent(user_id)
        assert consent['marketing_consent'] is True
        
        # Test consent validation
        has_consent = await consent_service.has_valid_consent(user_id)
        assert has_consent is True
    
    async def test_cache_service_integration(self, db_session: AsyncSession):
        """Test QueryCacheService with PostgreSQL backend."""
        cache_service = QueryCacheService()
        
        query_hash = "test_query_hash_123"
        test_result = {
            "products": [
                {"name": "Test Product", "price": 100},
                {"name": "Another Product", "price": 200}
            ],
            "summary": "Test query results"
        }
        
        # Test caching
        await cache_service.cache_query_result(query_hash, test_result)
        
        # Test retrieval
        cached_result = await cache_service.get_cached_result(query_hash)
        assert cached_result is not None
        assert cached_result == test_result
        
        # Test cache miss
        missing_result = await cache_service.get_cached_result("nonexistent_hash")
        assert missing_result is None
        
        # Test cache invalidation
        await cache_service.invalidate_cache_entry(query_hash)
        invalidated_result = await cache_service.get_cached_result(query_hash)
        assert invalidated_result is None
    
    async def test_application_restart_persistence(self, db_session: AsyncSession):
        """Test that data persists across application restarts."""
        # Create test data
        credit_service = CreditService()
        consent_service = UserConsentService()
        cache_service = QueryCacheService()
        
        user_id = "persistence_test_user"
        
        # Create user data
        await credit_service.initialize_user_credits(user_id, is_guest=False)
        await credit_service.deduct_credit(user_id, "Test deduction")
        
        await consent_service.record_user_consent(
            user_id=user_id,
            terms_accepted=True,
            marketing_consent=True
        )
        
        query_hash = "persistence_test_hash"
        test_result = {"test": "persistence_data"}
        await cache_service.cache_query_result(query_hash, test_result)
        
        # Simulate application restart by closing and reinitializing database
        await database_manager.close()
        await database_manager.initialize()
        
        # Verify data persistence
        credits = await credit_service.get_user_credits(user_id)
        assert credits is not None
        assert credits['available_credits'] == 49  # 50 - 1 deduction
        
        consent = await consent_service.get_user_consent(user_id)
        assert consent is not None
        assert consent['terms_accepted'] is True
        assert consent['marketing_consent'] is True
        
        cached_result = await cache_service.get_cached_result(query_hash)
        assert cached_result == test_result
    
    async def test_error_recovery(self, db_session: AsyncSession):
        """Test error scenarios and recovery procedures."""
        credit_service = CreditService()
        
        # Test handling of non-existent user
        credits = await credit_service.get_user_credits("nonexistent_user")
        assert credits is None
        
        # Test deduction from non-existent user
        success = await credit_service.deduct_credit("nonexistent_user", "Test")
        assert success is False
        
        # Test database connection recovery
        health_check = await database_manager.health_check()
        assert health_check is True
        
        # Test transaction rollback on error
        user_id = "error_test_user"
        await credit_service.initialize_user_credits(user_id, is_guest=False)
        
        # Simulate error during transaction
        credit_repo = CreditRepository(db_session)
        try:
            # Start a transaction that will fail
            await credit_repo.update_user_credits(user_id, available_credits=-1)  # Should fail constraint
            await db_session.commit()
            assert False, "Should have failed due to constraint violation"
        except Exception:
            # Transaction should be rolled back
            await db_session.rollback()
        
        # Verify user credits are unchanged
        credits = await credit_service.get_user_credits(user_id)
        assert credits['available_credits'] == 50  # Original value
    
    async def test_performance_under_load(self, db_session: AsyncSession):
        """Test application performance under simulated load."""
        credit_service = CreditService()
        
        # Create multiple users
        user_count = 50
        user_ids = [f"load_test_user_{i}" for i in range(user_count)]
        
        # Initialize users concurrently
        start_time = time.time()
        
        async def init_user(user_id):
            await credit_service.initialize_user_credits(user_id, is_guest=False)
            return user_id
        
        tasks = [init_user(user_id) for user_id in user_ids]
        results = await asyncio.gather(*tasks)
        
        init_time = time.time() - start_time
        assert len(results) == user_count
        assert init_time < 10.0, f"User initialization too slow: {init_time}s"
        
        # Perform concurrent operations
        start_time = time.time()
        
        async def user_operations(user_id):
            # Get credits
            credits = await credit_service.get_user_credits(user_id)
            assert credits is not None
            
            # Deduct credit
            success = await credit_service.deduct_credit(user_id, "Load test")
            assert success is True
            
            # Get updated credits
            updated_credits = await credit_service.get_user_credits(user_id)
            assert updated_credits['available_credits'] == credits['available_credits'] - 1
            
            return user_id
        
        tasks = [user_operations(user_id) for user_id in user_ids]
        results = await asyncio.gather(*tasks)
        
        operations_time = time.time() - start_time
        assert len(results) == user_count
        assert operations_time < 15.0, f"Concurrent operations too slow: {operations_time}s"
        
        print(f"Load test completed: {user_count} users, {operations_time:.2f}s")


@pytest.mark.asyncio
class TestDatabaseMaintenance:
    """Test database maintenance and cleanup operations."""
    
    @pytest.fixture(autouse=True)
    async def setup_database(self):
        """Set up database for testing."""
        await database_manager.initialize()
        yield
    
    @pytest.fixture
    async def db_session(self):
        """Get database session for testing."""
        session = await database_manager.get_session()
        try:
            yield session
        finally:
            await session.close()
    
    async def test_transaction_cleanup(self, db_session: AsyncSession):
        """Test cleanup of old transaction records."""
        credit_repo = CreditRepository(db_session)
        
        # Create test user
        user_id = "cleanup_test_user"
        user_credits = UserCreditsDB(
            user_id=user_id,
            is_guest=False,
            available_credits=10,
            max_credits=10
        )
        await credit_repo.create_user_credits(user_credits)
        
        # Create old transactions
        old_timestamp = datetime.utcnow() - timedelta(days=100)
        for i in range(10):
            transaction = CreditTransactionDB(
                user_id=user_id,
                transaction_type='deduct',
                amount=-1,
                timestamp=old_timestamp,
                description=f'Old transaction {i}'
            )
            await credit_repo.create_transaction(transaction)
        
        # Create recent transactions
        for i in range(5):
            transaction = CreditTransactionDB(
                user_id=user_id,
                transaction_type='deduct',
                amount=-1,
                description=f'Recent transaction {i}'
            )
            await credit_repo.create_transaction(transaction)
        
        await db_session.commit()
        
        # Verify all transactions exist
        all_transactions = await credit_repo.get_user_transactions(user_id)
        assert len(all_transactions) == 15
        
        # Run cleanup
        deleted_count = await credit_repo.cleanup_old_transactions(days=90)
        await db_session.commit()
        
        assert deleted_count == 10
        
        # Verify only recent transactions remain
        remaining_transactions = await credit_repo.get_user_transactions(user_id)
        assert len(remaining_transactions) == 5
        
        # Cleanup
        await credit_repo.delete_user_credits(user_id)
        await db_session.commit()
    
    async def test_cache_cleanup(self, db_session: AsyncSession):
        """Test cleanup of expired cache entries."""
        cache_repo = CacheRepository(db_session)
        
        # Create expired cache entries
        expired_time = datetime.utcnow() - timedelta(hours=1)
        for i in range(10):
            cache_entry = QueryCacheDB(
                query_hash=f'expired_hash_{i}',
                result={'test': f'expired_result_{i}'},
                cached_at=expired_time - timedelta(hours=1),
                expires_at=expired_time
            )
            await cache_repo.cache_result(cache_entry)
        
        # Create active cache entries
        future_time = datetime.utcnow() + timedelta(hours=1)
        for i in range(5):
            cache_entry = QueryCacheDB(
                query_hash=f'active_hash_{i}',
                result={'test': f'active_result_{i}'},
                cached_at=datetime.utcnow(),
                expires_at=future_time
            )
            await cache_repo.cache_result(cache_entry)
        
        await db_session.commit()
        
        # Run cleanup
        deleted_count = await cache_repo.cleanup_expired_cache()
        await db_session.commit()
        
        assert deleted_count == 10
        
        # Verify only active entries remain
        stats = await cache_repo.get_cache_statistics()
        assert stats['active_entries'] == 5
        assert stats['expired_entries'] == 0
        
        # Cleanup
        await cache_repo.clear_cache()
        await db_session.commit()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])