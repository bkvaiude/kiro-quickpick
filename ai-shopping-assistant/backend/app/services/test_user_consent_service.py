import pytest
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_consent import UserConsent, UserConsentCreate, UserConsentUpdate
from app.services.user_consent_service import user_consent_service
from app.database.models import UserConsentDB
from app.database.repositories.consent_repository import ConsentRepository


@pytest.fixture
async def db_session():
    """Create a test database session."""
    # This would typically use a test database
    # For now, we'll mock the session behavior
    from unittest.mock import AsyncMock
    session = AsyncMock(spec=AsyncSession)
    yield session


@pytest.fixture
async def consent_repo(db_session):
    """Create a consent repository with mocked session."""
    return ConsentRepository(db_session)


@pytest.mark.asyncio
async def test_create_consent(db_session):
    """Test creating a new user consent record."""
    # Setup
    user_id = "test_user_1"
    consent_data = UserConsentCreate(
        terms_accepted=True,
        marketing_consent=True
    )
    
    # Mock the repository response
    expected_consent_db = UserConsentDB(
        user_id=user_id,
        terms_accepted=True,
        marketing_consent=True,
        timestamp=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Mock the repository method
    from unittest.mock import AsyncMock, patch
    with patch('app.services.user_consent_service.ConsentRepository') as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.create_consent.return_value = expected_consent_db
        mock_repo_class.return_value = mock_repo
        
        # Execute
        result = await user_consent_service.create_consent(user_id, consent_data, db_session)
        
        # Assert
        assert result.user_id == user_id
        assert result.terms_accepted is True
        assert result.marketing_consent is True
        assert isinstance(result.timestamp, datetime)
        mock_repo.create_consent.assert_called_once()


@pytest.mark.asyncio
async def test_get_consent(db_session):
    """Test getting a user consent record."""
    # Setup
    user_id = "test_user_2"
    expected_consent_db = UserConsentDB(
        user_id=user_id,
        terms_accepted=True,
        marketing_consent=False,
        timestamp=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Mock the repository method
    from unittest.mock import AsyncMock, patch
    with patch('app.services.user_consent_service.ConsentRepository') as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.get_consent.return_value = expected_consent_db
        mock_repo_class.return_value = mock_repo
        
        # Execute
        result = await user_consent_service.get_consent(user_id, db_session)
        
        # Assert
        assert result is not None
        assert result.user_id == user_id
        assert result.terms_accepted is True
        assert result.marketing_consent is False
        mock_repo.get_consent.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_get_consent_not_found(db_session):
    """Test getting a user consent record that doesn't exist."""
    # Mock the repository method to return None
    from unittest.mock import AsyncMock, patch
    with patch('app.services.user_consent_service.ConsentRepository') as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.get_consent.return_value = None
        mock_repo_class.return_value = mock_repo
        
        # Execute
        result = await user_consent_service.get_consent("nonexistent_user", db_session)
        
        # Assert
        assert result is None


@pytest.mark.asyncio
async def test_update_consent(db_session):
    """Test updating a user consent record."""
    # Setup
    user_id = "test_user_3"
    updated_consent_db = UserConsentDB(
        user_id=user_id,
        terms_accepted=True,
        marketing_consent=True,  # Updated value
        timestamp=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Mock the repository method
    from unittest.mock import AsyncMock, patch
    with patch('app.services.user_consent_service.ConsentRepository') as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.update_consent.return_value = updated_consent_db
        mock_repo_class.return_value = mock_repo
        
        # Execute
        update_data = UserConsentUpdate(marketing_consent=True)
        result = await user_consent_service.update_consent(user_id, update_data, db_session)
        
        # Assert
        assert result is not None
        assert result.user_id == user_id
        assert result.terms_accepted is True
        assert result.marketing_consent is True
        mock_repo.update_consent.assert_called_once_with(user_id, marketing_consent=True)


@pytest.mark.asyncio
async def test_update_consent_not_found(db_session):
    """Test updating a user consent record that doesn't exist."""
    # Mock the repository method to return None
    from unittest.mock import AsyncMock, patch
    with patch('app.services.user_consent_service.ConsentRepository') as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.update_consent.return_value = None
        mock_repo_class.return_value = mock_repo
        
        # Execute
        update_data = UserConsentUpdate(marketing_consent=True)
        result = await user_consent_service.update_consent("nonexistent_user", update_data, db_session)
        
        # Assert
        assert result is None


@pytest.mark.asyncio
async def test_list_consents(db_session):
    """Test listing all user consent records."""
    # Setup
    user_ids = ["test_user_4", "test_user_5", "test_user_6"]
    expected_consents_db = [
        UserConsentDB(
            user_id=user_id,
            terms_accepted=True,
            marketing_consent=(user_id == "test_user_5"),
            timestamp=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        for user_id in user_ids
    ]
    
    # Mock the repository method
    from unittest.mock import AsyncMock, patch
    with patch('app.services.user_consent_service.ConsentRepository') as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.list_consents.return_value = expected_consents_db
        mock_repo_class.return_value = mock_repo
        
        # Execute
        result = await user_consent_service.list_consents(db_session)
        
        # Assert
        assert len(result) == 3
        assert set(c.user_id for c in result) == set(user_ids)
        
        # Check that only test_user_5 has marketing consent
        for consent in result:
            if consent.user_id == "test_user_5":
                assert consent.marketing_consent is True
            else:
                assert consent.marketing_consent is False
        
        mock_repo.list_consents.assert_called_once()


@pytest.mark.asyncio
async def test_update_consent_no_changes(db_session):
    """Test updating a user consent record with no actual changes."""
    # Setup
    user_id = "test_user_7"
    existing_consent_db = UserConsentDB(
        user_id=user_id,
        terms_accepted=True,
        marketing_consent=False,
        timestamp=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Mock the repository method
    from unittest.mock import AsyncMock, patch
    with patch('app.services.user_consent_service.ConsentRepository') as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.get_consent.return_value = existing_consent_db
        mock_repo_class.return_value = mock_repo
        
        # Execute - update with no changes
        update_data = UserConsentUpdate()  # No fields set
        result = await user_consent_service.update_consent(user_id, update_data, db_session)
        
        # Assert
        assert result is not None
        assert result.user_id == user_id
        assert result.terms_accepted is True
        assert result.marketing_consent is False
        # Should have called get_consent but not update_consent
        mock_repo.get_consent.assert_called_once_with(user_id)
        mock_repo.update_consent.assert_not_called()