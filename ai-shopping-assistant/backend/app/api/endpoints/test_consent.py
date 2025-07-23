import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.models.user_consent import UserConsent, UserConsentCreate, UserConsentUpdate
from app.services.user_consent_service import UserConsentService

client = TestClient(app)

# Mock user ID for testing
TEST_USER_ID = "auth0|test123456"

# Sample consent data
sample_consent = UserConsent(
    user_id=TEST_USER_ID,
    terms_accepted=True,
    marketing_consent=True,
    timestamp="2025-07-21T12:00:00"
)


@pytest.fixture
def mock_get_current_user_id():
    """Fixture to mock the get_current_user_id dependency."""
    with patch("app.api.endpoints.consent.get_current_user_id", return_value=TEST_USER_ID):
        yield


@pytest.fixture
def mock_user_consent_service():
    """Fixture to mock the UserConsentService."""
    with patch("app.api.endpoints.consent.UserConsentService") as mock_service:
        yield mock_service


def test_create_consent(mock_get_current_user_id, mock_user_consent_service):
    """Test creating a new consent record."""
    # Setup
    mock_user_consent_service.get_consent.return_value = None
    mock_user_consent_service.create_consent.return_value = sample_consent
    
    # Execute
    consent_data = {"terms_accepted": True, "marketing_consent": True}
    response = client.post("/api/consent/", json=consent_data)
    
    # Assert
    assert response.status_code == 200
    assert response.json()["user_id"] == TEST_USER_ID
    assert response.json()["terms_accepted"] is True
    assert response.json()["marketing_consent"] is True
    mock_user_consent_service.create_consent.assert_called_once()


def test_create_consent_already_exists(mock_get_current_user_id, mock_user_consent_service):
    """Test creating a consent record when one already exists."""
    # Setup
    mock_user_consent_service.get_consent.return_value = sample_consent
    
    # Execute
    consent_data = {"terms_accepted": True, "marketing_consent": True}
    response = client.post("/api/consent/", json=consent_data)
    
    # Assert
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_create_consent_terms_not_accepted(mock_get_current_user_id, mock_user_consent_service):
    """Test creating a consent record without accepting terms."""
    # Setup
    mock_user_consent_service.get_consent.return_value = None
    
    # Execute
    consent_data = {"terms_accepted": False, "marketing_consent": True}
    response = client.post("/api/consent/", json=consent_data)
    
    # Assert
    assert response.status_code == 400
    assert "Terms of Use and Privacy Policy must be accepted" in response.json()["detail"]


def test_get_my_consent(mock_get_current_user_id, mock_user_consent_service):
    """Test getting the current user's consent record."""
    # Setup
    mock_user_consent_service.get_consent.return_value = sample_consent
    
    # Execute
    response = client.get("/api/consent/me")
    
    # Assert
    assert response.status_code == 200
    assert response.json()["user_id"] == TEST_USER_ID
    assert response.json()["terms_accepted"] is True
    assert response.json()["marketing_consent"] is True


def test_get_my_consent_not_found(mock_get_current_user_id, mock_user_consent_service):
    """Test getting a consent record that doesn't exist."""
    # Setup
    mock_user_consent_service.get_consent.return_value = None
    
    # Execute
    response = client.get("/api/consent/me")
    
    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_my_consent(mock_get_current_user_id, mock_user_consent_service):
    """Test updating the current user's consent record."""
    # Setup
    updated_consent = UserConsent(
        user_id=TEST_USER_ID,
        terms_accepted=True,
        marketing_consent=False,
        timestamp="2025-07-21T13:00:00"
    )
    mock_user_consent_service.update_consent.return_value = updated_consent
    
    # Execute
    consent_data = {"marketing_consent": False}
    response = client.put("/api/consent/me", json=consent_data)
    
    # Assert
    assert response.status_code == 200
    assert response.json()["user_id"] == TEST_USER_ID
    assert response.json()["terms_accepted"] is True
    assert response.json()["marketing_consent"] is False


def test_update_my_consent_not_found(mock_get_current_user_id, mock_user_consent_service):
    """Test updating a consent record that doesn't exist."""
    # Setup
    mock_user_consent_service.update_consent.return_value = None
    
    # Execute
    consent_data = {"marketing_consent": False}
    response = client.put("/api/consent/me", json=consent_data)
    
    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_list_all_consents(mock_get_current_user_id, mock_user_consent_service):
    """Test listing all consent records."""
    # Setup
    mock_user_consent_service.list_consents.return_value = [sample_consent]
    
    # Execute
    response = client.get("/api/consent/admin/all")
    
    # Assert
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["user_id"] == TEST_USER_ID