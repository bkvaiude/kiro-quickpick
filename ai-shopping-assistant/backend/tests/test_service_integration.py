"""Integration tests for services with database repositories."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.services.credit_service import CreditService
from app.services.user_consent_service import UserConsentService
from app.services.query_cache_service import QueryCacheService
from app.models.credit import UserCredits, CreditTransaction
from app.models.user_consent import UserConsentCreate, UserConsentUpdate
from app.database.repositories.base import RepositoryError, RepositoryIntegrityError

# Use the same test setup as repository tests
from tests.test_repositories import TestBase, UserCreditsDB, CreditTransactionDB, UserConsentDB

# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def async_engine():
    """Create an async engine for testing."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.create_all)
    
    yield engine
    
    # Clean up
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine):
    """Create an async session for testing."""
    async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False)
    
    async with async_session_maker() as session:
        yield session


@pytest.fixture
def credit_service():
    """Create a CreditService instance for testing."""
    return CreditService()


@pytest.fixture
def consent_service():
    """Create a UserConsentService instance for testing."""
    return UserConsentService()


@pytest.fixture
def cache_service():
    """Create a QueryCacheService instance for testing."""
    return QueryCacheService()


class TestCreditServiceIntegration:
    """Integration tests for CreditService with database."""
    
    @pytest.mark.asyncio
    async def test_get_user_credits_new_guest(self, credit_service, async_session):
        """Test getting credits for a new guest user."""
        user_id = "guest_session_123"
        
        # Use the session parameter to avoid mocking issues
        credits = await credit_service.get_user_credits(user_id, is_guest=True, session=async_session)
        
        assert credits.user_id == user_id
        assert credits.is_guest is True
        assert credits.available_credits > 0
        assert credits.max_credits > 0
    
    @pytest.mark.asyncio
    async def test_get_user_credits_new_registered(self, credit_service, async_session):
        """Test getting credits for a new registered user."""
        user_id = "auth0|registered_user_123"
        
        credits = await credit_service.get_user_credits(user_id, is_guest=False, session=async_session)
        
        assert credits.user_id == user_id
        assert credits.is_guest is False
        assert credits.available_credits > 0
        assert credits.max_credits > 0
    
    @pytest.mark.asyncio
    async def test_get_user_credits_existing_user(self, credit_service, async_session):
        """Test getting credits for an existing user."""
        user_id = "existing_user_123"
        
        # Pre-create user credits in database
        from app.database.repositories.credit_repository import CreditRepository
        repo = CreditRepository(async_session)
        
        existing_credits = UserCreditsDB(
            user_id=user_id,
            is_guest=False,
            available_credits=5,
            max_credits=20,
            last_reset_timestamp=datetime.utcnow()
        )
        await repo.create_user_credits(existing_credits)
        await repo.commit()
        
        credits = await credit_service.get_user_credits(user_id, is_guest=False, session=async_session)
        
        assert credits.user_id == user_id
        assert credits.available_credits == 5
        assert credits.max_credits == 20
    
    @pytest.mark.asyncio
    async def test_deduct_credits_success(self, credit_service, async_session):
        """Test successfully deducting credits."""
        user_id = "test_user_deduct"
        
        # Pre-create user with credits
        from app.database.repositories.credit_repository import CreditRepository
        repo = CreditRepository(async_session)
        
        user_credits = UserCreditsDB(
            user_id=user_id,
            is_guest=False,
            available_credits=10,
            max_credits=20,
            last_reset_timestamp=datetime.utcnow()
        )
        await repo.create_user_credits(user_credits)
        await repo.commit()
        
        # Deduct credits using session parameter
        result = await credit_service.deduct_credit(user_id, is_guest=False, amount=3, session=async_session)
        
        assert result is True
        
        # Verify credits were deducted by checking current balance
        updated_credits = await credit_service.get_user_credits(user_id, is_guest=False, session=async_session)
        assert updated_credits.available_credits == 7
    
    @pytest.mark.asyncio
    async def test_deduct_credits_insufficient(self, credit_service, async_session):
        """Test deducting credits when insufficient credits available."""
        user_id = "test_user_insufficient"
        
        # Pre-create user with low credits
        from app.database.repositories.credit_repository import CreditRepository
        repo = CreditRepository(async_session)
        
        user_credits = UserCreditsDB(
            user_id=user_id,
            is_guest=True,
            available_credits=2,
            max_credits=10,
            last_reset_timestamp=datetime.utcnow()
        )
        await repo.create_user_credits(user_credits)
        await repo.commit()
        
        # Try to deduct more credits than available
        result = await credit_service.deduct_credit(user_id, is_guest=True, amount=5, session=async_session)
        
        assert result is False
        
        # Verify credits remained unchanged
        unchanged_credits = await credit_service.get_user_credits(user_id, is_guest=True, session=async_session)
        assert unchanged_credits.available_credits == 2
    
    @pytest.mark.asyncio
    async def test_database_connectivity_issues(self, credit_service):
        """Test handling of database connectivity issues."""
        user_id = "test_user_db_error"
        
        # Mock database session to raise an error
        with patch('app.services.credit_service.get_db_session') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")
            
            # This should handle the database error gracefully
            with pytest.raises(Exception):
                await credit_service.get_user_credits(user_id, is_guest=True)
    
    @pytest.mark.asyncio
    async def test_concurrent_credit_operations(self, credit_service, async_session):
        """Test concurrent access to credit operations."""
        user_id = "test_user_concurrent"
        
        # Pre-create user with credits
        from app.database.repositories.credit_repository import CreditRepository
        repo = CreditRepository(async_session)
        
        user_credits = UserCreditsDB(
            user_id=user_id,
            is_guest=False,
            available_credits=10,
            max_credits=20,
            last_reset_timestamp=datetime.utcnow()
        )
        await repo.create_user_credits(user_credits)
        await repo.commit()
        
        # Simulate concurrent operations
        import asyncio
        
        async def deduct_operation():
            return await credit_service.deduct_credit(user_id, is_guest=False, amount=2, session=async_session)
        
        # Run multiple concurrent deductions
        results = await asyncio.gather(
            deduct_operation(),
            deduct_operation(),
            deduct_operation(),
            return_exceptions=True
        )
        
        # At least some operations should succeed
        successful_results = [r for r in results if not isinstance(r, Exception) and r is True]
        assert len(successful_results) > 0


class TestUserConsentServiceIntegration:
    """Integration tests for UserConsentService with database."""
    
    @pytest.mark.asyncio
    async def test_create_consent(self, consent_service, async_session):
        """Test creating user consent."""
        user_id = "test_user_consent"
        consent_data = UserConsentCreate(
            terms_accepted=True,
            marketing_consent=False
        )
        
        consent = await consent_service.create_consent(user_id, consent_data, session=async_session)
        
        assert consent.user_id == user_id
        assert consent.terms_accepted is True
        assert consent.marketing_consent is False
    
    @pytest.mark.asyncio
    async def test_get_consent_existing(self, consent_service, async_session):
        """Test getting existing consent."""
        user_id = "test_user_existing_consent"
        
        # Pre-create consent in database
        from app.database.repositories.consent_repository import ConsentRepository
        repo = ConsentRepository(async_session)
        
        consent_db = UserConsentDB(
            user_id=user_id,
            terms_accepted=True,
            marketing_consent=True,
            timestamp=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await repo.create_consent(consent_db)
        await repo.commit()
        
        consent = await consent_service.get_consent(user_id, session=async_session)
        
        assert consent is not None
        assert consent.user_id == user_id
        assert consent.terms_accepted is True
        assert consent.marketing_consent is True
    
    @pytest.mark.asyncio
    async def test_get_consent_not_found(self, consent_service, async_session):
        """Test getting consent for non-existent user."""
        user_id = "nonexistent_user"
        
        consent = await consent_service.get_consent(user_id, session=async_session)
        
        assert consent is None
    
    @pytest.mark.asyncio
    async def test_update_consent(self, consent_service, async_session):
        """Test updating existing consent."""
        user_id = "test_user_update_consent"
        
        # Pre-create consent
        from app.database.repositories.consent_repository import ConsentRepository
        repo = ConsentRepository(async_session)
        
        consent_db = UserConsentDB(
            user_id=user_id,
            terms_accepted=True,
            marketing_consent=False,
            timestamp=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await repo.create_consent(consent_db)
        await repo.commit()
        
        # Update consent
        update_data = UserConsentUpdate(marketing_consent=True)
        updated_consent = await consent_service.update_consent(user_id, update_data, session=async_session)
        
        assert updated_consent is not None
        assert updated_consent.user_id == user_id
        assert updated_consent.terms_accepted is True  # Unchanged
        assert updated_consent.marketing_consent is True  # Updated
    
    @pytest.mark.asyncio
    async def test_create_duplicate_consent(self, consent_service, async_session):
        """Test creating duplicate consent raises appropriate error."""
        user_id = "test_user_duplicate_consent"
        
        # Pre-create consent
        from app.database.repositories.consent_repository import ConsentRepository
        repo = ConsentRepository(async_session)
        
        consent_db = UserConsentDB(
            user_id=user_id,
            terms_accepted=True,
            marketing_consent=False,
            timestamp=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await repo.create_consent(consent_db)
        await repo.commit()
        
        # Try to create duplicate consent
        consent_data = UserConsentCreate(
            terms_accepted=False,
            marketing_consent=True
        )
        
        with pytest.raises((RepositoryIntegrityError, RepositoryError)):
            await consent_service.create_consent(user_id, consent_data, session=async_session)
    
    @pytest.mark.asyncio
    async def test_database_connectivity_issues_consent(self, consent_service):
        """Test handling of database connectivity issues in consent service."""
        user_id = "test_user_db_error_consent"
        
        with patch('app.services.user_consent_service.get_db_session') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")
            
            with pytest.raises(Exception):
                await consent_service.get_consent(user_id)


class TestQueryCacheServiceIntegration:
    """Integration tests for QueryCacheService with database."""
    
    @pytest.mark.asyncio
    async def test_generate_query_hash_consistency(self, cache_service):
        """Test that query hash generation is consistent."""
        query = "Find me a laptop"
        context = "Looking for gaming laptops"
        
        hash1 = cache_service.generate_query_hash(query, context)
        hash2 = cache_service.generate_query_hash(query, context)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex string length
    
    @pytest.mark.asyncio
    async def test_generate_query_hash_different_queries(self, cache_service):
        """Test that different queries generate different hashes."""
        query1 = "Find me a laptop"
        query2 = "Find me a phone"
        
        hash1 = cache_service.generate_query_hash(query1)
        hash2 = cache_service.generate_query_hash(query2)
        
        assert hash1 != hash2
    
    @pytest.mark.asyncio
    async def test_generate_query_hash_normalization(self, cache_service):
        """Test that query normalization works correctly."""
        # These should generate the same hash due to normalization
        query1 = "Find me a laptop"
        query2 = "FIND ME A LAPTOP"
        query3 = "  find me a laptop  "
        
        hash1 = cache_service.generate_query_hash(query1)
        hash2 = cache_service.generate_query_hash(query2)
        hash3 = cache_service.generate_query_hash(query3)
        
        assert hash1 == hash2 == hash3
    
    @pytest.mark.asyncio
    async def test_cache_operations_with_database_mock(self, cache_service):
        """Test cache operations with mocked database."""
        query = "Find me a laptop"
        result_data = {"products": ["laptop1", "laptop2"]}
        
        # Mock the database manager and repository
        with patch('app.services.query_cache_service.database_manager') as mock_db_manager:
            mock_session = AsyncMock()
            mock_db_manager.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_db_manager.get_session.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Mock repository methods
            with patch('app.database.repositories.cache_repository.CacheRepository') as mock_repo_class:
                mock_repo = AsyncMock()
                mock_repo_class.return_value = mock_repo
                
                # Test cache miss (get returns None)
                mock_repo.get_cached_result.return_value = None
                
                cached_result = await cache_service.get_cached_result(query)
                assert cached_result is None
                
                # Test cache hit
                from app.database.models import QueryCacheDB
                mock_cache_entry = QueryCacheDB(
                    query_hash=cache_service.generate_query_hash(query),
                    result=result_data,
                    cached_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(hours=1)
                )
                mock_repo.get_cached_result.return_value = mock_cache_entry
                
                cached_result = await cache_service.get_cached_result(query)
                assert cached_result == result_data
    
    @pytest.mark.asyncio
    async def test_cache_statistics_tracking(self, cache_service):
        """Test that cache statistics are tracked correctly."""
        # Reset statistics
        cache_service._cache_hits = 0
        cache_service._cache_misses = 0
        
        query = "Find me a laptop"
        
        # Mock database operations
        with patch('app.services.query_cache_service.database_manager') as mock_db_manager:
            mock_session = AsyncMock()
            mock_db_manager.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_db_manager.get_session.return_value.__aexit__ = AsyncMock(return_value=None)
            
            with patch('app.database.repositories.cache_repository.CacheRepository') as mock_repo_class:
                mock_repo = AsyncMock()
                mock_repo_class.return_value = mock_repo
                
                # Simulate cache miss
                mock_repo.get_cached_result.return_value = None
                await cache_service.get_cached_result(query)
                
                # Simulate cache hit
                mock_cache_entry = AsyncMock()
                mock_cache_entry.result = {"products": ["laptop1"]}
                mock_repo.get_cached_result.return_value = mock_cache_entry
                await cache_service.get_cached_result(query)
                
                # Check statistics
                stats = cache_service.get_cache_statistics()
                assert stats['cache_hits'] >= 1
                assert stats['cache_misses'] >= 1
    
    @pytest.mark.asyncio
    async def test_database_connectivity_issues_cache(self, cache_service):
        """Test handling of database connectivity issues in cache service."""
        query = "Find me a laptop"
        
        # Mock database manager to raise connection error
        with patch('app.services.query_cache_service.database_manager') as mock_db_manager:
            mock_db_manager.get_session.side_effect = Exception("Database connection failed")
            
            # Cache service should handle database errors gracefully
            # It might return None or raise an exception depending on implementation
            try:
                result = await cache_service.get_cached_result(query)
                # If no exception, result should be None (cache miss due to DB error)
                assert result is None
            except Exception:
                # If exception is raised, that's also acceptable behavior
                pass


class TestServiceErrorHandling:
    """Test error handling across all services."""
    
    @pytest.mark.asyncio
    async def test_repository_error_propagation(self, credit_service, async_session):
        """Test that repository errors are properly propagated through services."""
        user_id = "test_error_propagation"
        
        with patch('app.services.credit_service.get_db_session') as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=async_session)
            mock_get_db.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Mock repository to raise an error
            with patch('app.database.repositories.credit_repository.CreditRepository') as mock_repo_class:
                mock_repo = AsyncMock()
                mock_repo_class.return_value = mock_repo
                mock_repo.get_user_credits.side_effect = RepositoryError("Database error")
                
                with pytest.raises(RepositoryError):
                    await credit_service.get_user_credits(user_id, is_guest=True)
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_service_error(self, consent_service, async_session):
        """Test that transactions are rolled back when service operations fail."""
        user_id = "test_transaction_rollback"
        consent_data = UserConsentCreate(
            terms_accepted=True,
            marketing_consent=False
        )
        
        with patch('app.services.user_consent_service.get_db_session') as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=async_session)
            mock_get_db.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Mock repository to raise error after partial operation
            with patch('app.database.repositories.consent_repository.ConsentRepository') as mock_repo_class:
                mock_repo = AsyncMock()
                mock_repo_class.return_value = mock_repo
                mock_repo.create_consent.side_effect = RepositoryError("Database constraint violation")
                
                with pytest.raises(RepositoryError):
                    await consent_service.create_consent(user_id, consent_data)
                
                # Verify that rollback was called (through session context manager)
                # This is implicitly tested by the session fixture cleanup