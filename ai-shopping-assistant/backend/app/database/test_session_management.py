"""Tests for database session management."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from .manager import (
    DatabaseManager, 
    DatabaseSessionManager, 
    TransactionalSessionManager,
    get_db_session,
    create_session_context,
    with_transaction
)


class TestDatabaseManager:
    """Test cases for DatabaseManager."""
    
    @pytest.fixture
    def db_manager(self):
        """Create a DatabaseManager instance for testing."""
        return DatabaseManager()
    
    @pytest.mark.asyncio
    async def test_initialization(self, db_manager):
        """Test database manager initialization."""
        with patch('app.database.manager.create_async_engine') as mock_engine, \
             patch('app.database.manager.async_sessionmaker') as mock_sessionmaker:
            
            mock_engine_instance = AsyncMock()
            mock_engine.return_value = mock_engine_instance
            mock_sessionmaker_instance = AsyncMock()
            mock_sessionmaker.return_value = mock_sessionmaker_instance
            
            # Mock the connection test
            mock_conn = AsyncMock()
            mock_result = AsyncMock()
            mock_result.scalar.return_value = 1
            mock_conn.execute.return_value = mock_result
            mock_engine_instance.begin.return_value.__aenter__.return_value = mock_conn
            
            await db_manager.initialize()
            
            assert db_manager._initialized is True
            assert db_manager.engine is not None
            assert db_manager.session_factory is not None
            mock_engine.assert_called_once()
            mock_sessionmaker.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_session_auto_initialize(self, db_manager):
        """Test that get_session automatically initializes if needed."""
        with patch.object(db_manager, 'initialize') as mock_init, \
             patch.object(db_manager, 'session_factory') as mock_factory:
            
            mock_session = AsyncMock()
            mock_factory.return_value = mock_session
            db_manager._initialized = False
            
            result = await db_manager.get_session()
            
            mock_init.assert_called_once()
            assert result == mock_session
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, db_manager):
        """Test successful health check."""
        with patch.object(db_manager, 'get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_result = AsyncMock()
            mock_result.scalar.return_value = 1
            mock_session.execute.return_value = mock_result
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            db_manager._initialized = True
            result = await db_manager.health_check()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, db_manager):
        """Test health check failure with retry logic."""
        with patch.object(db_manager, 'get_session') as mock_get_session:
            mock_get_session.side_effect = OperationalError("Connection failed", None, None)
            db_manager._initialized = True
            
            result = await db_manager.health_check()
            
            assert result is False
            # Should retry 3 times
            assert mock_get_session.call_count == 3
    
    @pytest.mark.asyncio
    async def test_close(self, db_manager):
        """Test database manager cleanup."""
        mock_engine = AsyncMock()
        db_manager.engine = mock_engine
        db_manager._initialized = True
        
        await db_manager.close()
        
        mock_engine.dispose.assert_called_once()
        assert db_manager.engine is None
        assert db_manager.session_factory is None
        assert db_manager._initialized is False


class TestDatabaseSessionManager:
    """Test cases for DatabaseSessionManager."""
    
    @pytest.mark.asyncio
    async def test_successful_context(self):
        """Test successful session context management."""
        mock_db_manager = AsyncMock()
        mock_session = AsyncMock()
        mock_session.in_transaction.return_value = True
        mock_db_manager.get_session.return_value = mock_session
        
        session_manager = DatabaseSessionManager(mock_db_manager)
        
        async with session_manager as session:
            assert session == mock_session
        
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_exception_rollback(self):
        """Test session rollback on exception."""
        mock_db_manager = AsyncMock()
        mock_session = AsyncMock()
        mock_session.in_transaction.return_value = True
        mock_db_manager.get_session.return_value = mock_session
        
        session_manager = DatabaseSessionManager(mock_db_manager)
        
        try:
            async with session_manager as session:
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.commit.assert_not_called()


class TestTransactionalSessionManager:
    """Test cases for TransactionalSessionManager."""
    
    @pytest.mark.asyncio
    async def test_transaction_commit(self):
        """Test successful transaction commit."""
        mock_session = AsyncMock()
        mock_session.in_transaction.return_value = False  # Initially not in transaction
        
        transaction_manager = TransactionalSessionManager(mock_session)
        
        async with transaction_manager as session:
            mock_session.in_transaction.return_value = True  # Now in transaction
            assert session == mock_session
        
        mock_session.begin.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self):
        """Test transaction rollback on exception."""
        mock_session = AsyncMock()
        mock_session.in_transaction.return_value = False  # Initially not in transaction
        
        transaction_manager = TransactionalSessionManager(mock_session)
        
        try:
            async with transaction_manager as session:
                mock_session.in_transaction.return_value = True  # Now in transaction
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        mock_session.begin.assert_called_once()
        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()


class TestDependencyInjection:
    """Test cases for FastAPI dependency injection functions."""
    
    @pytest.mark.asyncio
    async def test_get_db_session_success(self):
        """Test successful database session dependency."""
        with patch('app.database.manager.database_manager') as mock_manager:
            mock_session = AsyncMock()
            mock_session.in_transaction.return_value = True
            mock_manager.get_session.return_value = mock_session
            
            async for session in get_db_session():
                assert session == mock_session
                break
            
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_db_session_rollback(self):
        """Test database session rollback on error."""
        with patch('app.database.manager.database_manager') as mock_manager:
            mock_session = AsyncMock()
            mock_session.in_transaction.return_value = True
            mock_manager.get_session.return_value = mock_session
            
            try:
                async for session in get_db_session():
                    raise SQLAlchemyError("Test error")
            except SQLAlchemyError:
                pass
            
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
            mock_session.commit.assert_not_called()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])