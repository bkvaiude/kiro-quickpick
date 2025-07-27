"""Database manager for PostgreSQL connection and migration handling."""

import logging
import asyncio
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError, OperationalError
from sqlalchemy import text
from alembic import command
from alembic.config import Config
import os

from ..config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections, sessions, and migrations with enhanced error handling."""
    
    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None
        self._initialized = False
        self._initialization_lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize the database engine and session factory with proper error handling."""
        async with self._initialization_lock:
            if self._initialized:
                return
            
            try:
                # Create async engine with optimized configuration for production
                self.engine = create_async_engine(
                    settings.database.database_url,
                    pool_size=settings.database.pool_size,
                    max_overflow=settings.database.max_overflow,
                    pool_timeout=settings.database.pool_timeout,
                    pool_recycle=settings.database.pool_recycle,
                    pool_pre_ping=settings.database.pool_pre_ping,
                    echo=settings.database.echo_sql,
                    # Optimized connection pool settings for better performance
                    pool_reset_on_return='commit',
                    # Connection arguments with performance optimizations
                    connect_args={
                        "server_settings": settings.database.server_settings,
                        "timeout": settings.database.connect_timeout,
                        "command_timeout": settings.database.command_timeout,
                        # Enable prepared statements for better performance
                        "prepared_statement_cache_size": 100,
                        "prepared_statement_name_func": lambda: f"stmt_{hash(id(object()))}"
                    },
                    # Query execution settings
                    execution_options={
                        "isolation_level": "READ_COMMITTED",
                        "autocommit": False
                    }
                )
                
                # Create session factory
                self.session_factory = async_sessionmaker(
                    self.engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                    autoflush=False,  # Manual control over flushing
                    autocommit=False
                )
                
                # Test the connection
                await self._test_connection()
                
                self._initialized = True
                logger.info(
                    f"Database manager initialized successfully - "
                    f"Pool size: {settings.database.pool_size}, "
                    f"Max overflow: {settings.database.max_overflow}"
                )
                
            except Exception as e:
                logger.error(f"Failed to initialize database manager: {e}")
                # Clean up partial initialization
                if self.engine:
                    await self.engine.dispose()
                    self.engine = None
                self.session_factory = None
                raise
    
    async def _test_connection(self):
        """Test the database connection during initialization."""
        if not self.engine:
            raise RuntimeError("Engine not initialized")
        
        async with self.engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            if result.scalar() != 1:
                raise RuntimeError("Database connection test failed")
    
    async def get_session(self) -> AsyncSession:
        """Get a new database session with automatic initialization."""
        if not self._initialized:
            await self.initialize()
        
        if not self.session_factory:
            raise RuntimeError("Session factory not initialized")
        
        return self.session_factory()
    
    async def close(self):
        """Close the database engine and cleanup resources."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database engine disposed")
        
        self.engine = None
        self.session_factory = None
        self._initialized = False
    
    def run_migrations(self):
        """Run database migrations using Alembic with enhanced error handling."""
        try:
            # Get the directory containing this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(os.path.dirname(current_dir))
            alembic_cfg_path = os.path.join(backend_dir, "alembic.ini")
            
            if not os.path.exists(alembic_cfg_path):
                raise FileNotFoundError(f"Alembic configuration not found at {alembic_cfg_path}")
            
            # Create Alembic configuration
            alembic_cfg = Config(alembic_cfg_path)
            
            # Set the database URL for migrations (convert to sync URL)
            database_url = settings.database.database_url
            if database_url.startswith("postgresql+asyncpg://"):
                database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)
            
            # Run migrations
            command.upgrade(alembic_cfg, "head")
            logger.info("Database migrations completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to run database migrations: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if the database connection is healthy with retry logic."""
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                if not self._initialized:
                    await self.initialize()
                
                session = await self.get_session()
                try:
                    # Simple query to test connection
                    result = await session.execute(text("SELECT 1"))
                    if result.scalar() == 1:
                        return True
                finally:
                    await session.close()
                    
            except (OperationalError, DisconnectionError) as e:
                logger.warning(f"Database health check attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    
            except Exception as e:
                logger.error(f"Database health check failed with unexpected error: {e}")
                return False
        
        logger.error("Database health check failed after all retries")
        return False
    
    async def get_connection_info(self) -> dict:
        """Get information about the current database connection pool."""
        if not self.engine:
            return {"status": "not_initialized"}
        
        try:
            pool = self.engine.pool
            return {
                "status": "initialized",
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                # Note: invalid() method may not be available on all pool types
                "pool_type": type(pool).__name__
            }
        except Exception as e:
            logger.warning(f"Could not get detailed pool info: {e}")
            return {
                "status": "initialized",
                "pool_type": type(self.engine.pool).__name__ if self.engine.pool else "unknown",
                "error": str(e)
            }


# Global database manager instance
database_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection function for FastAPI to get database sessions.
    Provides proper transaction management and error handling.
    """
    session = await database_manager.get_session()
    try:
        yield session
        # Commit any pending transactions if no exception occurred
        if session.in_transaction():
            await session.commit()
    except SQLAlchemyError as e:
        # Rollback on database errors
        if session.in_transaction():
            await session.rollback()
        logger.error(f"Database error in session: {e}")
        raise
    except Exception as e:
        # Rollback on any other errors
        if session.in_transaction():
            await session.rollback()
        logger.error(f"Unexpected error in database session: {e}")
        raise
    finally:
        await session.close()


async def get_db_session_with_retry() -> AsyncGenerator[AsyncSession, None]:
    """
    Enhanced dependency injection with retry logic for transient failures.
    Use this for critical operations that need higher reliability.
    """
    max_retries = 3
    retry_delay = 0.1
    
    for attempt in range(max_retries):
        try:
            async for session in get_db_session():
                yield session
                return  # Success, exit retry loop
        except (OperationalError, DisconnectionError) as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database session attempt {attempt + 1} failed, retrying: {e}")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"Database session failed after {max_retries} attempts: {e}")
                raise
        except Exception:
            # Don't retry on non-transient errors
            raise


class DatabaseSessionManager:
    """Context manager for database sessions with enhanced lifecycle management."""
    
    def __init__(self, database_manager: DatabaseManager):
        self.database_manager = database_manager
        self.session: Optional[AsyncSession] = None
    
    async def __aenter__(self) -> AsyncSession:
        """Enter the async context and create a new session."""
        self.session = await self.database_manager.get_session()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context and handle session cleanup."""
        if self.session:
            try:
                if exc_type is None:
                    # No exception occurred, commit the transaction
                    if self.session.in_transaction():
                        await self.session.commit()
                else:
                    # Exception occurred, rollback the transaction
                    if self.session.in_transaction():
                        await self.session.rollback()
                    logger.error(f"Session rolled back due to exception: {exc_type.__name__}: {exc_val}")
            except Exception as cleanup_error:
                logger.error(f"Error during session cleanup: {cleanup_error}")
            finally:
                await self.session.close()
                self.session = None


class TransactionalSessionManager:
    """Context manager for explicit transaction management."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._transaction_started = False
    
    async def __aenter__(self) -> AsyncSession:
        """Begin a new transaction."""
        if not self.session.in_transaction():
            await self.session.begin()
            self._transaction_started = True
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Handle transaction completion."""
        if self._transaction_started and self.session.in_transaction():
            try:
                if exc_type is None:
                    await self.session.commit()
                    logger.debug("Transaction committed successfully")
                else:
                    await self.session.rollback()
                    logger.warning(f"Transaction rolled back due to: {exc_type.__name__}: {exc_val}")
            except Exception as e:
                logger.error(f"Error during transaction cleanup: {e}")
                try:
                    await self.session.rollback()
                except Exception as rollback_error:
                    logger.error(f"Failed to rollback transaction: {rollback_error}")


def create_session_context() -> DatabaseSessionManager:
    """Factory function to create a new session context manager."""
    return DatabaseSessionManager(database_manager)


def with_transaction(session: AsyncSession) -> TransactionalSessionManager:
    """Create a transaction context manager for an existing session."""
    return TransactionalSessionManager(session)