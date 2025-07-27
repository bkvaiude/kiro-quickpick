"""Performance optimization: add composite indexes and optimize existing ones

Revision ID: 002
Revises: 001
Create Date: 2025-07-26 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance optimizations including composite indexes and query-specific indexes."""
    
    # === Credit Transactions Optimizations ===
    
    # Composite index for user_id + timestamp (most common query pattern)
    # This optimizes queries that filter by user and order by timestamp
    op.create_index(
        'idx_credit_transactions_user_timestamp_desc',
        'credit_transactions',
        ['user_id', sa.text('timestamp DESC')],
        postgresql_using='btree'
    )
    
    # Composite index for user_id + transaction_type + timestamp
    # This optimizes filtered queries by transaction type
    op.create_index(
        'idx_credit_transactions_user_type_timestamp',
        'credit_transactions',
        ['user_id', 'transaction_type', sa.text('timestamp DESC')],
        postgresql_using='btree'
    )
    
    # Index for cleanup operations (timestamp-based cleanup)
    # Note: Using a partial index for old transactions (older than 3 months)
    op.create_index(
        'idx_credit_transactions_timestamp_desc',
        'credit_transactions',
        [sa.text('timestamp DESC')],
        postgresql_using='btree'
    )
    
    # === User Credits Optimizations ===
    
    # Composite index for credit reset operations
    op.create_index(
        'idx_user_credits_reset_lookup',
        'user_credits',
        ['last_reset_timestamp', 'is_guest'],
        postgresql_using='btree'
    )
    
    # Index for guest user queries (frequently accessed)
    op.create_index(
        'idx_user_credits_guest_credits',
        'user_credits',
        ['is_guest', 'available_credits'],
        postgresql_using='btree'
    )
    
    # === User Consents Optimizations ===
    
    # Composite index for consent analytics queries
    op.create_index(
        'idx_user_consents_analytics',
        'user_consents',
        ['terms_accepted', 'marketing_consent', 'updated_at'],
        postgresql_using='btree'
    )
    
    # Index for recent consent changes (time-based queries)
    op.create_index(
        'idx_user_consents_updated_at_desc',
        'user_consents',
        [sa.text('updated_at DESC')],
        postgresql_using='btree'
    )
    
    # === Query Cache Optimizations ===
    
    # Composite index for cache cleanup operations
    op.create_index(
        'idx_query_cache_cleanup',
        'query_cache',
        ['expires_at', 'cached_at'],
        postgresql_using='btree'
    )
    
    # Index for active cache entries lookup
    op.create_index(
        'idx_query_cache_hash_expires',
        'query_cache',
        ['query_hash', 'expires_at'],
        postgresql_using='btree'
    )
    
    # Index for cache size management (oldest entries first)
    op.create_index(
        'idx_query_cache_size_management',
        'query_cache',
        [sa.text('cached_at ASC')],
        postgresql_using='btree'
    )
    
    # === Statistics and Analytics Indexes ===
    
    # Index for transaction statistics (timestamp + type for analytics)
    op.create_index(
        'idx_credit_transactions_timestamp_type',
        'credit_transactions',
        ['timestamp', 'transaction_type'],
        postgresql_using='btree'
    )
    
    # Index for consent analytics (updated_at + consent flags)
    op.create_index(
        'idx_user_consents_updated_consents',
        'user_consents',
        ['updated_at', 'terms_accepted', 'marketing_consent'],
        postgresql_using='btree'
    )


def downgrade() -> None:
    """Remove performance optimization indexes."""
    
    # Drop all the indexes we created (in reverse order)
    op.drop_index('idx_user_consents_updated_consents', table_name='user_consents')
    op.drop_index('idx_credit_transactions_timestamp_type', table_name='credit_transactions')
    op.drop_index('idx_query_cache_size_management', table_name='query_cache')
    op.drop_index('idx_query_cache_hash_expires', table_name='query_cache')
    op.drop_index('idx_query_cache_cleanup', table_name='query_cache')
    op.drop_index('idx_user_consents_updated_at_desc', table_name='user_consents')
    op.drop_index('idx_user_consents_analytics', table_name='user_consents')
    op.drop_index('idx_user_credits_guest_credits', table_name='user_credits')
    op.drop_index('idx_user_credits_reset_lookup', table_name='user_credits')
    op.drop_index('idx_credit_transactions_timestamp_desc', table_name='credit_transactions')
    op.drop_index('idx_credit_transactions_user_type_timestamp', table_name='credit_transactions')
    op.drop_index('idx_credit_transactions_user_timestamp_desc', table_name='credit_transactions')