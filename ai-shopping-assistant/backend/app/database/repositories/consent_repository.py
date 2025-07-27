"""Consent repository for managing user consent records."""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc, and_, func, or_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from .base import BaseRepository, RepositoryError, RepositoryIntegrityError
from ..models import UserConsentDB

logger = logging.getLogger(__name__)


class ConsentRepository(BaseRepository[UserConsentDB]):
    """Repository for managing user consent records."""
    
    def __init__(self, session: AsyncSession):
        """Initialize the consent repository."""
        super().__init__(session, UserConsentDB)
    
    # User Consent CRUD Operations
    
    async def get_consent(self, user_id: str) -> Optional[UserConsentDB]:
        """
        Get user consent record by user ID.
        
        Args:
            user_id: The user identifier
            
        Returns:
            User consent if found, None otherwise
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            result = await self.session.execute(
                select(UserConsentDB).where(UserConsentDB.user_id == user_id)
            )
            consent = result.scalar_one_or_none()
            
            if consent:
                logger.debug(f"Retrieved consent for user {user_id}: "
                           f"terms={consent.terms_accepted}, marketing={consent.marketing_consent}")
            else:
                logger.debug(f"No consent record found for user {user_id}")
            
            return consent
        except SQLAlchemyError as e:
            logger.error(f"Failed to get consent for user {user_id}: {e}")
            raise RepositoryError(f"Failed to get user consent: {e}") from e
    
    async def create_consent(self, consent: UserConsentDB) -> UserConsentDB:
        """
        Create new user consent record.
        
        Args:
            consent: The consent instance to create
            
        Returns:
            The created consent record
            
        Raises:
            RepositoryIntegrityError: If consent already exists for user
            RepositoryError: If creation fails
        """
        try:
            created_consent = await self.create(consent)
            logger.info(f"Created consent for user {consent.user_id}: "
                       f"terms={consent.terms_accepted}, marketing={consent.marketing_consent}")
            return created_consent
        except RepositoryIntegrityError:
            logger.warning(f"Consent already exists for user {consent.user_id}")
            raise
        except Exception as e:
            logger.error(f"Failed to create consent for user {consent.user_id}: {e}")
            raise RepositoryError(f"Failed to create user consent: {e}") from e
    
    async def update_consent(self, user_id: str, **updates) -> Optional[UserConsentDB]:
        """
        Update user consent information.
        
        Args:
            user_id: The user identifier
            **updates: Fields to update
            
        Returns:
            Updated consent if found, None otherwise
            
        Raises:
            RepositoryError: If update fails
        """
        try:
            # Add updated_at timestamp
            updates['updated_at'] = datetime.utcnow()
            
            updated_consent = await self.update_by_id(user_id, **updates)
            
            if updated_consent:
                logger.debug(f"Updated consent for user {user_id}: {updates}")
            else:
                logger.warning(f"No consent record found to update for user {user_id}")
            
            return updated_consent
        except Exception as e:
            logger.error(f"Failed to update consent for user {user_id}: {e}")
            raise
    
    async def delete_consent(self, user_id: str) -> bool:
        """
        Delete user consent record.
        
        Args:
            user_id: The user identifier
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            RepositoryError: If deletion fails
        """
        try:
            deleted = await self.delete_by_id(user_id)
            
            if deleted:
                logger.info(f"Deleted consent for user {user_id}")
            else:
                logger.debug(f"No consent record found to delete for user {user_id}")
            
            return deleted
        except Exception as e:
            logger.error(f"Failed to delete consent for user {user_id}: {e}")
            raise
    
    # Consent History and Tracking
    
    async def get_consents_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        terms_accepted: Optional[bool] = None,
        marketing_consent: Optional[bool] = None
    ) -> List[UserConsentDB]:
        """
        Get consent records within a date range with optional filters.
        
        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            terms_accepted: Filter by terms acceptance status (optional)
            marketing_consent: Filter by marketing consent status (optional)
            
        Returns:
            List of consent records within the date range
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            query = select(UserConsentDB).where(
                and_(
                    UserConsentDB.updated_at >= start_date,
                    UserConsentDB.updated_at <= end_date
                )
            )
            
            # Add optional filters
            if terms_accepted is not None:
                query = query.where(UserConsentDB.terms_accepted == terms_accepted)
            if marketing_consent is not None:
                query = query.where(UserConsentDB.marketing_consent == marketing_consent)
            
            # Order by updated_at descending (newest first)
            query = query.order_by(desc(UserConsentDB.updated_at))
            
            result = await self.session.execute(query)
            consents = result.scalars().all()
            
            logger.debug(f"Retrieved {len(consents)} consent records "
                        f"between {start_date} and {end_date}")
            return list(consents)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get consents by date range: {e}")
            raise RepositoryError(f"Failed to get consents by date range: {e}") from e
    
    async def get_recent_consent_changes(self, hours: int = 24) -> List[UserConsentDB]:
        """
        Get consent records that have been updated recently.
        
        Args:
            hours: Number of hours to look back (default: 24)
            
        Returns:
            List of recently updated consent records
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            result = await self.session.execute(
                select(UserConsentDB)
                .where(UserConsentDB.updated_at >= cutoff_time)
                .order_by(desc(UserConsentDB.updated_at))
            )
            
            recent_consents = result.scalars().all()
            logger.debug(f"Retrieved {len(recent_consents)} consent records updated in last {hours} hours")
            return list(recent_consents)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get recent consent changes: {e}")
            raise RepositoryError(f"Failed to get recent consent changes: {e}") from e
    
    # Batch Consent Operations
    
    async def list_consents(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        terms_accepted: Optional[bool] = None,
        marketing_consent: Optional[bool] = None
    ) -> List[UserConsentDB]:
        """
        List consent records with optional filters and pagination.
        
        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip
            terms_accepted: Filter by terms acceptance status (optional)
            marketing_consent: Filter by marketing consent status (optional)
            
        Returns:
            List of consent records
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            query = select(UserConsentDB)
            
            # Add optional filters
            if terms_accepted is not None:
                query = query.where(UserConsentDB.terms_accepted == terms_accepted)
            if marketing_consent is not None:
                query = query.where(UserConsentDB.marketing_consent == marketing_consent)
            
            # Order by updated_at descending
            query = query.order_by(desc(UserConsentDB.updated_at))
            
            # Apply pagination
            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)
            
            result = await self.session.execute(query)
            consents = result.scalars().all()
            
            logger.debug(f"Listed {len(consents)} consent records")
            return list(consents)
        except SQLAlchemyError as e:
            logger.error(f"Failed to list consents: {e}")
            raise RepositoryError(f"Failed to list consents: {e}") from e
    
    async def get_consents_by_user_ids(self, user_ids: List[str]) -> List[UserConsentDB]:
        """
        Get consent records for multiple users.
        
        Args:
            user_ids: List of user IDs
            
        Returns:
            List of consent records for the specified users
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            if not user_ids:
                return []
            
            result = await self.session.execute(
                select(UserConsentDB)
                .where(UserConsentDB.user_id.in_(user_ids))
                .order_by(UserConsentDB.user_id)
            )
            
            consents = result.scalars().all()
            logger.debug(f"Retrieved consent records for {len(consents)} out of {len(user_ids)} users")
            return list(consents)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get consents by user IDs: {e}")
            raise RepositoryError(f"Failed to get consents by user IDs: {e}") from e
    
    async def batch_update_marketing_consent(
        self,
        user_ids: List[str],
        marketing_consent: bool
    ) -> int:
        """
        Batch update marketing consent for multiple users.
        
        Args:
            user_ids: List of user IDs to update
            marketing_consent: New marketing consent value
            
        Returns:
            Number of records updated
            
        Raises:
            RepositoryError: If batch update fails
        """
        try:
            if not user_ids:
                return 0
            
            result = await self.session.execute(
                update(UserConsentDB)
                .where(UserConsentDB.user_id.in_(user_ids))
                .values(
                    marketing_consent=marketing_consent,
                    updated_at=datetime.utcnow()
                )
            )
            
            updated_count = result.rowcount
            await self.flush()
            
            logger.info(f"Batch updated marketing consent to {marketing_consent} for {updated_count} users")
            return updated_count
        except SQLAlchemyError as e:
            logger.error(f"Failed to batch update marketing consent: {e}")
            await self.rollback()
            raise RepositoryError(f"Failed to batch update marketing consent: {e}") from e
    
    # Analytics and Reporting
    
    async def get_consent_statistics(self) -> Dict[str, Any]:
        """
        Get consent statistics and analytics.
        
        Returns:
            Dictionary with consent statistics
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            # Get overall consent statistics
            result = await self.session.execute(
                select(
                    func.count(UserConsentDB.user_id).label('total_users'),
                    func.count().filter(UserConsentDB.terms_accepted == True).label('terms_accepted_count'),
                    func.count().filter(UserConsentDB.marketing_consent == True).label('marketing_consent_count'),
                    func.count().filter(
                        and_(
                            UserConsentDB.terms_accepted == True,
                            UserConsentDB.marketing_consent == True
                        )
                    ).label('both_consents_count')
                )
            )
            
            row = result.first()
            
            total_users = row.total_users or 0
            terms_accepted = row.terms_accepted_count or 0
            marketing_consent = row.marketing_consent_count or 0
            both_consents = row.both_consents_count or 0
            
            statistics = {
                'total_users': total_users,
                'terms_accepted': {
                    'count': terms_accepted,
                    'percentage': (terms_accepted / total_users * 100) if total_users > 0 else 0
                },
                'marketing_consent': {
                    'count': marketing_consent,
                    'percentage': (marketing_consent / total_users * 100) if total_users > 0 else 0
                },
                'both_consents': {
                    'count': both_consents,
                    'percentage': (both_consents / total_users * 100) if total_users > 0 else 0
                }
            }
            
            logger.debug(f"Generated consent statistics: {statistics}")
            return statistics
        except SQLAlchemyError as e:
            logger.error(f"Failed to get consent statistics: {e}")
            raise RepositoryError(f"Failed to get consent statistics: {e}") from e
    
    async def get_consent_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Get consent trends over time.
        
        Args:
            days: Number of days to analyze (default: 30)
            
        Returns:
            Dictionary with consent trends
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get consent changes over time
            result = await self.session.execute(
                select(
                    func.date(UserConsentDB.updated_at).label('date'),
                    func.count(UserConsentDB.user_id).label('total_updates'),
                    func.count().filter(UserConsentDB.terms_accepted == True).label('terms_accepted'),
                    func.count().filter(UserConsentDB.marketing_consent == True).label('marketing_consent')
                )
                .where(UserConsentDB.updated_at >= cutoff_date)
                .group_by(func.date(UserConsentDB.updated_at))
                .order_by(func.date(UserConsentDB.updated_at))
            )
            
            trends = {
                'period_days': days,
                'daily_data': []
            }
            
            for row in result:
                trends['daily_data'].append({
                    'date': row.date.isoformat() if row.date else None,
                    'total_updates': row.total_updates or 0,
                    'terms_accepted': row.terms_accepted or 0,
                    'marketing_consent': row.marketing_consent or 0
                })
            
            logger.debug(f"Generated consent trends for {days} days: {len(trends['daily_data'])} data points")
            return trends
        except SQLAlchemyError as e:
            logger.error(f"Failed to get consent trends: {e}")
            raise RepositoryError(f"Failed to get consent trends: {e}") from e
    
    # Compliance and Data Management
    
    async def find_users_without_consent(self, user_ids: List[str]) -> List[str]:
        """
        Find users from a list who don't have consent records.
        
        Args:
            user_ids: List of user IDs to check
            
        Returns:
            List of user IDs without consent records
            
        Raises:
            RepositoryError: If query fails
        """
        try:
            if not user_ids:
                return []
            
            # Get users who have consent records
            result = await self.session.execute(
                select(UserConsentDB.user_id)
                .where(UserConsentDB.user_id.in_(user_ids))
            )
            
            users_with_consent = {row.user_id for row in result}
            users_without_consent = [user_id for user_id in user_ids if user_id not in users_with_consent]
            
            logger.debug(f"Found {len(users_without_consent)} users without consent records "
                        f"out of {len(user_ids)} checked")
            return users_without_consent
        except SQLAlchemyError as e:
            logger.error(f"Failed to find users without consent: {e}")
            raise RepositoryError(f"Failed to find users without consent: {e}") from e
    
    async def cleanup_old_consent_records(self, days: int = 365) -> int:
        """
        Clean up very old consent records (for compliance with data retention policies).
        
        Args:
            days: Number of days to keep consent records (default: 365)
            
        Returns:
            Number of records deleted
            
        Raises:
            RepositoryError: If cleanup fails
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Delete old consent records
            result = await self.session.execute(
                delete(UserConsentDB).where(UserConsentDB.updated_at < cutoff_date)
            )
            
            deleted_count = result.rowcount
            await self.flush()
            
            logger.info(f"Cleaned up {deleted_count} consent records older than {days} days")
            return deleted_count
        except SQLAlchemyError as e:
            logger.error(f"Failed to cleanup old consent records: {e}")
            await self.rollback()
            raise RepositoryError(f"Failed to cleanup old consent records: {e}") from e
    
    async def export_consent_data(
        self,
        user_ids: Optional[List[str]] = None,
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Export consent data for compliance or backup purposes.
        
        Args:
            user_ids: Specific user IDs to export (optional, exports all if None)
            include_deleted: Whether to include deleted records (not implemented yet)
            
        Returns:
            List of consent records as dictionaries
            
        Raises:
            RepositoryError: If export fails
        """
        try:
            query = select(UserConsentDB)
            
            if user_ids:
                query = query.where(UserConsentDB.user_id.in_(user_ids))
            
            query = query.order_by(UserConsentDB.user_id)
            
            result = await self.session.execute(query)
            consents = result.scalars().all()
            
            # Convert to dictionaries for export
            export_data = []
            for consent in consents:
                export_data.append({
                    'user_id': consent.user_id,
                    'terms_accepted': consent.terms_accepted,
                    'marketing_consent': consent.marketing_consent,
                    'timestamp': consent.timestamp.isoformat() if consent.timestamp else None,
                    'updated_at': consent.updated_at.isoformat() if consent.updated_at else None
                })
            
            logger.info(f"Exported consent data for {len(export_data)} users")
            return export_data
        except SQLAlchemyError as e:
            logger.error(f"Failed to export consent data: {e}")
            raise RepositoryError(f"Failed to export consent data: {e}") from e