"""Initial migration: create user_credits, credit_transactions, user_consents, and query_cache tables

Revision ID: 001
Revises: 
Create Date: 2025-07-26 18:18:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_credits table
    op.create_table('user_credits',
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('is_guest', sa.Boolean(), nullable=False, default=True),
        sa.Column('available_credits', sa.Integer(), nullable=False, default=0),
        sa.Column('max_credits', sa.Integer(), nullable=False, default=10),
        sa.Column('last_reset_timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('available_credits >= 0', name='check_available_credits_non_negative'),
        sa.CheckConstraint('max_credits > 0', name='check_max_credits_positive'),
        sa.PrimaryKeyConstraint('user_id')
    )
    
    # Create indexes for user_credits
    op.create_index('idx_user_credits_user_id', 'user_credits', ['user_id'])
    op.create_index('idx_user_credits_is_guest', 'user_credits', ['is_guest'])
    op.create_index('idx_user_credits_last_reset', 'user_credits', ['last_reset_timestamp'])

    # Create credit_transactions table
    op.create_table('credit_transactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('transaction_type', sa.String(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('description', sa.Text(), nullable=True),
        sa.CheckConstraint('amount != 0', name='check_amount_non_zero'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for credit_transactions
    op.create_index('idx_credit_transactions_user_id', 'credit_transactions', ['user_id'])
    op.create_index('idx_credit_transactions_timestamp', 'credit_transactions', ['timestamp'])
    op.create_index('idx_credit_transactions_type', 'credit_transactions', ['transaction_type'])
    op.create_index('idx_credit_transactions_user_timestamp', 'credit_transactions', ['user_id', 'timestamp'])

    # Create user_consents table
    op.create_table('user_consents',
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('terms_accepted', sa.Boolean(), nullable=False, default=True),
        sa.Column('marketing_consent', sa.Boolean(), nullable=False, default=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('user_id')
    )
    
    # Create indexes for user_consents
    op.create_index('idx_user_consents_user_id', 'user_consents', ['user_id'])
    op.create_index('idx_user_consents_terms_accepted', 'user_consents', ['terms_accepted'])
    op.create_index('idx_user_consents_updated_at', 'user_consents', ['updated_at'])

    # Create query_cache table
    op.create_table('query_cache',
        sa.Column('query_hash', sa.String(), nullable=False),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('cached_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('expires_at > cached_at', name='check_expires_after_cached'),
        sa.PrimaryKeyConstraint('query_hash')
    )
    
    # Create indexes for query_cache
    op.create_index('idx_query_cache_query_hash', 'query_cache', ['query_hash'])
    op.create_index('idx_query_cache_expires_at', 'query_cache', ['expires_at'])
    op.create_index('idx_query_cache_cached_at', 'query_cache', ['cached_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('query_cache')
    op.drop_table('user_consents')
    op.drop_table('credit_transactions')
    op.drop_table('user_credits')