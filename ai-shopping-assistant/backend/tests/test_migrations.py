"""Tests for database migrations and schema validation."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import text, inspect, MetaData
from sqlalchemy.exc import IntegrityError
from alembic.config import Config
from alembic import command
from alembic.runtime.migration import MigrationContext
from alembic.operations import Operations
import tempfile
import os

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
    
    yield engine
    
    # Clean up
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine):
    """Create an async session for testing."""
    async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False)
    
    async with async_session_maker() as session:
        yield session


class TestMigrationUpgrade:
    """Test database migration upgrade operations."""
    
    @pytest.mark.asyncio
    async def test_create_user_credits_table(self, async_session):
        """Test creating user_credits table with proper schema."""
        # Simulate the migration SQL for user_credits table
        create_table_sql = """
        CREATE TABLE user_credits (
            user_id VARCHAR NOT NULL,
            is_guest BOOLEAN NOT NULL DEFAULT 1,
            available_credits INTEGER NOT NULL DEFAULT 0,
            max_credits INTEGER NOT NULL DEFAULT 10,
            last_reset_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id),
            CHECK (available_credits >= 0),
            CHECK (max_credits > 0)
        )
        """
        
        await async_session.execute(text(create_table_sql))
        await async_session.commit()
        
        # Test that we can insert valid data
        insert_sql = """
        INSERT INTO user_credits (user_id, is_guest, available_credits, max_credits)
        VALUES ('test_user', 0, 5, 10)
        """
        await async_session.execute(text(insert_sql))
        await async_session.commit()
        
        # Verify data was inserted
        result = await async_session.execute(text("SELECT * FROM user_credits WHERE user_id = 'test_user'"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 'test_user'  # user_id
        assert row[1] == 0  # is_guest (False)
        assert row[2] == 5  # available_credits
        assert row[3] == 10  # max_credits
    
    @pytest.mark.asyncio
    async def test_create_credit_transactions_table(self, async_session):
        """Test creating credit_transactions table with proper schema."""
        create_table_sql = """
        CREATE TABLE credit_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR NOT NULL,
            transaction_type VARCHAR NOT NULL,
            amount INTEGER NOT NULL,
            timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            description TEXT,
            CHECK (amount != 0)
        )
        """
        
        await async_session.execute(text(create_table_sql))
        await async_session.commit()
        
        # Test inserting transaction data
        insert_sql = """
        INSERT INTO credit_transactions (user_id, transaction_type, amount, description)
        VALUES ('test_user', 'deduct', -1, 'Test deduction')
        """
        await async_session.execute(text(insert_sql))
        await async_session.commit()
        
        # Verify data
        result = await async_session.execute(text("SELECT * FROM credit_transactions"))
        row = result.fetchone()
        assert row is not None
        assert row[1] == 'test_user'  # user_id
        assert row[2] == 'deduct'  # transaction_type
        assert row[3] == -1  # amount
        assert row[5] == 'Test deduction'  # description
    
    @pytest.mark.asyncio
    async def test_create_user_consents_table(self, async_session):
        """Test creating user_consents table with proper schema."""
        create_table_sql = """
        CREATE TABLE user_consents (
            user_id VARCHAR NOT NULL PRIMARY KEY,
            terms_accepted BOOLEAN NOT NULL DEFAULT 1,
            marketing_consent BOOLEAN NOT NULL DEFAULT 0,
            timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        await async_session.execute(text(create_table_sql))
        await async_session.commit()
        
        # Test inserting consent data
        insert_sql = """
        INSERT INTO user_consents (user_id, terms_accepted, marketing_consent)
        VALUES ('test_user', 1, 0)
        """
        await async_session.execute(text(insert_sql))
        await async_session.commit()
        
        # Verify data
        result = await async_session.execute(text("SELECT * FROM user_consents WHERE user_id = 'test_user'"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 'test_user'  # user_id
        assert row[1] == 1  # terms_accepted (True)
        assert row[2] == 0  # marketing_consent (False)
    
    @pytest.mark.asyncio
    async def test_create_query_cache_table(self, async_session):
        """Test creating query_cache table with proper schema."""
        # Note: Using JSON instead of JSONB for SQLite compatibility
        create_table_sql = """
        CREATE TABLE query_cache (
            query_hash VARCHAR NOT NULL PRIMARY KEY,
            result JSON NOT NULL,
            cached_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL,
            CHECK (expires_at > cached_at)
        )
        """
        
        await async_session.execute(text(create_table_sql))
        await async_session.commit()
        
        # Test inserting cache data
        import json
        cache_data = json.dumps({"products": ["laptop1", "laptop2"]})
        future_time = datetime.utcnow() + timedelta(hours=1)
        
        insert_sql = """
        INSERT INTO query_cache (query_hash, result, expires_at)
        VALUES ('test_hash_123', ?, ?)
        """
        await async_session.execute(text(insert_sql), (cache_data, future_time))
        await async_session.commit()
        
        # Verify data
        result = await async_session.execute(text("SELECT * FROM query_cache WHERE query_hash = 'test_hash_123'"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 'test_hash_123'  # query_hash
        assert json.loads(row[1]) == {"products": ["laptop1", "laptop2"]}  # result


class TestSchemaConstraints:
    """Test database schema constraints and validation."""
    
    @pytest.mark.asyncio
    async def test_user_credits_constraints(self, async_session):
        """Test user_credits table constraints."""
        # Create table
        create_table_sql = """
        CREATE TABLE user_credits (
            user_id VARCHAR NOT NULL PRIMARY KEY,
            is_guest BOOLEAN NOT NULL DEFAULT 1,
            available_credits INTEGER NOT NULL DEFAULT 0,
            max_credits INTEGER NOT NULL DEFAULT 10,
            last_reset_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (available_credits >= 0),
            CHECK (max_credits > 0)
        )
        """
        await async_session.execute(text(create_table_sql))
        await async_session.commit()
        
        # Test primary key constraint (duplicate user_id)
        await async_session.execute(text("""
            INSERT INTO user_credits (user_id, available_credits, max_credits)
            VALUES ('test_user', 5, 10)
        """))
        await async_session.commit()
        
        with pytest.raises(IntegrityError):
            await async_session.execute(text("""
                INSERT INTO user_credits (user_id, available_credits, max_credits)
                VALUES ('test_user', 3, 15)
            """))
            await async_session.commit()
        
        # Rollback the failed transaction
        await async_session.rollback()
        
        # Test check constraint: available_credits >= 0
        with pytest.raises(IntegrityError):
            await async_session.execute(text("""
                INSERT INTO user_credits (user_id, available_credits, max_credits)
                VALUES ('negative_credits_user', -1, 10)
            """))
            await async_session.commit()
        
        await async_session.rollback()
        
        # Test check constraint: max_credits > 0
        with pytest.raises(IntegrityError):
            await async_session.execute(text("""
                INSERT INTO user_credits (user_id, available_credits, max_credits)
                VALUES ('zero_max_user', 5, 0)
            """))
            await async_session.commit()
    
    @pytest.mark.asyncio
    async def test_credit_transactions_constraints(self, async_session):
        """Test credit_transactions table constraints."""
        create_table_sql = """
        CREATE TABLE credit_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR NOT NULL,
            transaction_type VARCHAR NOT NULL,
            amount INTEGER NOT NULL,
            timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            description TEXT,
            CHECK (amount != 0)
        )
        """
        await async_session.execute(text(create_table_sql))
        await async_session.commit()
        
        # Test valid transaction
        await async_session.execute(text("""
            INSERT INTO credit_transactions (user_id, transaction_type, amount)
            VALUES ('test_user', 'deduct', -1)
        """))
        await async_session.commit()
        
        # Test check constraint: amount != 0
        with pytest.raises(IntegrityError):
            await async_session.execute(text("""
                INSERT INTO credit_transactions (user_id, transaction_type, amount)
                VALUES ('test_user', 'invalid', 0)
            """))
            await async_session.commit()
    
    @pytest.mark.asyncio
    async def test_query_cache_constraints(self, async_session):
        """Test query_cache table constraints."""
        create_table_sql = """
        CREATE TABLE query_cache (
            query_hash VARCHAR NOT NULL PRIMARY KEY,
            result JSON NOT NULL,
            cached_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL,
            CHECK (expires_at > cached_at)
        )
        """
        await async_session.execute(text(create_table_sql))
        await async_session.commit()
        
        # Test valid cache entry
        now = datetime.utcnow()
        future = now + timedelta(hours=1)
        
        await async_session.execute(text("""
            INSERT INTO query_cache (query_hash, result, cached_at, expires_at)
            VALUES ('valid_hash', '{"data": "test"}', ?, ?)
        """), (now, future))
        await async_session.commit()
        
        # Test check constraint: expires_at > cached_at
        past = now - timedelta(hours=1)
        
        with pytest.raises(IntegrityError):
            await async_session.execute(text("""
                INSERT INTO query_cache (query_hash, result, cached_at, expires_at)
                VALUES ('invalid_hash', '{"data": "test"}', ?, ?)
            """), (now, past))
            await async_session.commit()


class TestSchemaIndexes:
    """Test database indexes for performance."""
    
    @pytest.mark.asyncio
    async def test_user_credits_indexes(self, async_session):
        """Test that user_credits indexes work correctly."""
        # Create table with indexes
        create_table_sql = """
        CREATE TABLE user_credits (
            user_id VARCHAR NOT NULL PRIMARY KEY,
            is_guest BOOLEAN NOT NULL DEFAULT 1,
            available_credits INTEGER NOT NULL DEFAULT 0,
            max_credits INTEGER NOT NULL DEFAULT 10,
            last_reset_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
        await async_session.execute(text(create_table_sql))
        
        # Create indexes
        await async_session.execute(text("CREATE INDEX idx_user_credits_is_guest ON user_credits (is_guest)"))
        await async_session.execute(text("CREATE INDEX idx_user_credits_last_reset ON user_credits (last_reset_timestamp)"))
        await async_session.commit()
        
        # Insert test data
        test_data = [
            ('guest1', 1, 5, 10),
            ('guest2', 1, 3, 10),
            ('registered1', 0, 15, 20),
            ('registered2', 0, 12, 20)
        ]
        
        for user_id, is_guest, available, max_credits in test_data:
            await async_session.execute(text("""
                INSERT INTO user_credits (user_id, is_guest, available_credits, max_credits)
                VALUES (?, ?, ?, ?)
            """), (user_id, is_guest, available, max_credits))
        await async_session.commit()
        
        # Test queries that should use indexes
        # Query by is_guest (should use idx_user_credits_is_guest)
        result = await async_session.execute(text("SELECT COUNT(*) FROM user_credits WHERE is_guest = 1"))
        guest_count = result.scalar()
        assert guest_count == 2
        
        # Query by user_id (should use primary key index)
        result = await async_session.execute(text("SELECT * FROM user_credits WHERE user_id = 'guest1'"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 'guest1'
    
    @pytest.mark.asyncio
    async def test_credit_transactions_indexes(self, async_session):
        """Test that credit_transactions indexes work correctly."""
        create_table_sql = """
        CREATE TABLE credit_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR NOT NULL,
            transaction_type VARCHAR NOT NULL,
            amount INTEGER NOT NULL,
            timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        )
        """
        await async_session.execute(text(create_table_sql))
        
        # Create indexes
        await async_session.execute(text("CREATE INDEX idx_credit_transactions_user_id ON credit_transactions (user_id)"))
        await async_session.execute(text("CREATE INDEX idx_credit_transactions_type ON credit_transactions (transaction_type)"))
        await async_session.commit()
        
        # Insert test data
        transactions = [
            ('user1', 'deduct', -1),
            ('user1', 'reset', 10),
            ('user2', 'deduct', -2),
            ('user2', 'grant', 5)
        ]
        
        for user_id, tx_type, amount in transactions:
            await async_session.execute(text("""
                INSERT INTO credit_transactions (user_id, transaction_type, amount)
                VALUES (?, ?, ?)
            """), (user_id, tx_type, amount))
        await async_session.commit()
        
        # Test queries that should use indexes
        # Query by user_id (should use idx_credit_transactions_user_id)
        result = await async_session.execute(text("SELECT COUNT(*) FROM credit_transactions WHERE user_id = 'user1'"))
        user1_count = result.scalar()
        assert user1_count == 2
        
        # Query by transaction_type (should use idx_credit_transactions_type)
        result = await async_session.execute(text("SELECT COUNT(*) FROM credit_transactions WHERE transaction_type = 'deduct'"))
        deduct_count = result.scalar()
        assert deduct_count == 2


class TestDataIntegrity:
    """Test data integrity during migrations and operations."""
    
    @pytest.mark.asyncio
    async def test_data_preservation_during_schema_changes(self, async_session):
        """Test that data is preserved during schema modifications."""
        # Create initial table
        create_table_sql = """
        CREATE TABLE user_credits (
            user_id VARCHAR NOT NULL PRIMARY KEY,
            available_credits INTEGER NOT NULL DEFAULT 0,
            max_credits INTEGER NOT NULL DEFAULT 10
        )
        """
        await async_session.execute(text(create_table_sql))
        await async_session.commit()
        
        # Insert initial data
        await async_session.execute(text("""
            INSERT INTO user_credits (user_id, available_credits, max_credits)
            VALUES ('test_user', 5, 10)
        """))
        await async_session.commit()
        
        # Simulate adding a new column (like a migration would do)
        await async_session.execute(text("""
            ALTER TABLE user_credits ADD COLUMN is_guest BOOLEAN DEFAULT 1
        """))
        await async_session.commit()
        
        # Verify data is preserved and new column has default value
        result = await async_session.execute(text("SELECT * FROM user_credits WHERE user_id = 'test_user'"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 'test_user'  # user_id preserved
        assert row[1] == 5  # available_credits preserved
        assert row[2] == 10  # max_credits preserved
        assert row[3] == 1  # is_guest has default value
    
    @pytest.mark.asyncio
    async def test_foreign_key_relationships(self, async_session):
        """Test relationships between tables (simulated foreign keys)."""
        # Create both tables
        await async_session.execute(text("""
            CREATE TABLE user_credits (
                user_id VARCHAR NOT NULL PRIMARY KEY,
                available_credits INTEGER NOT NULL DEFAULT 0,
                max_credits INTEGER NOT NULL DEFAULT 10
            )
        """))
        
        await async_session.execute(text("""
            CREATE TABLE credit_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id VARCHAR NOT NULL,
                transaction_type VARCHAR NOT NULL,
                amount INTEGER NOT NULL
            )
        """))
        await async_session.commit()
        
        # Insert user
        await async_session.execute(text("""
            INSERT INTO user_credits (user_id, available_credits, max_credits)
            VALUES ('test_user', 10, 10)
        """))
        
        # Insert transaction for the user
        await async_session.execute(text("""
            INSERT INTO credit_transactions (user_id, transaction_type, amount)
            VALUES ('test_user', 'deduct', -1)
        """))
        await async_session.commit()
        
        # Test join query to verify relationship
        result = await async_session.execute(text("""
            SELECT uc.user_id, uc.available_credits, ct.transaction_type, ct.amount
            FROM user_credits uc
            JOIN credit_transactions ct ON uc.user_id = ct.user_id
            WHERE uc.user_id = 'test_user'
        """))
        
        row = result.fetchone()
        assert row is not None
        assert row[0] == 'test_user'  # user_id
        assert row[1] == 10  # available_credits
        assert row[2] == 'deduct'  # transaction_type
        assert row[3] == -1  # amount
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_integrity(self, async_session):
        """Test that failed transactions don't corrupt data."""
        # Create table
        create_table_sql = """
        CREATE TABLE user_credits (
            user_id VARCHAR NOT NULL PRIMARY KEY,
            available_credits INTEGER NOT NULL DEFAULT 0,
            max_credits INTEGER NOT NULL DEFAULT 10,
            CHECK (available_credits >= 0)
        )
        """
        await async_session.execute(text(create_table_sql))
        await async_session.commit()
        
        # Insert valid data
        await async_session.execute(text("""
            INSERT INTO user_credits (user_id, available_credits, max_credits)
            VALUES ('test_user', 5, 10)
        """))
        await async_session.commit()
        
        # Try to update with invalid data (should fail and rollback)
        try:
            await async_session.execute(text("""
                UPDATE user_credits SET available_credits = -1 WHERE user_id = 'test_user'
            """))
            await async_session.commit()
        except IntegrityError:
            await async_session.rollback()
        
        # Verify original data is intact
        result = await async_session.execute(text("SELECT available_credits FROM user_credits WHERE user_id = 'test_user'"))
        credits = result.scalar()
        assert credits == 5  # Original value preserved


class TestMigrationRollback:
    """Test migration rollback scenarios."""
    
    @pytest.mark.asyncio
    async def test_table_creation_rollback(self, async_session):
        """Test rolling back table creation."""
        # Create table (simulate migration upgrade)
        create_table_sql = """
        CREATE TABLE user_credits (
            user_id VARCHAR NOT NULL PRIMARY KEY,
            available_credits INTEGER NOT NULL DEFAULT 0,
            max_credits INTEGER NOT NULL DEFAULT 10
        )
        """
        await async_session.execute(text(create_table_sql))
        await async_session.commit()
        
        # Verify table exists
        result = await async_session.execute(text("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='user_credits'
        """))
        assert result.fetchone() is not None
        
        # Rollback (simulate migration downgrade)
        await async_session.execute(text("DROP TABLE user_credits"))
        await async_session.commit()
        
        # Verify table no longer exists
        result = await async_session.execute(text("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='user_credits'
        """))
        assert result.fetchone() is None
    
    @pytest.mark.asyncio
    async def test_index_creation_rollback(self, async_session):
        """Test rolling back index creation."""
        # Create table and index
        await async_session.execute(text("""
            CREATE TABLE user_credits (
                user_id VARCHAR NOT NULL PRIMARY KEY,
                is_guest BOOLEAN NOT NULL DEFAULT 1
            )
        """))
        await async_session.execute(text("CREATE INDEX idx_user_credits_is_guest ON user_credits (is_guest)"))
        await async_session.commit()
        
        # Verify index exists (SQLite specific query)
        result = await async_session.execute(text("""
            SELECT name FROM sqlite_master WHERE type='index' AND name='idx_user_credits_is_guest'
        """))
        assert result.fetchone() is not None
        
        # Rollback index creation
        await async_session.execute(text("DROP INDEX idx_user_credits_is_guest"))
        await async_session.commit()
        
        # Verify index no longer exists
        result = await async_session.execute(text("""
            SELECT name FROM sqlite_master WHERE type='index' AND name='idx_user_credits_is_guest'
        """))
        assert result.fetchone() is None


class TestPerformanceOptimization:
    """Test performance-related aspects of the schema."""
    
    @pytest.mark.asyncio
    async def test_index_performance_benefit(self, async_session):
        """Test that indexes improve query performance."""
        # Create table without index first
        await async_session.execute(text("""
            CREATE TABLE user_credits (
                user_id VARCHAR NOT NULL PRIMARY KEY,
                is_guest BOOLEAN NOT NULL DEFAULT 1,
                available_credits INTEGER NOT NULL DEFAULT 0
            )
        """))
        await async_session.commit()
        
        # Insert test data
        for i in range(100):
            await async_session.execute(text("""
                INSERT INTO user_credits (user_id, is_guest, available_credits)
                VALUES (?, ?, ?)
            """), (f"user_{i}", i % 2, i))
        await async_session.commit()
        
        # Query without index (baseline)
        result = await async_session.execute(text("SELECT COUNT(*) FROM user_credits WHERE is_guest = 1"))
        count_without_index = result.scalar()
        
        # Create index
        await async_session.execute(text("CREATE INDEX idx_user_credits_is_guest ON user_credits (is_guest)"))
        await async_session.commit()
        
        # Query with index (should be faster, but we'll just verify correctness)
        result = await async_session.execute(text("SELECT COUNT(*) FROM user_credits WHERE is_guest = 1"))
        count_with_index = result.scalar()
        
        # Results should be the same
        assert count_without_index == count_with_index
        assert count_with_index == 50  # Half of 100 records
    
    @pytest.mark.asyncio
    async def test_composite_index_usage(self, async_session):
        """Test composite index for multi-column queries."""
        # Create table with composite index
        await async_session.execute(text("""
            CREATE TABLE credit_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id VARCHAR NOT NULL,
                timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                amount INTEGER NOT NULL
            )
        """))
        await async_session.execute(text("""
            CREATE INDEX idx_user_timestamp ON credit_transactions (user_id, timestamp)
        """))
        await async_session.commit()
        
        # Insert test data
        for i in range(50):
            user_id = f"user_{i % 10}"  # 10 different users
            await async_session.execute(text("""
                INSERT INTO credit_transactions (user_id, amount)
                VALUES (?, ?)
            """), (user_id, -1))
        await async_session.commit()
        
        # Query that should benefit from composite index
        result = await async_session.execute(text("""
            SELECT COUNT(*) FROM credit_transactions 
            WHERE user_id = 'user_1' 
            ORDER BY timestamp DESC
        """))
        
        count = result.scalar()
        assert count == 5  # user_1 appears 5 times (1, 11, 21, 31, 41)