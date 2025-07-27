# Implementation Plan

- [x] 1. Set up PostgreSQL dependencies and configuration
  - Add SQLAlchemy, asyncpg, and Alembic to requirements.txt
  - Create database configuration class in config.py
  - Add database environment variables to .env files
  - _Requirements: 4.1, 5.1_

- [x] 2. Create database models and schema
  - [x] 2.1 Create SQLAlchemy base model and database models
    - Implement Base class and database table models for user_credits, credit_transactions, user_consents, and query_cache
    - Add proper indexes, constraints, and relationships
    - _Requirements: 1.2, 2.2, 3.1_

  - [x] 2.2 Set up Alembic migration system
    - Initialize Alembic configuration
    - Create initial migration scripts for all tables
    - Implement migration runner for application startup
    - _Requirements: 4.1, 4.2, 4.3_

- [x] 3. Implement database connection and session management
  - [x] 3.1 Create database manager and connection pooling
    - Implement DatabaseManager class with async engine and session factory
    - Configure connection pooling with proper settings
    - Add database dependency injection for FastAPI
    - _Requirements: 5.1, 5.2_

  - [x] 3.2 Implement database session lifecycle management
    - Create async session context managers
    - Add proper transaction handling and rollback logic
    - Implement database health checks
    - _Requirements: 5.2, 5.3_

- [x] 4. Create repository layer for data access
  - [x] 4.1 Implement base repository class
    - Create BaseRepository with common database operations
    - Add transaction management methods
    - Implement error handling patterns
    - _Requirements: 6.1, 5.4_

  - [x] 4.2 Create CreditRepository for credit operations
    - Implement CRUD operations for user credits
    - Add credit transaction logging methods
    - Create transaction history retrieval methods
    - Add cleanup methods for old transactions
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 4.3 Create ConsentRepository for user consent operations
    - Implement CRUD operations for user consent records
    - Add consent history tracking
    - Create batch consent retrieval methods
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 4.4 Create CacheRepository for query cache operations
    - Implement cache storage and retrieval methods
    - Add automatic expiration handling
    - Create cache cleanup and maintenance methods
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 5. Migrate CreditService to use PostgreSQL
  - [x] 5.1 Update CreditService to use CreditRepository
    - Replace in-memory storage with database repository calls
    - Maintain existing public interface methods
    - Add proper error handling and transaction management
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 6.1, 6.3_

  - [x] 5.2 Update credit middleware to work with database
    - Modify credit_middleware.py to use async database operations
    - Ensure proper session management in middleware
    - Add error handling for database connectivity issues
    - _Requirements: 6.1, 6.3, 5.3_

- [x] 6. Migrate UserConsentService to use PostgreSQL
  - Replace in-memory storage with ConsentRepository
  - Maintain existing service interface
  - Add proper async/await patterns for database operations
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 6.1, 6.3_

- [x] 7. Migrate QueryCacheService to use PostgreSQL
  - Replace in-memory cache with CacheRepository
  - Implement automatic cache expiration cleanup
  - Add cache statistics tracking in database
  - Maintain existing service interface
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 6.1, 6.3_

- [x] 8. Update application startup and configuration
  - [x] 8.1 Add database initialization to application startup
    - Run database migrations on application start
    - Initialize database connection pool
    - Add database health checks to startup sequence
    - _Requirements: 4.1, 4.3, 5.1_
 
  - [x] 8.2 Update Docker configuration for PostgreSQL
    - Add PostgreSQL service to docker-compose.yml
    - Update environment variables for database connection
    - Add database initialization scripts
    - _Requirements: 4.1, 5.1_

- [x] 9. Create comprehensive tests for database integration
  - [x] 9.1 Write repository unit tests
    - Create tests for all repository CRUD operations
    - Test error handling and constraint violations
    - Add tests for transaction rollback scenarios
    - _Requirements: 6.2_

  - [x] 9.2 Write service integration tests
    - Update existing service tests to work with database
    - Add tests for database connectivity issues
    - Test concurrent access patterns
    - _Requirements: 6.2_

  - [x] 9.3 Create migration and schema tests
    - Test database migration upgrade and downgrade
    - Verify schema constraints and indexes
    - Test data integrity during migrations
    - _Requirements: 4.2, 4.4_

- [x] 10. Add database monitoring and maintenance
  - [x] 10.1 Implement database health monitoring
    - Add health check endpoints for database connectivity
    - Create connection pool monitoring
    - Add database performance metrics
    - _Requirements: 5.3, 5.4_

  - [x] 10.2 Create database maintenance tasks
    - Implement automatic cleanup of expired cache entries
    - Add transaction history cleanup job
    - Create database backup and recovery procedures
    - _Requirements: 3.4, 1.4_

- [x] 11. Update API endpoints and error handling
  - Ensure all API endpoints work with async database operations
  - Update error handling to properly handle database errors
  - Add proper HTTP status codes for database-related errors
  - Verify API response formats remain unchanged
  - _Requirements: 6.3, 6.4, 5.4_

- [x] 12. Performance optimization and final testing
  - [x] 12.1 Optimize database queries and indexes
    - Analyze query performance and add missing indexes
    - Optimize batch operations for better performance
    - Configure connection pool settings for production
    - _Requirements: 5.1, 5.2_

  - [x] 12.2 Run comprehensive end-to-end tests
    - Test full application functionality with PostgreSQL
    - Verify data persistence across application restarts
    - Test error scenarios and recovery procedures
    - Validate performance under load
    - _Requirements: 6.2, 6.4_