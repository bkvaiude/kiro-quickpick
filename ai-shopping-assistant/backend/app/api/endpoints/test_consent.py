import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from datetime import datetime

from app.main import app
from app.models.user_consent import UserConsent, UserConsentCreate, UserConsentUpdate
from app.middleware.auth import get_current_user_id
from app.database.manager import get_db_session

client = TestClient(app)

# Mock user ID for testing
TEST_USER_ID = "auth0|test123456"

# Sample consent data
sample_consent = UserConsent(
    user_id=TEST_USER_ID,
    terms_accepted=True,
    marketing_consent=True,
    timestamp=datetime.utcnow()
)


@pytest.fixture
def mock_get_current_user_id():
    """Fixture to mock the get_current_user_id dependency."""
    def override_get_current_user_id():
        return TEST_USER_ID
    
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_db_session():
    """Fixture to mock the database session dependency."""
    mock_session = AsyncMock()
    
    def override_get_db_session():
        return mock_session
    
    app.dependency_overrides[get_db_session] = override_get_db_session
    yield mock_session
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user_consent_service():
    """Fixture to mock the user_consent_service."""
    with patch("app.api.endpoints.consent.user_consent_service") as mock_service:
        yield mock_service


def test_create_consent(mock_get_current_user_id, mock_db_session, mock_user_consent_service):
    """Test creating a new consent record."""
    # Setup
    mock_user_consent_service.get_consent = AsyncMock(return_value=None)
    mock_user_consent_service.create_consent = AsyncMock(return_value=sample_consent)
    
    # Execute
    consent_data = {"terms_accepted": True, "marketing_consent": True}
    response = client.post("/api/consent/", json=consent_data)
    
    # Assert
    assert response.status_code == 200
    assert response.json()["user_id"] == TEST_USER_ID
    assert response.json()["terms_accepted"] is True
    assert response.json()["marketing_consent"] is True
    mock_user_consent_service.create_consent.assert_called_once()


def test_create_consent_already_exists(mock_get_current_user_id, mock_db_session, mock_user_consent_service):
    """Test creating a consent record when one already exists."""
    # Setup
    mock_user_consent_service.get_consent = AsyncMock(return_value=sample_consent)
    
    # Execute
    consent_data = {"terms_accepted": True, "marketing_consent": True}
    response = client.post("/api/consent/", json=consent_data)
    
    # Assert
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_create_consent_terms_not_accepted(mock_get_current_user_id, mock_db_session, mock_user_consent_service):
    """Test creating a consent record without accepting terms."""
    # Setup
    mock_user_consent_service.get_consent = AsyncMock(return_value=None)
    
    # Execute
    consent_data = {"terms_accepted": False, "marketing_consent": True}
    response = client.post("/api/consent/", json=consent_data)
    
    # Assert
    assert response.status_code == 400
    assert "Terms of Use and Privacy Policy must be accepted" in response.json()["detail"]


def test_get_my_consent(mock_get_current_user_id, mock_db_session, mock_user_consent_service):
    """Test getting the current user's consent record."""
    # Setup
    mock_user_consent_service.get_consent = AsyncMock(return_value=sample_consent)
    
    # Execute
    response = client.get("/api/consent/me")
    
    # Assert
    assert response.status_code == 200
    assert response.json()["user_id"] == TEST_USER_ID
    assert response.json()["terms_accepted"] is True
    assert response.json()["marketing_consent"] is True


def test_get_my_consent_not_found(mock_get_current_user_id, mock_db_session, mock_user_consent_service):
    """Test getting a consent record that doesn't exist."""
    # Setup
    mock_user_consent_service.get_consent = AsyncMock(return_value=None)
    
    # Execute
    response = client.get("/api/consent/me")
    
    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_my_consent(mock_get_current_user_id, mock_db_session, mock_user_consent_service):
    """Test updating the current user's consent record."""
    # Setup
    updated_consent = UserConsent(
        user_id=TEST_USER_ID,
        terms_accepted=True,
        marketing_consent=False,
        timestamp=datetime.utcnow()
    )
    mock_user_consent_service.update_consent = AsyncMock(return_value=updated_consent)
    
    # Execute
    consent_data = {"marketing_consent": False}
    response = client.put("/api/consent/me", json=consent_data)
    
    # Assert
    assert response.status_code == 200
    assert response.json()["user_id"] == TEST_USER_ID
    assert response.json()["terms_accepted"] is True
    assert response.json()["marketing_consent"] is False


def test_update_my_consent_not_found(mock_get_current_user_id, mock_db_session, mock_user_consent_service):
    """Test updating a consent record that doesn't exist."""
    # Setup
    mock_user_consent_service.update_consent = AsyncMock(return_value=None)
    
    # Execute
    consent_data = {"marketing_consent": False}
    response = client.put("/api/consent/me", json=consent_data)
    
    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_list_all_consents(mock_get_current_user_id, mock_db_session, mock_user_consent_service):
    """Test listing all consent records."""
    # Setup
    mock_user_consent_service.list_consents = AsyncMock(return_value=[sample_consent])
    
    # Execute
    response = client.get("/api/consent/admin/all")
    
    # Assert
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["user_id"] == TEST_USER_ID