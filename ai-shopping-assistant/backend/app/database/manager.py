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
                # Configure connection arguments based on prepared statement cache setting
                connect_args = {
                    "server_settings": settings.database.server_settings,
                    "timeout": settings.database.connect_timeout,
                    "command_timeout": settings.database.command_timeout,
                }
                
                # Determine prepared statement cache size
                cache_size = settings.database.prepared_statement_cache_size
                
                if cache_size == -1:
                    # Auto-detect based on connection string
                    is_pgbouncer = (
                        ":5433/" in settings.database.database_url or 
                        ":6432/" in settings.database.database_url or
                        "pgbouncer" in settings.database.database_url.lower()
                    )
                    cache_size = 0 if is_pgbouncer else 100
                    logger.info(f"Auto-detected prepared statement cache size: {cache_size} (pgbouncer: {is_pgbouncer})")
                else:
                    logger.info(f"Using configured prepared statement cache size: {cache_size}")
                
                if cache_size > 0:
                    # Enable prepared statements
                    connect_args.update({
                        "prepared_statement_cache_size": cache_size,
                        "prepared_statement_name_func": lambda: f"stmt_{hash(id(object()))}"
                    })
                    logger.info("Prepared statement caching enabled")
                else:
                    # Disable prepared statements (pgbouncer compatibility)
                    connect_args["prepared_statement_cache_size"] = 0
                    logger.info("Prepared statement caching disabled for pgbouncer compatibility")
                
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
                    # Connection arguments with pgbouncer compatibility
                    connect_args=connect_args,
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
        import io
        import sys
        import signal
        import threading
        from contextlib import redirect_stdout, redirect_stderr
        
        # Save current logging configuration before Alembic messes with it
        original_handlers = logging.root.handlers[:]
        original_level = logging.root.level
        
        try:
            # Get the directory containing this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(os.path.dirname(current_dir))
            alembic_cfg_path = os.path.join(backend_dir, "alembic.ini")
            
            if not os.path.exists(alembic_cfg_path):
                raise FileNotFoundError(f"Alembic configuration not found at {alembic_cfg_path}")
            
            logger.info(f"🚀 Starting database migrations using config: {alembic_cfg_path}")
            
            # Create Alembic configuration
            alembic_cfg = Config(alembic_cfg_path)
            
            # Disable Alembic's logging configuration to prevent it from overriding ours
            alembic_cfg.set_main_option("configure_logger", "false")
            
            # Set the database URL for migrations (convert to sync URL)
            database_url = settings.database.database_url
            if database_url.startswith("postgresql+asyncpg://"):
                database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)
            
            logger.info(f"📊 Database URL configured: {database_url[:50]}...")
            
            # Check if migrations are needed
            try:
                from alembic.script import ScriptDirectory
                from alembic.runtime.environment import EnvironmentContext
                from alembic.runtime.migration import MigrationContext
                from sqlalchemy import create_engine
                
                logger.info("🔍 Checking if migrations are needed...")
                
                # Create sync engine for Alembic checks
                sync_engine = create_engine(database_url)
                script = ScriptDirectory.from_config(alembic_cfg)
                
                with sync_engine.connect() as connection:
                    context = MigrationContext.configure(connection)
                    current_rev = context.get_current_revision()
                    head_rev = script.get_current_head()
                    
                    logger.info(f"📍 Current revision: {current_rev}")
                    logger.info(f"🎯 Head revision: {head_rev}")
                    
                    if current_rev == head_rev:
                        logger.info("✅ Database is already up to date - no migrations needed!")
                        # Restore logging immediately and return
                        logging.root.handlers = original_handlers
                        logging.root.level = original_level
                        return
                    
                    logger.info(f"🔄 Need to migrate from {current_rev} to {head_rev}")
                
                sync_engine.dispose()
                
            except Exception as check_error:
                logger.warning(f"⚠️ Could not check migration status: {check_error}")
                logger.info("🤷 Proceeding with migration attempt anyway...")
            
            logger.info("⚡ Executing Alembic upgrade to head...")
            
            # Force flush logs before Alembic
            for handler in logging.root.handlers:
                handler.flush()
            
            # Capture Alembic output
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            try:
                logger.info("🔄 About to call command.upgrade...")
                sys.stdout.flush()
                sys.stderr.flush()
                
                # Add timeout mechanism
                def run_alembic():
                    with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                        command.upgrade(alembic_cfg, "head")
                
                # Run with timeout
                alembic_thread = threading.Thread(target=run_alembic)
                alembic_thread.daemon = True
                alembic_thread.start()
                alembic_thread.join(timeout=10)  # 60 second timeout
                
                if alembic_thread.is_alive():
                    logger.error("⏰ Alembic command timed out after 60 seconds!")
                    raise TimeoutError("Alembic migration timed out")
                
                logger.info("🎯 command.upgrade completed, processing output...")
                
                # Force restore logging configuration IMMEDIATELY
                logging.root.handlers = original_handlers
                logging.root.level = original_level
                
                # Get captured output
                stdout_output = stdout_capture.getvalue().strip()
                stderr_output = stderr_capture.getvalue().strip()
                
                # Log the results (after restoring logging)
                if stdout_output:
                    logger.info(f"📝 Alembic output:\n{stdout_output}")
                else:
                    logger.info("📝 Alembic produced no stdout output")
                    
                if stderr_output:
                    logger.warning(f"⚠️ Alembic warnings:\n{stderr_output}")
                else:
                    logger.info("📝 Alembic produced no stderr output")
                
                logger.info("✅ Database migrations completed successfully!")
                
            except Exception as alembic_error:
                # Restore logging first
                logging.root.handlers = original_handlers
                logging.root.level = original_level
                
                # Log any captured output
                stdout_output = stdout_capture.getvalue().strip()
                stderr_output = stderr_capture.getvalue().strip()
                
                if stdout_output:
                    logger.error(f"📝 Alembic output before error:\n{stdout_output}")
                if stderr_output:
                    logger.error(f"❌ Alembic error output:\n{stderr_output}")
                
                logger.error(f"💥 Alembic command failed: {alembic_error}")
                raise alembic_error
                
        except Exception as e:
            # Ensure logging is restored even on outer exceptions
            logging.root.handlers = original_handlers
            logging.root.level = original_level
            
            logger.error(f"❌ Migration process failed: {e}")
            logger.error(f"🔍 Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"📋 Full traceback:\n{traceback.format_exc()}")
            raise
        finally:
            # Final safety net to restore logging
            logging.root.handlers = original_handlers
            logging.root.level = original_level
    
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