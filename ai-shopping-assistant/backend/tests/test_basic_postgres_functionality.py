"""Basic PostgreSQL functionality tests."""

import pytest
import asyncio
from datetime import datetime, timedelta

from app.database.manager import database_manager
from app.database.models import UserCreditsDB, CreditTransactionDB, UserConsentDB, QueryCacheDB
from app.database.repositories.credit_repository import CreditRepository
from app.database.repositories.consent_repository import ConsentRepository
from app.database.repositories.cache_repository import CacheRepository


@pytest.mark.asyncio
async def test_database_initialization():
    """Test that database initializes correctly."""
    await database_manager.initialize()
    
    # Test health check
    health_check = await database_manager.health_check()
    assert health_check is True
    
    # Test connection info
    conn_info = await database_manager.get_connection_info()
    assert conn_info["status"] == "initialized"


@pytest.mark.asyncio
async def test_credit_repository_basic_operations():
    """Test basic credit repository operations."""
    await database_manager.initialize()
    session = await database_manager.get_session()
    
    try:
        credit_repo = CreditRepository(session)
        
        # Test user creation
        user_id = "test_user_123"
        user_credits = UserCreditsDB(
            user_id=user_id,
            is_guest=False,
            available_credits=50,
            max_credits=50
        )
        
        created_user = await credit_repo.create_user_credits(user_credits)
        assert created_user.user_id == user_id
        assert created_user.available_credits == 50
        
        # Test user retrieval
        retrieved_user = await credit_repo.get_user_credits(user_id)
        assert retrieved_user is not None
        assert retrieved_user.user_id == user_id
        
        # Test user update
        updated_user = await credit_repo.update_user_credits(
            user_id, 
            available_credits=45
        )
        assert updated_user.available_credits == 45
        
        # Test transaction creation
        transaction = CreditTransactionDB(
            user_id=user_id,
            transaction_type='deduct',
            amount=-5,
            description='Test deduction'
        )
        
        created_transaction = await credit_repo.create_transaction(transaction)
        assert created_transaction.user_id == user_id
        assert created_transaction.amount == -5
        
        # Test transaction retrieval
        transactions = await credit_repo.get_user_transactions(user_id)
        assert len(transactions) == 1
        assert transactions[0].amount == -5
        
        # Test cleanup
        deleted = await credit_repo.delete_user_credits(user_id)
        assert deleted is True
        
        await session.commit()
        
    finally:
        await session.close()


@pytest.mark.asyncio
async def test_consent_repository_basic_operations():
    """Test basic consent repository operations."""
    await database_manager.initialize()
    session = await database_manager.get_session()
    
    try:
        consent_repo = ConsentRepository(session)
        
        # Test consent creation
        user_id = "consent_test_user"
        user_consent = UserConsentDB(
            user_id=user_id,
            terms_accepted=True,
            marketing_consent=False
        )
        
        created_consent = await consent_repo.create_consent(user_consent)
        assert created_consent.user_id == user_id
        assert created_consent.terms_accepted is True
        assert created_consent.marketing_consent is False
        
        # Test consent retrieval
        retrieved_consent = await consent_repo.get_consent(user_id)
        assert retrieved_consent is not None
        assert retrieved_consent.terms_accepted is True
        
        # Test consent update
        updated_consent = await consent_repo.update_consent(
            user_id,
            marketing_consent=True
        )
        assert updated_consent.marketing_consent is True
        
        # Test cleanup
        deleted = await consent_repo.delete_consent(user_id)
        assert deleted is True
        
        await session.commit()
        
    finally:
        await session.close()


@pytest.mark.asyncio
async def test_cache_repository_basic_operations():
    """Test basic cache repository operations."""
    await database_manager.initialize()
    session = await database_manager.get_session()
    
    try:
        cache_repo = CacheRepository(session)
        
        # Test cache creation
        query_hash = "test_query_hash"
        cache_entry = QueryCacheDB(
            query_hash=query_hash,
            result={"test": "data", "products": [1, 2, 3]},
            cached_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        cached_result = await cache_repo.cache_result(cache_entry)
        assert cached_result.query_hash == query_hash
        
        # Test cache retrieval
        retrieved_cache = await cache_repo.get_cached_result(query_hash)
        assert retrieved_cache is not None
        assert retrieved_cache.result["test"] == "data"
        
        # Test cache invalidation
        invalidated = await cache_repo.invalidate_cache_entry(query_hash)
        assert invalidated is True
        
        # Verify cache is gone
        missing_cache = await cache_repo.get_cached_result(query_hash)
        assert missing_cache is None
        
        await session.commit()
        
    finally:
        await session.close()


@pytest.mark.asyncio
async def test_performance_indexes():
    """Test that performance indexes are working."""
    await database_manager.initialize()
    session = await database_manager.get_session()
    
    try:
        # Test that we can query index information
        result = await session.execute("""
            SELECT indexname, tablename 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND tablename IN ('user_credits', 'credit_transactions', 'user_consents', 'query_cache')
            ORDER BY tablename, indexname
        """)
        
        indexes = result.fetchall()
        
        # Should have multiple indexes
        assert len(indexes) > 10
        
        # Check for some specific performance indexes we created
        index_names = [idx.indexname for idx in indexes]
        
        # Check for composite indexes
        assert 'idx_credit_transactions_user_timestamp_desc' in index_names
        assert 'idx_user_credits_reset_lookup' in index_names
        assert 'idx_query_cache_cleanup' in index_names
        
        print(f"Found {len(indexes)} indexes:")
        for idx in indexes:
            print(f"  {idx.tablename}.{idx.indexname}")
        
        await session.commit()
        
    finally:
        await session.close()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])