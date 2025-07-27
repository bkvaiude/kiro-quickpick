"""SQLAlchemy database models for PostgreSQL migration."""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, JSON,
    CheckConstraint, Index, func
)
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base


class UserCreditsDB(Base):
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


class CreditTransactionDB(Base):
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


class UserConsentDB(Base):
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


class QueryCacheDB(Base):
    """Database model for query cache storage."""
    
    __tablename__ = "query_cache"
    
    # Primary key
    query_hash = Column(String, primary_key=True, nullable=False)
    
    # Cache data
    result = Column(JSONB, nullable=False)  # Use JSONB for better performance in PostgreSQL
    
    # Timestamp tracking
    cached_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint('expires_at > cached_at', name='check_expires_after_cached'),
        Index('idx_query_cache_query_hash', 'query_hash'),
        Index('idx_query_cache_expires_at', 'expires_at'),
        Index('idx_query_cache_cached_at', 'cached_at'),
    )