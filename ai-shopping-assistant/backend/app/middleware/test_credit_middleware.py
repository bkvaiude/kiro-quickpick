import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import Request
from fastapi.responses import JSONResponse
from app.middleware.credit_middleware import (
    CreditMiddleware, 
    CreditExhaustedException, 
    credit_exhausted_handler,
    validate_credits,
    deduct_credit,
    get_credit_status
)
from app.models.credit import CreditStatus


class TestCreditMiddleware:
    """Test cases for CreditMiddleware"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        self.middleware = CreditMiddleware()
        # Mock the credit service
        self.middleware.credit_service = MagicMock()
    
    def test_get_user_identifier_authenticated_user(self):
        """Test getting user identifier for authenticated user"""
        request = MagicMock()
        user = {"sub": "auth0|123456", "email": "test@example.com"}
        
        user_id, is_guest = self.middleware.get_user_identifier(request, user)
        
        assert user_id == "auth0|123456"
        assert is_guest is False
    
    def test_get_user_identifier_guest_with_session_id(self):
        """Test getting user identifier for guest with session ID"""
        request = MagicMock()
        request.headers.get.return_value = "session_123"
        user = None
        
        user_id, is_guest = self.middleware.get_user_identifier(request, user)
        
        assert user_id == "session_123"
        assert is_guest is True
        request.headers.get.assert_called_with("X-Session-ID")
    
    def test_get_user_identifier_guest_without_session_id(self):
        """Test getting user identifier for guest without session ID"""
        request = MagicMock()
        request.headers.get.return_value = None
        request.client.host = "192.168.1.1"
        user = None
        
        user_id, is_guest = self.middleware.get_user_identifier(request, user)
        
        assert user_id.startswith("guest_192.168.1.1_")
        assert is_guest is True
    
    def test_get_user_identifier_guest_no_client_info(self):
        """Test getting user identifier for guest without client info"""
        request = MagicMock()
        request.headers.get.return_value = None
        request.client = None
        user = None
        
        user_id, is_guest = self.middleware.get_user_identifier(request, user)
        
        assert user_id.startswith("guest_unknown_")
        assert is_guest is True
    
    @pytest.mark.asyncio
    async def test_validate_credits_sufficient_credits(self):
        """Test credit validation with sufficient credits"""
        request = MagicMock()
        user = {"sub": "auth0|123456"}
        
        # Mock credit service to return sufficient credits
        self.middleware.credit_service.check_credits.return_value = 25
        
        result = await self.middleware.validate_credits(request, user)
        
        assert result["user_id"] == "auth0|123456"
        assert result["is_guest"] is False
        assert result["available_credits"] == 25
        
        self.middleware.credit_service.check_credits.assert_called_once_with("auth0|123456", False)
    
    @pytest.mark.asyncio
    async def test_validate_credits_insufficient_credits(self):
        """Test credit validation with insufficient credits"""
        request = MagicMock()
        user = {"sub": "auth0|123456"}
        
        # Mock credit service to return no credits
        self.middleware.credit_service.check_credits.return_value = 0
        
        # Mock credit status for error response
        mock_status = CreditStatus(
            available_credits=0,
            max_credits=50,
            is_guest=False,
            can_reset=True,
            next_reset_time=None
        )
        self.middleware.credit_service.get_credit_status.return_value = mock_status
        
        with pytest.raises(CreditExhaustedException) as exc_info:
            await self.middleware.validate_credits(request, user)
        
        assert exc_info.value.detail == "Insufficient credits to process request"
        assert exc_info.value.available_credits == 0
        assert exc_info.value.max_credits == 50
        assert exc_info.value.is_guest is False
    
    @pytest.mark.asyncio
    async def test_deduct_credit_success(self):
        """Test successful credit deduction"""
        request = MagicMock()
        user = {"sub": "auth0|123456"}
        
        # Mock credit service to return success
        self.middleware.credit_service.deduct_credit.return_value = True
        
        result = await self.middleware.deduct_credit(request, user, amount=2)
        
        assert result is True
        self.middleware.credit_service.deduct_credit.assert_called_once_with("auth0|123456", False, 2)
    
    @pytest.mark.asyncio
    async def test_deduct_credit_failure(self):
        """Test failed credit deduction"""
        request = MagicMock()
        user = {"sub": "auth0|123456"}
        
        # Mock credit service to return failure
        self.middleware.credit_service.deduct_credit.return_value = False
        
        # Mock credit status for error response
        mock_status = CreditStatus(
            available_credits=1,
            max_credits=50,
            is_guest=False,
            can_reset=True,
            next_reset_time=None
        )
        self.middleware.credit_service.get_credit_status.return_value = mock_status
        
        with pytest.raises(CreditExhaustedException) as exc_info:
            await self.middleware.deduct_credit(request, user, amount=2)
        
        assert exc_info.value.detail == "Insufficient credits to deduct 2 credit(s)"
        assert exc_info.value.available_credits == 1
        assert exc_info.value.max_credits == 50
        assert exc_info.value.is_guest is False
    
    @pytest.mark.asyncio
    async def test_get_credit_status(self):
        """Test getting credit status"""
        request = MagicMock()
        user = {"sub": "auth0|123456"}
        
        # Mock credit status
        from datetime import datetime
        mock_status = CreditStatus(
            available_credits=30,
            max_credits=50,
            is_guest=False,
            can_reset=True,
            next_reset_time=datetime(2025, 7, 25, 0, 0, 0)
        )
        self.middleware.credit_service.get_credit_status.return_value = mock_status
        
        result = await self.middleware.get_credit_status(request, user)
        
        assert result["user_id"] == "auth0|123456"
        assert result["available_credits"] == 30
        assert result["max_credits"] == 50
        assert result["is_guest"] is False
        assert result["can_reset"] is True
        assert result["next_reset_time"] == "2025-07-25T00:00:00"
    
    @pytest.mark.asyncio
    async def test_get_credit_status_guest_user(self):
        """Test getting credit status for guest user"""
        request = MagicMock()
        request.headers.get.return_value = "guest_session_123"
        user = None
        
        # Mock credit status for guest
        mock_status = CreditStatus(
            available_credits=8,
            max_credits=10,
            is_guest=True,
            can_reset=False,
            next_reset_time=None
        )
        self.middleware.credit_service.get_credit_status.return_value = mock_status
        
        result = await self.middleware.get_credit_status(request, user)
        
        assert result["user_id"] == "guest_session_123"
        assert result["available_credits"] == 8
        assert result["max_credits"] == 10
        assert result["is_guest"] is True
        assert result["can_reset"] is False
        assert result["next_reset_time"] is None


class TestCreditExhaustedException:
    """Test cases for CreditExhaustedException"""
    
    def test_exception_creation(self):
        """Test creating a CreditExhaustedException"""
        exc = CreditExhaustedException(
            detail="Test error",
            available_credits=5,
            max_credits=50,
            is_guest=False
        )
        
        assert exc.detail == "Test error"
        assert exc.available_credits == 5
        assert exc.max_credits == 50
        assert exc.is_guest is False
    
    def test_exception_default_values(self):
        """Test CreditExhaustedException with default values"""
        exc = CreditExhaustedException("Test error")
        
        assert exc.detail == "Test error"
        assert exc.available_credits == 0
        assert exc.max_credits == 0
        assert exc.is_guest is True


class TestCreditExhaustedHandler:
    """Test cases for credit_exhausted_handler"""
    
    @pytest.mark.asyncio
    async def test_credit_exhausted_handler_guest(self):
        """Test credit exhausted handler for guest user"""
        request = MagicMock()
        exc = CreditExhaustedException(
            detail="Insufficient credits",
            available_credits=0,
            max_credits=10,
            is_guest=True
        )
        
        response = await credit_exhausted_handler(request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 429
        
        # Check response content
        content = response.body.decode()
        assert "Insufficient credits" in content
        assert "credits_exhausted" in content
        assert "log in to get more credits" in content
    
    @pytest.mark.asyncio
    async def test_credit_exhausted_handler_registered(self):
        """Test credit exhausted handler for registered user"""
        request = MagicMock()
        exc = CreditExhaustedException(
            detail="Insufficient credits",
            available_credits=0,
            max_credits=50,
            is_guest=False
        )
        
        response = await credit_exhausted_handler(request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 429
        
        # Check response content
        content = response.body.decode()
        assert "Insufficient credits" in content
        assert "credits_exhausted" in content
        assert "credits will be reset in 24 hours" in content


class TestDependencyFunctions:
    """Test cases for dependency functions"""
    
    @pytest.mark.asyncio
    @patch('app.middleware.credit_middleware.credit_middleware')
    async def test_validate_credits_dependency(self, mock_middleware):
        """Test validate_credits dependency function"""
        request = MagicMock()
        user = {"sub": "auth0|123456"}
        
        mock_middleware.validate_credits = AsyncMock(return_value={"user_id": "auth0|123456", "available_credits": 25})
        
        result = await validate_credits(request, user)
        
        assert result["user_id"] == "auth0|123456"
        assert result["available_credits"] == 25
        mock_middleware.validate_credits.assert_called_once_with(request, user)
    
    @pytest.mark.asyncio
    @patch('app.middleware.credit_middleware.credit_middleware')
    async def test_deduct_credit_dependency(self, mock_middleware):
        """Test deduct_credit dependency function"""
        request = MagicMock()
        user = {"sub": "auth0|123456"}
        
        mock_middleware.deduct_credit = AsyncMock(return_value=True)
        
        result = await deduct_credit(request, user)
        
        assert result is True
        mock_middleware.deduct_credit.assert_called_once_with(request, user, amount=1)
    
    @pytest.mark.asyncio
    @patch('app.middleware.credit_middleware.credit_middleware')
    async def test_get_credit_status_dependency(self, mock_middleware):
        """Test get_credit_status dependency function"""
        request = MagicMock()
        user = {"sub": "auth0|123456"}
        
        expected_status = {
            "user_id": "auth0|123456",
            "available_credits": 30,
            "max_credits": 50,
            "is_guest": False,
            "can_reset": True,
            "next_reset_time": "2025-07-25T00:00:00"
        }
        
        mock_middleware.get_credit_status = AsyncMock(return_value=expected_status)
        
        result = await get_credit_status(request, user)
        
        assert result == expected_status
        mock_middleware.get_credit_status.assert_called_once_with(request, user)