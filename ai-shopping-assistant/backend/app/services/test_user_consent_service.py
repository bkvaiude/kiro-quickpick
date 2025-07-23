import pytest
from datetime import datetime
from app.models.user_consent import UserConsent, UserConsentCreate, UserConsentUpdate
from app.services.user_consent_service import UserConsentService, user_consents


@pytest.fixture
def reset_consents():
    """Reset the user_consents dictionary before each test."""
    user_consents.clear()
    yield
    user_consents.clear()


def test_create_consent(reset_consents):
    """Test creating a new user consent record."""
    # Setup
    user_id = "test_user_1"
    consent_data = UserConsentCreate(
        terms_accepted=True,
        marketing_consent=True
    )
    
    # Execute
    result = UserConsentService.create_consent(user_id, consent_data)
    
    # Assert
    assert result.user_id == user_id
    assert result.terms_accepted is True
    assert result.marketing_consent is True
    assert isinstance(result.timestamp, datetime)
    assert user_id in user_consents


def test_get_consent(reset_consents):
    """Test getting a user consent record."""
    # Setup
    user_id = "test_user_2"
    consent_data = UserConsentCreate(
        terms_accepted=True,
        marketing_consent=False
    )
    UserConsentService.create_consent(user_id, consent_data)
    
    # Execute
    result = UserConsentService.get_consent(user_id)
    
    # Assert
    assert result is not None
    assert result.user_id == user_id
    assert result.terms_accepted is True
    assert result.marketing_consent is False


def test_get_consent_not_found(reset_consents):
    """Test getting a user consent record that doesn't exist."""
    # Execute
    result = UserConsentService.get_consent("nonexistent_user")
    
    # Assert
    assert result is None


def test_update_consent(reset_consents):
    """Test updating a user consent record."""
    # Setup
    user_id = "test_user_3"
    consent_data = UserConsentCreate(
        terms_accepted=True,
        marketing_consent=False
    )
    original_consent = UserConsentService.create_consent(user_id, consent_data)
    original_timestamp = original_consent.timestamp
    
    # Wait a moment to ensure timestamp changes
    import time
    time.sleep(0.001)
    
    # Execute
    update_data = UserConsentUpdate(marketing_consent=True)
    result = UserConsentService.update_consent(user_id, update_data)
    
    # Assert
    assert result is not None
    assert result.user_id == user_id
    assert result.terms_accepted is True  # Unchanged
    assert result.marketing_consent is True  # Updated
    assert result.timestamp > original_timestamp  # Timestamp updated


def test_update_consent_not_found(reset_consents):
    """Test updating a user consent record that doesn't exist."""
    # Execute
    update_data = UserConsentUpdate(marketing_consent=True)
    result = UserConsentService.update_consent("nonexistent_user", update_data)
    
    # Assert
    assert result is None


def test_list_consents(reset_consents):
    """Test listing all user consent records."""
    # Setup
    user_ids = ["test_user_4", "test_user_5", "test_user_6"]
    for user_id in user_ids:
        consent_data = UserConsentCreate(
            terms_accepted=True,
            marketing_consent=(user_id == "test_user_5")  # Only the second user has marketing consent
        )
        UserConsentService.create_consent(user_id, consent_data)
    
    # Execute
    result = UserConsentService.list_consents()
    
    # Assert
    assert len(result) == 3
    assert set(c.user_id for c in result) == set(user_ids)
    
    # Check that only test_user_5 has marketing consent
    for consent in result:
        if consent.user_id == "test_user_5":
            assert consent.marketing_consent is True
        else:
            assert consent.marketing_consent is False