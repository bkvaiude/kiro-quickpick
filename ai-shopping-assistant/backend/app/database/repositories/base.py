"""Base repository class with common database operations and transaction management."""

import logging
from typing import TypeVar, Generic, Type, Optional, List, Any, Dict, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import DeclarativeBase

from ..base import Base

logger = logging.getLogger(__name__)

# Type variable for model classes
ModelType = TypeVar("ModelType", bound=Base)


class RepositoryError(Exception):
    """Base exception for repository operations."""
    pass


class RepositoryIntegrityError(RepositoryError):
    """Exception raised when database integrity constraints are violated."""
    pass


class RepositoryOperationalError(RepositoryError):
    """Exception raised when database operational errors occur."""
    pass


class BaseRepository(Generic[ModelType]):
    """
    Base repository class providing common database operations.
    
    This class provides:
    - Common CRUD operations
    - Transaction management methods
    - Error handling patterns
    - Query utilities
    """
    
    def __init__(self, session: AsyncSession, model_class: Type[ModelType]):
        """
        Initialize the repository with a database session and model class.
        
        Args:
            session: Async SQLAlchemy session
            model_class: The SQLAlchemy model class this repository manages
        """
        self.session = session
        self.model_class = model_class
    
    async def commit(self) -> None:
        """
        Commit the current transaction.
        
        Raises:
            RepositoryError: If commit fails
        """
        try:
            await self.session.commit()
            logger.debug(f"Transaction committed for {self.model_class.__name__}")
        except SQLAlchemyError as e:
            logger.error(f"Failed to commit transaction for {self.model_class.__name__}: {e}")
            await self.rollback()
            raise RepositoryError(f"Failed to commit transaction: {e}") from e
    
    async def rollback(self) -> None:
        """
        Rollback the current transaction.
        
        Raises:
            RepositoryError: If rollback fails
        """
        try:
            await self.session.rollback()
            logger.debug(f"Transaction rolled back for {self.model_class.__name__}")
        except SQLAlchemyError as e:
            logger.error(f"Failed to rollback transaction for {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Failed to rollback transaction: {e}") from e
    
    async def flush(self) -> None:
        """
        Flush pending changes to the database without committing.
        
        Raises:
            RepositoryError: If flush fails
        """
        try:
            await self.session.flush()
            logger.debug(f"Session flushed for {self.model_class.__name__}")
        except SQLAlchemyError as e:
            logger.error(f"Failed to flush session for {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Failed to flush session: {e}") from e
    
    async def refresh(self, instance: ModelType) -> ModelType:
        """
        Refresh an instance from the database.
        
        Args:
            instance: The model instance to refresh
            
        Returns:
            The refreshed instance
            
        Raises:
            RepositoryError: If refresh fails
        """
        try:
            await self.session.refresh(instance)
            return instance
        except SQLAlchemyError as e:
            logger.error(f"Failed to refresh {self.model_class.__name__} instance: {e}")
            raise RepositoryError(f"Failed to refresh instance: {e}") from e
    
    async def create(self, instance: ModelType) -> ModelType:
        """
        Create a new instance in the database.
        
        Args:
            instance: The model instance to create
            
        Returns:
            The created instance
            
        Raises:
            RepositoryIntegrityError: If integrity constraints are violated
            RepositoryError: If creation fails
        """
        try:
            self.session.add(instance)
            await self.flush()
            await self.refresh(instance)
            logger.debug(f"Created {self.model_class.__name__} instance")
            return instance
        except IntegrityError as e:
            logger.warning(f"Integrity error creating {self.model_class.__name__}: {e}")
            await self.rollback()
            raise RepositoryIntegrityError(f"Integrity constraint violation: {e}") from e
        except SQLAlchemyError as e:
            logger.error(f"Failed to create {self.model_class.__name__}: {e}")
            await self.rollback()
            raise RepositoryError(f"Failed to create instance: {e}") from e
    
    async def get_by_id(self, id_value: Any) -> Optional[ModelType]:
        """
        Get an instance by its primary key.
        
        Args:
            id_value: The primary key value
            
        Returns:
            The instance if found, None otherwise
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            result = await self.session.get(self.model_class, id_value)
            if result:
                logger.debug(f"Found {self.model_class.__name__} with id: {id_value}")
            else:
                logger.debug(f"No {self.model_class.__name__} found with id: {id_value}")
            return result
        except SQLAlchemyError as e:
            logger.error(f"Failed to get {self.model_class.__name__} by id {id_value}: {e}")
            raise RepositoryError(f"Failed to get instance by id: {e}") from e
    
    async def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[ModelType]:
        """
        Get all instances with optional pagination.
        
        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of instances
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            query = select(self.model_class)
            
            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)
            
            result = await self.session.execute(query)
            instances = result.scalars().all()
            logger.debug(f"Retrieved {len(instances)} {self.model_class.__name__} instances")
            return list(instances)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get all {self.model_class.__name__} instances: {e}")
            raise RepositoryError(f"Failed to get all instances: {e}") from e
    
    async def update_by_id(self, id_value: Any, **updates) -> Optional[ModelType]:
        """
        Update an instance by its primary key.
        
        Args:
            id_value: The primary key value
            **updates: Fields to update
            
        Returns:
            The updated instance if found, None otherwise
            
        Raises:
            RepositoryIntegrityError: If integrity constraints are violated
            RepositoryError: If update fails
        """
        try:
            # Get the primary key column name
            primary_key = self.model_class.__table__.primary_key.columns.keys()[0]
            
            # Build update query
            query = (
                update(self.model_class)
                .where(getattr(self.model_class, primary_key) == id_value)
                .values(**updates)
                .returning(self.model_class)
            )
            
            result = await self.session.execute(query)
            updated_instance = result.scalar_one_or_none()
            
            if updated_instance:
                await self.flush()
                logger.debug(f"Updated {self.model_class.__name__} with id: {id_value}")
            else:
                logger.debug(f"No {self.model_class.__name__} found to update with id: {id_value}")
            
            return updated_instance
        except IntegrityError as e:
            logger.warning(f"Integrity error updating {self.model_class.__name__}: {e}")
            await self.rollback()
            raise RepositoryIntegrityError(f"Integrity constraint violation: {e}") from e
        except SQLAlchemyError as e:
            logger.error(f"Failed to update {self.model_class.__name__} with id {id_value}: {e}")
            await self.rollback()
            raise RepositoryError(f"Failed to update instance: {e}") from e
    
    async def delete_by_id(self, id_value: Any) -> bool:
        """
        Delete an instance by its primary key.
        
        Args:
            id_value: The primary key value
            
        Returns:
            True if instance was deleted, False if not found
            
        Raises:
            RepositoryError: If deletion fails
        """
        try:
            # Get the primary key column name
            primary_key = self.model_class.__table__.primary_key.columns.keys()[0]
            
            # Build delete query
            query = delete(self.model_class).where(getattr(self.model_class, primary_key) == id_value)
            
            result = await self.session.execute(query)
            deleted_count = result.rowcount
            
            if deleted_count > 0:
                await self.flush()
                logger.debug(f"Deleted {self.model_class.__name__} with id: {id_value}")
                return True
            else:
                logger.debug(f"No {self.model_class.__name__} found to delete with id: {id_value}")
                return False
        except SQLAlchemyError as e:
            logger.error(f"Failed to delete {self.model_class.__name__} with id {id_value}: {e}")
            await self.rollback()
            raise RepositoryError(f"Failed to delete instance: {e}") from e
    
    async def count(self, **filters) -> int:
        """
        Count instances with optional filters.
        
        Args:
            **filters: Filter conditions
            
        Returns:
            Number of matching instances
            
        Raises:
            RepositoryError: If count fails
        """
        try:
            query = select(func.count()).select_from(self.model_class)
            
            # Apply filters
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    query = query.where(getattr(self.model_class, field) == value)
            
            result = await self.session.execute(query)
            count = result.scalar()
            logger.debug(f"Counted {count} {self.model_class.__name__} instances with filters: {filters}")
            return count
        except SQLAlchemyError as e:
            logger.error(f"Failed to count {self.model_class.__name__} instances: {e}")
            raise RepositoryError(f"Failed to count instances: {e}") from e
    
    async def exists(self, **filters) -> bool:
        """
        Check if any instances exist with the given filters.
        
        Args:
            **filters: Filter conditions
            
        Returns:
            True if at least one instance exists, False otherwise
            
        Raises:
            RepositoryError: If existence check fails
        """
        try:
            query = select(self.model_class)
            
            # Apply filters
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    query = query.where(getattr(self.model_class, field) == value)
            
            # Use exists() for better performance
            query = select(query.exists())
            
            result = await self.session.execute(query)
            exists = result.scalar()
            logger.debug(f"{self.model_class.__name__} exists with filters {filters}: {exists}")
            return exists
        except SQLAlchemyError as e:
            logger.error(f"Failed to check {self.model_class.__name__} existence: {e}")
            raise RepositoryError(f"Failed to check existence: {e}") from e
    
    async def find_by(self, limit: Optional[int] = None, offset: Optional[int] = None, **filters) -> List[ModelType]:
        """
        Find instances by filter conditions.
        
        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip
            **filters: Filter conditions
            
        Returns:
            List of matching instances
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            query = select(self.model_class)
            
            # Apply filters
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    query = query.where(getattr(self.model_class, field) == value)
            
            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)
            
            result = await self.session.execute(query)
            instances = result.scalars().all()
            logger.debug(f"Found {len(instances)} {self.model_class.__name__} instances with filters: {filters}")
            return list(instances)
        except SQLAlchemyError as e:
            logger.error(f"Failed to find {self.model_class.__name__} instances: {e}")
            raise RepositoryError(f"Failed to find instances: {e}") from e
    
    async def find_one_by(self, **filters) -> Optional[ModelType]:
        """
        Find a single instance by filter conditions.
        
        Args:
            **filters: Filter conditions
            
        Returns:
            The matching instance if found, None otherwise
            
        Raises:
            RepositoryError: If query fails or multiple instances found
        """
        try:
            query = select(self.model_class)
            
            # Apply filters
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    query = query.where(getattr(self.model_class, field) == value)
            
            result = await self.session.execute(query)
            instance = result.scalar_one_or_none()
            
            if instance:
                logger.debug(f"Found {self.model_class.__name__} instance with filters: {filters}")
            else:
                logger.debug(f"No {self.model_class.__name__} found with filters: {filters}")
            
            return instance
        except SQLAlchemyError as e:
            logger.error(f"Failed to find {self.model_class.__name__} instance: {e}")
            raise RepositoryError(f"Failed to find instance: {e}") from e
    
    def _handle_database_error(self, error: Exception, operation: str) -> None:
        """
        Handle database errors with appropriate logging and exception conversion.
        
        Args:
            error: The original exception
            operation: Description of the operation that failed
        """
        if isinstance(error, IntegrityError):
            logger.warning(f"Integrity error during {operation}: {error}")
            raise RepositoryIntegrityError(f"Integrity constraint violation during {operation}: {error}") from error
        elif isinstance(error, OperationalError):
            logger.error(f"Operational error during {operation}: {error}")
            raise RepositoryOperationalError(f"Database operational error during {operation}: {error}") from error
        elif isinstance(error, SQLAlchemyError):
            logger.error(f"Database error during {operation}: {error}")
            raise RepositoryError(f"Database error during {operation}: {error}") from error
        else:
            logger.error(f"Unexpected error during {operation}: {error}")
            raise RepositoryError(f"Unexpected error during {operation}: {error}") from error