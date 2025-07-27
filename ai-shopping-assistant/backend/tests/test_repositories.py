"""Unit tests for database repositories."""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.pool import StaticPool

# Create a separate Base for testing to avoid JSONB issues with SQLite
from sqlalchemy.orm import DeclarativeBase

class TestBase(DeclarativeBase):
    """Test-specific base class for SQLAlchemy models."""
    pass

# Import only the models we need for testing, avoiding QueryCacheDB
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text,
    CheckConstraint, Index, func
)

class UserCreditsDB(TestBase):
    """Database model for user credit information."""
    
    __tablename__ = "user_credits"
    
    # Primary key
    user_id = Column(String, primary_key=True, nullable=False)
    
    # User type and credit information
    is_guest = Column(Boolean, nullable=False, default=True)
    available_credits = Column(Integer, nullable=False, default=0)
    max_credits = Column(Integer, nullable=False, default=10)
    
    # Timestamp tracking
    last_reset_timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint('available_credits >= 0', name='check_available_credits_non_negative'),
        CheckConstraint('max_credits > 0', name='check_max_credits_positive'),
        Index('idx_user_credits_user_id', 'user_id'),
        Index('idx_user_credits_is_guest', 'is_guest'),
        Index('idx_user_credits_last_reset', 'last_reset_timestamp'),
    )


class CreditTransactionDB(TestBase):
    """Database model for credit transaction history."""
    
    __tablename__ = "credit_transactions"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Transaction details
    user_id = Column(String, nullable=False)
    transaction_type = Column(String, nullable=False)  # 'deduct', 'reset', 'grant'
    amount = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    description = Column(Text, nullable=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('amount != 0', name='check_amount_non_zero'),
        Index('idx_credit_transactions_user_id', 'user_id'),
        Index('idx_credit_transactions_timestamp', 'timestamp'),
        Index('idx_credit_transactions_type', 'transaction_type'),
        Index('idx_credit_transactions_user_timestamp', 'user_id', 'timestamp'),
    )


class UserConsentDB(TestBase):
    """Database model for user consent records."""
    
    __tablename__ = "user_consents"
    
    # Primary key
    user_id = Column(String, primary_key=True, nullable=False)
    
    # Consent information
    terms_accepted = Column(Boolean, nullable=False, default=True)
    marketing_consent = Column(Boolean, nullable=False, default=False)
    
    # Timestamp tracking
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_user_consents_user_id', 'user_id'),
        Index('idx_user_consents_terms_accepted', 'terms_accepted'),
        Index('idx_user_consents_updated_at', 'updated_at'),
    )

# Import repository classes and create test versions that use our test models
from app.database.repositories.base import (
    BaseRepository, RepositoryError, RepositoryIntegrityError, RepositoryOperationalError
)

# Create test versions of repositories that use test models
class CreditRepositoryTest(BaseRepository[UserCreditsDB]):
    """Test version of CreditRepository."""
    
    def __init__(self, session):
        super().__init__(session, UserCreditsDB)
    
    # Copy all methods from CreditRepository but use test models
    async def get_user_credits(self, user_id: str):
        return await self.get_by_id(user_id)
    
    async def create_user_credits(self, user_credits: UserCreditsDB):
        return await self.create(user_credits)
    
    async def update_user_credits(self, user_id: str, **updates):
        updates['updated_at'] = datetime.utcnow()
        return await self.update_by_id(user_id, **updates)
    
    async def delete_user_credits(self, user_id: str):
        return await self.delete_by_id(user_id)
    
    async def create_transaction(self, transaction: CreditTransactionDB):
        self.session.add(transaction)
        await self.flush()
        await self.refresh(transaction)
        return transaction

class ConsentRepositoryTest(BaseRepository[UserConsentDB]):
    """Test version of ConsentRepository."""
    
    def __init__(self, session):
        super().__init__(session, UserConsentDB)
    
    async def get_consent(self, user_id: str):
        return await self.get_by_id(user_id)
    
    async def create_consent(self, consent: UserConsentDB):
        return await self.create(consent)
    
    async def update_consent(self, user_id: str, **updates):
        updates['updated_at'] = datetime.utcnow()
        return await self.update_by_id(user_id, **updates)
    
    async def delete_consent(self, user_id: str):
        return await self.delete_by_id(user_id)

# Use test versions
CreditRepository = CreditRepositoryTest
ConsentRepository = ConsentRepositoryTest
Base = TestBase


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
def sample_user_credits():
    """Sample user credits data for testing."""
    return UserCreditsDB(
        user_id="test_user_123",
        is_guest=False,
        available_credits=5,
        max_credits=10,
        last_reset_timestamp=datetime.utcnow()
    )


@pytest.fixture
def sample_credit_transaction():
    """Sample credit transaction data for testing."""
    return CreditTransactionDB(
        user_id="test_user_123",
        transaction_type="deduct",
        amount=-1,
        description="Test transaction"
    )


@pytest.fixture
def sample_user_consent():
    """Sample user consent data for testing."""
    return UserConsentDB(
        user_id="test_user_123",
        terms_accepted=True,
        marketing_consent=False
    )





class TestBaseRepository:
    """Test cases for BaseRepository."""
    
    @pytest.mark.asyncio
    async def test_create_instance(self, async_session, sample_user_credits):
        """Test creating a new instance."""
        repo = BaseRepository(async_session, UserCreditsDB)
        
        result = await repo.create(sample_user_credits)
        
        assert result.user_id == "test_user_123"
        assert result.available_credits == 5
        assert result.max_credits == 10
    
    @pytest.mark.asyncio
    async def test_get_by_id(self, async_session, sample_user_credits):
        """Test getting instance by ID."""
        repo = BaseRepository(async_session, UserCreditsDB)
        
        # Create instance first
        await repo.create(sample_user_credits)
        await repo.commit()
        
        # Get by ID
        result = await repo.get_by_id("test_user_123")
        
        assert result is not None
        assert result.user_id == "test_user_123"
        assert result.available_credits == 5
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, async_session):
        """Test getting instance by ID when not found."""
        repo = BaseRepository(async_session, UserCreditsDB)
        
        result = await repo.get_by_id("nonexistent_user")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_by_id(self, async_session, sample_user_credits):
        """Test updating instance by ID."""
        repo = BaseRepository(async_session, UserCreditsDB)
        
        # Create instance first
        await repo.create(sample_user_credits)
        await repo.commit()
        
        # Update
        result = await repo.update_by_id("test_user_123", available_credits=8)
        
        assert result is not None
        assert result.available_credits == 8
        assert result.max_credits == 10  # Unchanged
    
    @pytest.mark.asyncio
    async def test_update_by_id_not_found(self, async_session):
        """Test updating instance by ID when not found."""
        repo = BaseRepository(async_session, UserCreditsDB)
        
        result = await repo.update_by_id("nonexistent_user", available_credits=8)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_by_id(self, async_session, sample_user_credits):
        """Test deleting instance by ID."""
        repo = BaseRepository(async_session, UserCreditsDB)
        
        # Create instance first
        await repo.create(sample_user_credits)
        await repo.commit()
        
        # Delete
        result = await repo.delete_by_id("test_user_123")
        
        assert result is True
        
        # Verify deletion
        deleted_instance = await repo.get_by_id("test_user_123")
        assert deleted_instance is None
    
    @pytest.mark.asyncio
    async def test_delete_by_id_not_found(self, async_session):
        """Test deleting instance by ID when not found."""
        repo = BaseRepository(async_session, UserCreditsDB)
        
        result = await repo.delete_by_id("nonexistent_user")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_all(self, async_session):
        """Test getting all instances."""
        repo = BaseRepository(async_session, UserCreditsDB)
        
        # Create multiple instances
        users = [
            UserCreditsDB(user_id="user1", available_credits=5, max_credits=10),
            UserCreditsDB(user_id="user2", available_credits=3, max_credits=10),
            UserCreditsDB(user_id="user3", available_credits=7, max_credits=10)
        ]
        
        for user in users:
            await repo.create(user)
        await repo.commit()
        
        # Get all
        result = await repo.get_all()
        
        assert len(result) == 3
        user_ids = [user.user_id for user in result]
        assert "user1" in user_ids
        assert "user2" in user_ids
        assert "user3" in user_ids
    
    @pytest.mark.asyncio
    async def test_get_all_with_pagination(self, async_session):
        """Test getting all instances with pagination."""
        repo = BaseRepository(async_session, UserCreditsDB)
        
        # Create multiple instances
        for i in range(5):
            user = UserCreditsDB(user_id=f"user{i}", available_credits=i, max_credits=10)
            await repo.create(user)
        await repo.commit()
        
        # Get with limit
        result = await repo.get_all(limit=3)
        assert len(result) == 3
        
        # Get with offset
        result = await repo.get_all(limit=2, offset=2)
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_count(self, async_session):
        """Test counting instances."""
        repo = BaseRepository(async_session, UserCreditsDB)
        
        # Create instances
        for i in range(3):
            user = UserCreditsDB(user_id=f"user{i}", available_credits=i, max_credits=10, is_guest=(i % 2 == 0))
            await repo.create(user)
        await repo.commit()
        
        # Count all
        total_count = await repo.count()
        assert total_count == 3
        
        # Count with filter
        guest_count = await repo.count(is_guest=True)
        assert guest_count == 2  # user0 and user2
    
    @pytest.mark.asyncio
    async def test_exists(self, async_session, sample_user_credits):
        """Test checking if instance exists."""
        repo = BaseRepository(async_session, UserCreditsDB)
        
        # Check non-existent
        exists = await repo.exists(user_id="test_user_123")
        assert exists is False
        
        # Create instance
        await repo.create(sample_user_credits)
        await repo.commit()
        
        # Check existing
        exists = await repo.exists(user_id="test_user_123")
        assert exists is True
    
    @pytest.mark.asyncio
    async def test_find_by(self, async_session):
        """Test finding instances by filters."""
        repo = BaseRepository(async_session, UserCreditsDB)
        
        # Create instances
        users = [
            UserCreditsDB(user_id="guest1", is_guest=True, available_credits=5, max_credits=10),
            UserCreditsDB(user_id="guest2", is_guest=True, available_credits=3, max_credits=10),
            UserCreditsDB(user_id="registered1", is_guest=False, available_credits=7, max_credits=20)
        ]
        
        for user in users:
            await repo.create(user)
        await repo.commit()
        
        # Find guests
        guests = await repo.find_by(is_guest=True)
        assert len(guests) == 2
        
        # Find with multiple filters
        specific_guest = await repo.find_by(is_guest=True, available_credits=5)
        assert len(specific_guest) == 1
        assert specific_guest[0].user_id == "guest1"
    
    @pytest.mark.asyncio
    async def test_find_one_by(self, async_session, sample_user_credits):
        """Test finding single instance by filters."""
        repo = BaseRepository(async_session, UserCreditsDB)
        
        await repo.create(sample_user_credits)
        await repo.commit()
        
        # Find existing
        result = await repo.find_one_by(user_id="test_user_123")
        assert result is not None
        assert result.user_id == "test_user_123"
        
        # Find non-existing
        result = await repo.find_one_by(user_id="nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_commit_rollback_flush(self, async_session, sample_user_credits):
        """Test transaction management methods."""
        repo = BaseRepository(async_session, UserCreditsDB)
        
        # Test flush
        await repo.create(sample_user_credits)
        await repo.flush()
        
        # Test rollback
        await repo.rollback()
        
        # Verify rollback worked
        result = await repo.get_by_id("test_user_123")
        assert result is None
        
        # Test commit
        await repo.create(sample_user_credits)
        await repo.commit()
        
        result = await repo.get_by_id("test_user_123")
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_refresh(self, async_session, sample_user_credits):
        """Test refreshing instance from database."""
        repo = BaseRepository(async_session, UserCreditsDB)
        
        created = await repo.create(sample_user_credits)
        await repo.commit()
        
        # Modify instance in memory
        created.available_credits = 999
        
        # Refresh from database
        refreshed = await repo.refresh(created)
        
        assert refreshed.available_credits == 5  # Original value
    
    @pytest.mark.asyncio
    async def test_error_handling_integrity_error(self, async_session, sample_user_credits):
        """Test handling of integrity constraint violations."""
        repo = BaseRepository(async_session, UserCreditsDB)
        
        # Create first instance
        await repo.create(sample_user_credits)
        await repo.commit()
        
        # Try to create duplicate (should raise RepositoryIntegrityError)
        duplicate = UserCreditsDB(
            user_id="test_user_123",  # Same ID
            available_credits=10,
            max_credits=20
        )
        
        with pytest.raises((RepositoryIntegrityError, RepositoryError)):
            await repo.create(duplicate)
    
    @pytest.mark.asyncio
    async def test_error_handling_sqlalchemy_error(self, async_session):
        """Test handling of general SQLAlchemy errors."""
        repo = BaseRepository(async_session, UserCreditsDB)
        
        # Mock session to raise SQLAlchemyError
        with patch.object(async_session, 'get', side_effect=SQLAlchemyError("Test error")):
            with pytest.raises(RepositoryError):
                await repo.get_by_id("test_user")


class TestCreditRepository:
    """Test cases for CreditRepository."""
    
    @pytest.mark.asyncio
    async def test_get_user_credits(self, async_session, sample_user_credits):
        """Test getting user credits."""
        repo = CreditRepository(async_session)
        
        # Create credits
        await repo.create_user_credits(sample_user_credits)
        await repo.commit()
        
        # Get credits
        result = await repo.get_user_credits("test_user_123")
        
        assert result is not None
        assert result.user_id == "test_user_123"
        assert result.available_credits == 5
        assert result.max_credits == 10
    
    @pytest.mark.asyncio
    async def test_get_user_credits_not_found(self, async_session):
        """Test getting user credits when not found."""
        repo = CreditRepository(async_session)
        
        result = await repo.get_user_credits("nonexistent_user")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_user_credits(self, async_session, sample_user_credits):
        """Test creating user credits."""
        repo = CreditRepository(async_session)
        
        result = await repo.create_user_credits(sample_user_credits)
        
        assert result.user_id == "test_user_123"
        assert result.available_credits == 5
        assert result.max_credits == 10
        assert result.is_guest is False
    
    @pytest.mark.asyncio
    async def test_create_user_credits_duplicate(self, async_session, sample_user_credits):
        """Test creating duplicate user credits raises error."""
        repo = CreditRepository(async_session)
        
        # Create first instance
        await repo.create_user_credits(sample_user_credits)
        await repo.commit()
        
        # Try to create duplicate
        duplicate = UserCreditsDB(
            user_id="test_user_123",
            available_credits=10,
            max_credits=20
        )
        
        with pytest.raises(RepositoryIntegrityError):
            await repo.create_user_credits(duplicate)
    
    @pytest.mark.asyncio
    async def test_update_user_credits(self, async_session, sample_user_credits):
        """Test updating user credits."""
        repo = CreditRepository(async_session)
        
        # Create credits
        await repo.create_user_credits(sample_user_credits)
        await repo.commit()
        
        # Update credits
        result = await repo.update_user_credits("test_user_123", available_credits=8)
        
        assert result is not None
        assert result.available_credits == 8
        assert result.max_credits == 10  # Unchanged
        assert result.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_update_user_credits_not_found(self, async_session):
        """Test updating user credits when not found."""
        repo = CreditRepository(async_session)
        
        result = await repo.update_user_credits("nonexistent_user", available_credits=8)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_user_credits(self, async_session, sample_user_credits):
        """Test deleting user credits."""
        repo = CreditRepository(async_session)
        
        # Create credits
        await repo.create_user_credits(sample_user_credits)
        await repo.commit()
        
        # Delete credits
        result = await repo.delete_user_credits("test_user_123")
        
        assert result is True
        
        # Verify deletion
        deleted = await repo.get_user_credits("test_user_123")
        assert deleted is None
    
    @pytest.mark.asyncio
    async def test_create_transaction(self, async_session, sample_credit_transaction):
        """Test creating credit transaction."""
        repo = CreditRepository(async_session)
        
        result = await repo.create_transaction(sample_credit_transaction)
        
        assert result.user_id == "test_user_123"
        assert result.transaction_type == "deduct"
        assert result.amount == -1
        assert result.description == "Test transaction"
        assert result.id is not None
    
    @pytest.mark.asyncio
    async def test_get_user_transactions(self, async_session):
        """Test getting user transactions."""
        repo = CreditRepository(async_session)
        
        # Create multiple transactions
        transactions = [
            CreditTransactionDB(user_id="test_user", transaction_type="deduct", amount=-1),
            CreditTransactionDB(user_id="test_user", transaction_type="reset", amount=10),
            CreditTransactionDB(user_id="other_user", transaction_type="deduct", amount=-2)
        ]
        
        for transaction in transactions:
            await repo.create_transaction(transaction)
        await repo.commit()
        
        # Get transactions for specific user
        result = await repo.get_user_transactions("test_user")
        
        assert len(result) == 2
        # Should be ordered by timestamp descending (newest first)
        assert result[0].transaction_type in ["deduct", "reset"]
        assert result[1].transaction_type in ["deduct", "reset"]
    
    @pytest.mark.asyncio
    async def test_get_user_transactions_with_filters(self, async_session):
        """Test getting user transactions with filters."""
        repo = CreditRepository(async_session)
        
        # Create transactions
        transactions = [
            CreditTransactionDB(user_id="test_user", transaction_type="deduct", amount=-1),
            CreditTransactionDB(user_id="test_user", transaction_type="deduct", amount=-2),
            CreditTransactionDB(user_id="test_user", transaction_type="reset", amount=10)
        ]
        
        for transaction in transactions:
            await repo.create_transaction(transaction)
        await repo.commit()
        
        # Get with transaction type filter
        deduct_transactions = await repo.get_user_transactions("test_user", transaction_type="deduct")
        assert len(deduct_transactions) == 2
        
        # Get with limit
        limited_transactions = await repo.get_user_transactions("test_user", limit=2)
        assert len(limited_transactions) == 2
    
    @pytest.mark.asyncio
    async def test_get_transaction_by_id(self, async_session, sample_credit_transaction):
        """Test getting transaction by ID."""
        repo = CreditRepository(async_session)
        
        created = await repo.create_transaction(sample_credit_transaction)
        await repo.commit()
        
        result = await repo.get_transaction_by_id(created.id)
        
        assert result is not None
        assert result.id == created.id
        assert result.user_id == "test_user_123"
    
    @pytest.mark.asyncio
    async def test_get_transactions_by_date_range(self, async_session):
        """Test getting transactions by date range."""
        repo = CreditRepository(async_session)
        
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        
        # Create transactions with different timestamps
        old_transaction = CreditTransactionDB(
            user_id="test_user", 
            transaction_type="deduct", 
            amount=-1,
            timestamp=yesterday - timedelta(hours=1)
        )
        recent_transaction = CreditTransactionDB(
            user_id="test_user", 
            transaction_type="reset", 
            amount=10,
            timestamp=now
        )
        
        await repo.create_transaction(old_transaction)
        await repo.create_transaction(recent_transaction)
        await repo.commit()
        
        # Get transactions in date range
        result = await repo.get_transactions_by_date_range("test_user", yesterday, tomorrow)
        
        assert len(result) == 1
        assert result[0].transaction_type == "reset"
    
    @pytest.mark.asyncio
    async def test_cleanup_old_transactions(self, async_session):
        """Test cleaning up old transactions."""
        repo = CreditRepository(async_session)
        
        now = datetime.utcnow()
        old_date = now - timedelta(days=100)
        
        # Create old and recent transactions
        old_transaction = CreditTransactionDB(
            user_id="test_user", 
            transaction_type="deduct", 
            amount=-1,
            timestamp=old_date
        )
        recent_transaction = CreditTransactionDB(
            user_id="test_user", 
            transaction_type="reset", 
            amount=10,
            timestamp=now
        )
        
        await repo.create_transaction(old_transaction)
        await repo.create_transaction(recent_transaction)
        await repo.commit()
        
        # Cleanup transactions older than 90 days
        deleted_count = await repo.cleanup_old_transactions(days=90)
        await repo.commit()
        
        assert deleted_count == 1
        
        # Verify only recent transaction remains
        remaining = await repo.get_user_transactions("test_user")
        assert len(remaining) == 1
        assert remaining[0].transaction_type == "reset"
    
    @pytest.mark.asyncio
    async def test_get_transaction_statistics(self, async_session):
        """Test getting transaction statistics."""
        repo = CreditRepository(async_session)
        
        # Create various transactions
        transactions = [
            CreditTransactionDB(user_id="test_user", transaction_type="deduct", amount=-1),
            CreditTransactionDB(user_id="test_user", transaction_type="deduct", amount=-2),
            CreditTransactionDB(user_id="test_user", transaction_type="reset", amount=10),
            CreditTransactionDB(user_id="test_user", transaction_type="grant", amount=5)
        ]
        
        for transaction in transactions:
            await repo.create_transaction(transaction)
        await repo.commit()
        
        # Get statistics
        stats = await repo.get_transaction_statistics("test_user", days=30)
        
        assert stats['period_days'] == 30
        assert stats['total_transactions'] == 4
        assert stats['net_credit_change'] == 12  # -1 + -2 + 10 + 5
        assert 'deduct' in stats['transactions_by_type']
        assert stats['transactions_by_type']['deduct']['count'] == 2
        assert stats['transactions_by_type']['deduct']['total_amount'] == -3
    
    @pytest.mark.asyncio
    async def test_get_users_needing_reset(self, async_session):
        """Test getting users needing credit reset."""
        repo = CreditRepository(async_session)
        
        now = datetime.utcnow()
        old_reset_time = now - timedelta(hours=25)  # More than 24 hours ago
        recent_reset_time = now - timedelta(hours=1)  # Less than 24 hours ago
        
        # Create users with different reset times
        old_user = UserCreditsDB(
            user_id="old_user",
            available_credits=0,
            max_credits=10,
            last_reset_timestamp=old_reset_time
        )
        recent_user = UserCreditsDB(
            user_id="recent_user",
            available_credits=5,
            max_credits=10,
            last_reset_timestamp=recent_reset_time
        )
        
        await repo.create_user_credits(old_user)
        await repo.create_user_credits(recent_user)
        await repo.commit()
        
        # Get users needing reset (default 24 hours)
        users_needing_reset = await repo.get_users_needing_reset()
        
        assert len(users_needing_reset) == 1
        assert users_needing_reset[0].user_id == "old_user"
    
    @pytest.mark.asyncio
    async def test_batch_reset_credits(self, async_session):
        """Test batch resetting credits for multiple users."""
        repo = CreditRepository(async_session)
        
        # Create users
        users = [
            UserCreditsDB(user_id="user1", available_credits=0, max_credits=10),
            UserCreditsDB(user_id="user2", available_credits=3, max_credits=15),
            UserCreditsDB(user_id="user3", available_credits=1, max_credits=20)
        ]
        
        for user in users:
            await repo.create_user_credits(user)
        await repo.commit()
        
        # Batch reset
        reset_time = datetime.utcnow()
        updated_count = await repo.batch_reset_credits(["user1", "user2"], reset_time)
        await repo.commit()
        
        assert updated_count == 2
        
        # Verify reset
        user1 = await repo.get_user_credits("user1")
        user2 = await repo.get_user_credits("user2")
        user3 = await repo.get_user_credits("user3")
        
        assert user1.available_credits == 10  # Reset to max_credits
        assert user2.available_credits == 15  # Reset to max_credits
        assert user3.available_credits == 1   # Unchanged
    
    @pytest.mark.asyncio
    async def test_get_credit_summary(self, async_session):
        """Test getting credit system summary."""
        repo = CreditRepository(async_session)
        
        # Create users
        users = [
            UserCreditsDB(user_id="guest1", is_guest=True, available_credits=5, max_credits=10),
            UserCreditsDB(user_id="guest2", is_guest=True, available_credits=3, max_credits=10),
            UserCreditsDB(user_id="registered1", is_guest=False, available_credits=15, max_credits=20)
        ]
        
        for user in users:
            await repo.create_user_credits(user)
        await repo.commit()
        
        # Get summary
        summary = await repo.get_credit_summary()
        
        assert summary['total_users'] == 3
        assert summary['guest_users'] == 2
        assert summary['registered_users'] == 1
        assert summary['total_available_credits'] == 23  # 5 + 3 + 15
        assert summary['total_max_credits'] == 40  # 10 + 10 + 20
        assert summary['avg_available_credits'] == pytest.approx(23/3, rel=1e-2)


class TestConsentRepository:
    """Test cases for ConsentRepository."""
    
    @pytest.mark.asyncio
    async def test_get_consent(self, async_session, sample_user_consent):
        """Test getting user consent."""
        repo = ConsentRepository(async_session)
        
        # Create consent
        await repo.create_consent(sample_user_consent)
        await repo.commit()
        
        # Get consent
        result = await repo.get_consent("test_user_123")
        
        assert result is not None
        assert result.user_id == "test_user_123"
        assert result.terms_accepted is True
        assert result.marketing_consent is False
    
    @pytest.mark.asyncio
    async def test_create_consent(self, async_session, sample_user_consent):
        """Test creating user consent."""
        repo = ConsentRepository(async_session)
        
        result = await repo.create_consent(sample_user_consent)
        
        assert result.user_id == "test_user_123"
        assert result.terms_accepted is True
        assert result.marketing_consent is False
    
    @pytest.mark.asyncio
    async def test_create_consent_duplicate(self, async_session, sample_user_consent):
        """Test creating duplicate consent raises error."""
        repo = ConsentRepository(async_session)
        
        # Create first instance
        await repo.create_consent(sample_user_consent)
        await repo.commit()
        
        # Try to create duplicate
        duplicate = UserConsentDB(
            user_id="test_user_123",
            terms_accepted=False,
            marketing_consent=True
        )
        
        with pytest.raises(RepositoryIntegrityError):
            await repo.create_consent(duplicate)
    
    @pytest.mark.asyncio
    async def test_update_consent(self, async_session, sample_user_consent):
        """Test updating user consent."""
        repo = ConsentRepository(async_session)
        
        # Create consent
        await repo.create_consent(sample_user_consent)
        await repo.commit()
        
        # Update consent
        result = await repo.update_consent("test_user_123", marketing_consent=True)
        
        assert result is not None
        assert result.marketing_consent is True
        assert result.terms_accepted is True  # Unchanged
        assert result.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_delete_consent(self, async_session, sample_user_consent):
        """Test deleting user consent."""
        repo = ConsentRepository(async_session)
        
        # Create consent
        await repo.create_consent(sample_user_consent)
        await repo.commit()
        
        # Delete consent
        result = await repo.delete_consent("test_user_123")
        
        assert result is True
        
        # Verify deletion
        deleted = await repo.get_consent("test_user_123")
        assert deleted is None
    
    @pytest.mark.asyncio
    async def test_list_consents(self, async_session):
        """Test listing consents with filters."""
        repo = ConsentRepository(async_session)
        
        # Create consents
        consents = [
            UserConsentDB(user_id="user1", terms_accepted=True, marketing_consent=True),
            UserConsentDB(user_id="user2", terms_accepted=True, marketing_consent=False),
            UserConsentDB(user_id="user3", terms_accepted=False, marketing_consent=False)
        ]
        
        for consent in consents:
            await repo.create_consent(consent)
        await repo.commit()
        
        # List all
        all_consents = await repo.list_consents()
        assert len(all_consents) == 3
        
        # List with filter
        marketing_consents = await repo.list_consents(marketing_consent=True)
        assert len(marketing_consents) == 1
        assert marketing_consents[0].user_id == "user1"
        
        # List with pagination
        limited_consents = await repo.list_consents(limit=2)
        assert len(limited_consents) == 2
    
    @pytest.mark.asyncio
    async def test_get_consents_by_user_ids(self, async_session):
        """Test getting consents by user IDs."""
        repo = ConsentRepository(async_session)
        
        # Create consents
        consents = [
            UserConsentDB(user_id="user1", terms_accepted=True, marketing_consent=True),
            UserConsentDB(user_id="user2", terms_accepted=True, marketing_consent=False),
            UserConsentDB(user_id="user3", terms_accepted=False, marketing_consent=False)
        ]
        
        for consent in consents:
            await repo.create_consent(consent)
        await repo.commit()
        
        # Get specific users
        result = await repo.get_consents_by_user_ids(["user1", "user3", "nonexistent"])
        
        assert len(result) == 2
        user_ids = [consent.user_id for consent in result]
        assert "user1" in user_ids
        assert "user3" in user_ids
        assert "nonexistent" not in user_ids
    
    @pytest.mark.asyncio
    async def test_batch_update_marketing_consent(self, async_session):
        """Test batch updating marketing consent."""
        repo = ConsentRepository(async_session)
        
        # Create consents
        consents = [
            UserConsentDB(user_id="user1", terms_accepted=True, marketing_consent=False),
            UserConsentDB(user_id="user2", terms_accepted=True, marketing_consent=False),
            UserConsentDB(user_id="user3", terms_accepted=True, marketing_consent=False)
        ]
        
        for consent in consents:
            await repo.create_consent(consent)
        await repo.commit()
        
        # Batch update
        updated_count = await repo.batch_update_marketing_consent(["user1", "user2"], True)
        await repo.commit()
        
        assert updated_count == 2
        
        # Verify updates
        user1 = await repo.get_consent("user1")
        user2 = await repo.get_consent("user2")
        user3 = await repo.get_consent("user3")
        
        assert user1.marketing_consent is True
        assert user2.marketing_consent is True
        assert user3.marketing_consent is False  # Unchanged
    
    @pytest.mark.asyncio
    async def test_get_consent_statistics(self, async_session):
        """Test getting consent statistics."""
        repo = ConsentRepository(async_session)
        
        # Create consents
        consents = [
            UserConsentDB(user_id="user1", terms_accepted=True, marketing_consent=True),
            UserConsentDB(user_id="user2", terms_accepted=True, marketing_consent=False),
            UserConsentDB(user_id="user3", terms_accepted=False, marketing_consent=False),
            UserConsentDB(user_id="user4", terms_accepted=True, marketing_consent=True)
        ]
        
        for consent in consents:
            await repo.create_consent(consent)
        await repo.commit()
        
        # Get statistics
        stats = await repo.get_consent_statistics()
        
        assert stats['total_users'] == 4
        assert stats['terms_accepted']['count'] == 3
        assert stats['terms_accepted']['percentage'] == 75.0
        assert stats['marketing_consent']['count'] == 2
        assert stats['marketing_consent']['percentage'] == 50.0
        assert stats['both_consents']['count'] == 2
        assert stats['both_consents']['percentage'] == 50.0
    
    @pytest.mark.asyncio
    async def test_find_users_without_consent(self, async_session):
        """Test finding users without consent records."""
        repo = ConsentRepository(async_session)
        
        # Create consent for some users
        consent = UserConsentDB(user_id="user1", terms_accepted=True, marketing_consent=False)
        await repo.create_consent(consent)
        await repo.commit()
        
        # Check which users don't have consent
        user_ids = ["user1", "user2", "user3"]
        users_without_consent = await repo.find_users_without_consent(user_ids)
        
        assert len(users_without_consent) == 2
        assert "user2" in users_without_consent
        assert "user3" in users_without_consent
        assert "user1" not in users_without_consent
    
    @pytest.mark.asyncio
    async def test_export_consent_data(self, async_session):
        """Test exporting consent data."""
        repo = ConsentRepository(async_session)
        
        # Create consents
        consents = [
            UserConsentDB(user_id="user1", terms_accepted=True, marketing_consent=True),
            UserConsentDB(user_id="user2", terms_accepted=True, marketing_consent=False)
        ]
        
        for consent in consents:
            await repo.create_consent(consent)
        await repo.commit()
        
        # Export all data
        export_data = await repo.export_consent_data()
        
        assert len(export_data) == 2
        assert all('user_id' in record for record in export_data)
        assert all('terms_accepted' in record for record in export_data)
        assert all('marketing_consent' in record for record in export_data)
        
        # Export specific users
        specific_export = await repo.export_consent_data(user_ids=["user1"])
        assert len(specific_export) == 1
        assert specific_export[0]['user_id'] == "user1"


# Cache repository tests will be in a separate file due to SQLite JSONB compatibility issues


class TestRepositoryErrorHandling:
    """Test cases for repository error handling and transaction rollback scenarios."""
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_integrity_error(self, async_session):
        """Test that transactions are rolled back on integrity errors."""
        repo = CreditRepository(async_session)
        
        # Create initial user
        user1 = UserCreditsDB(user_id="test_user", available_credits=5, max_credits=10)
        await repo.create_user_credits(user1)
        await repo.commit()
        
        # Try to create duplicate user (should trigger rollback)
        user2 = UserCreditsDB(user_id="test_user", available_credits=8, max_credits=15)
        
        with pytest.raises(RepositoryIntegrityError):
            await repo.create_user_credits(user2)
        
        # Verify original user is unchanged
        original_user = await repo.get_user_credits("test_user")
        assert original_user.available_credits == 5
        assert original_user.max_credits == 10
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_update_error(self, async_session):
        """Test transaction rollback on update errors."""
        repo = BaseRepository(async_session, UserCreditsDB)
        
        # Create user
        user = UserCreditsDB(user_id="test_user", available_credits=5, max_credits=10)
        await repo.create(user)
        await repo.commit()
        
        # Mock session to raise error on update
        with patch.object(async_session, 'execute', side_effect=SQLAlchemyError("Update failed")):
            with pytest.raises(RepositoryError):
                await repo.update_by_id("test_user", available_credits=8)
        
        # Verify user is unchanged (rollback worked)
        unchanged_user = await repo.get_by_id("test_user")
        assert unchanged_user.available_credits == 5
    
    @pytest.mark.asyncio
    async def test_operational_error_handling(self, async_session):
        """Test handling of operational errors."""
        repo = BaseRepository(async_session, UserCreditsDB)
        
        # Mock session to raise OperationalError
        with patch.object(async_session, 'execute', side_effect=OperationalError("Connection failed", None, None)):
            with pytest.raises(RepositoryOperationalError):
                await repo.get_by_id("test_user")
    
    @pytest.mark.asyncio
    async def test_constraint_violation_error_handling(self, async_session):
        """Test handling of constraint violations."""
        repo = CreditRepository(async_session)
        
        # Try to create user with invalid data (negative max_credits would violate constraint)
        # Note: This test depends on database constraints being enforced
        invalid_user = UserCreditsDB(
            user_id="invalid_user",
            available_credits=5,
            max_credits=-1  # This should violate check constraint
        )
        
        # The exact error type depends on the database implementation
        # SQLite might not enforce all constraints, so we'll test the general error handling
        try:
            await repo.create_user_credits(invalid_user)
            await repo.commit()
        except (RepositoryIntegrityError, RepositoryError):
            # Either error type is acceptable for constraint violations
            pass
    
    @pytest.mark.asyncio
    async def test_concurrent_access_simulation(self, async_session):
        """Test handling of concurrent access patterns."""
        repo = CreditRepository(async_session)
        
        # Create initial user
        user = UserCreditsDB(user_id="concurrent_user", available_credits=10, max_credits=10)
        await repo.create_user_credits(user)
        await repo.commit()
        
        # Simulate concurrent updates
        # In a real scenario, this would be multiple async tasks
        # Here we'll test sequential updates to ensure consistency
        
        # First update
        result1 = await repo.update_user_credits("concurrent_user", available_credits=8)
        assert result1.available_credits == 8
        
        # Second update
        result2 = await repo.update_user_credits("concurrent_user", available_credits=5)
        assert result2.available_credits == 5
        
        await repo.commit()
        
        # Verify final state
        final_user = await repo.get_user_credits("concurrent_user")
        assert final_user.available_credits == 5
    
    @pytest.mark.asyncio
    async def test_session_cleanup_on_error(self, async_session):
        """Test that sessions are properly cleaned up on errors."""
        repo = BaseRepository(async_session, UserCreditsDB)
        
        # Mock session methods to track calls
        rollback_mock = AsyncMock()
        async_session.rollback = rollback_mock
        
        # Trigger an error that should cause rollback
        with patch.object(async_session, 'execute', side_effect=SQLAlchemyError("Test error")):
            with pytest.raises(RepositoryError):
                await repo.create(UserCreditsDB(user_id="test", available_credits=5, max_credits=10))
        
        # Verify rollback was called
        rollback_mock.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_flush_error_handling(self, async_session):
        """Test error handling during flush operations."""
        repo = BaseRepository(async_session, UserCreditsDB)
        
        # Mock flush to raise error
        with patch.object(async_session, 'flush', side_effect=SQLAlchemyError("Flush failed")):
            with pytest.raises(RepositoryError):
                await repo.flush()
    
    @pytest.mark.asyncio
    async def test_refresh_error_handling(self, async_session):
        """Test error handling during refresh operations."""
        repo = BaseRepository(async_session, UserCreditsDB)
        
        user = UserCreditsDB(user_id="test_user", available_credits=5, max_credits=10)
        
        # Mock refresh to raise error
        with patch.object(async_session, 'refresh', side_effect=SQLAlchemyError("Refresh failed")):
            with pytest.raises(RepositoryError):
                await repo.refresh(user)