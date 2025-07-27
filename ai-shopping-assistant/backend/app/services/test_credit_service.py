import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from app.services.credit_service import CreditService
from app.models.credit import UserCredits, CreditStatus
from app.config import settings


class TestCreditService:
    """Test cases for CreditService"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        self.service = CreditService()
        # Clear any existing data
        self.service._user_credits = {}
        self.service._credit_transactions = []
    
    def test_get_user_credits_new_guest(self):
        """Test getting credits for a new guest user"""
        user_id = "guest_123"
        credits = self.service.get_user_credits(user_id, is_guest=True)
        
        assert credits.user_id == user_id
        assert credits.is_guest is True
        assert credits.available_credits == settings.credit_system.max_guest_credits
        assert credits.max_credits == settings.credit_system.max_guest_credits
        assert isinstance(credits.last_reset_timestamp, datetime)
    
    def test_get_user_credits_new_registered(self):
        """Test getting credits for a new registered user"""
        user_id = "auth0|123456"
        credits = self.service.get_user_credits(user_id, is_guest=False)
        
        assert credits.user_id == user_id
        assert credits.is_guest is False
        assert credits.available_credits == settings.credit_system.max_registered_credits
        assert credits.max_credits == settings.credit_system.max_registered_credits
        assert isinstance(credits.last_reset_timestamp, datetime)
    
    def test_get_user_credits_existing_user(self):
        """Test getting credits for an existing user"""
        user_id = "auth0|123456"
        
        # First call creates the user
        credits1 = self.service.get_user_credits(user_id, is_guest=False)
        credits1.available_credits = 30  # Modify credits
        
        # Second call should return the same instance
        credits2 = self.service.get_user_credits(user_id, is_guest=False)
        
        assert credits1 is credits2
        assert credits2.available_credits == 30
    
    def test_check_credits(self):
        """Test checking available credits"""
        user_id = "guest_123"
        
        # Check credits for new user
        available = self.service.check_credits(user_id, is_guest=True)
        assert available == settings.credit_system.max_guest_credits
        
        # Deduct some credits and check again
        self.service.deduct_credit(user_id, is_guest=True, amount=3)
        available = self.service.check_credits(user_id, is_guest=True)
        assert available == settings.credit_system.max_guest_credits - 3
    
    def test_deduct_credit_success(self):
        """Test successful credit deduction"""
        user_id = "guest_123"
        
        # Deduct 1 credit
        result = self.service.deduct_credit(user_id, is_guest=True)
        assert result is True
        
        # Check remaining credits
        credits = self.service.get_user_credits(user_id, is_guest=True)
        assert credits.available_credits == settings.credit_system.max_guest_credits - 1
    
    def test_deduct_credit_multiple(self):
        """Test deducting multiple credits"""
        user_id = "guest_123"
        
        # Deduct 5 credits
        result = self.service.deduct_credit(user_id, is_guest=True, amount=5)
        assert result is True
        
        # Check remaining credits
        credits = self.service.get_user_credits(user_id, is_guest=True)
        assert credits.available_credits == settings.credit_system.max_guest_credits - 5
    
    def test_deduct_credit_insufficient(self):
        """Test credit deduction when insufficient credits"""
        user_id = "guest_123"
        
        # First, exhaust most credits
        max_credits = settings.credit_system.max_guest_credits
        self.service.deduct_credit(user_id, is_guest=True, amount=max_credits - 1)
        
        # Try to deduct more than available
        result = self.service.deduct_credit(user_id, is_guest=True, amount=2)
        assert result is False
        
        # Credits should remain unchanged
        credits = self.service.get_user_credits(user_id, is_guest=True)
        assert credits.available_credits == 1
    
    def test_reset_credits_specific_user(self):
        """Test resetting credits for a specific registered user"""
        user_id = "auth0|123456"
        
        # Create user and deduct some credits
        self.service.deduct_credit(user_id, is_guest=False, amount=20)
        credits_before = self.service.get_user_credits(user_id, is_guest=False)
        assert credits_before.available_credits == settings.credit_system.max_registered_credits - 20
        
        # Reset credits
        self.service.reset_credits(user_id)
        
        # Check credits are reset
        credits_after = self.service.get_user_credits(user_id, is_guest=False)
        assert credits_after.available_credits == settings.credit_system.max_registered_credits
    
    def test_reset_credits_guest_user_ignored(self):
        """Test that guest user credits are not reset"""
        user_id = "guest_123"
        
        # Create guest user and deduct some credits
        self.service.deduct_credit(user_id, is_guest=True, amount=5)
        credits_before = self.service.get_user_credits(user_id, is_guest=True)
        original_credits = credits_before.available_credits
        
        # Try to reset credits (should be ignored for guests)
        self.service.reset_credits(user_id)
        
        # Credits should remain unchanged
        credits_after = self.service.get_user_credits(user_id, is_guest=True)
        assert credits_after.available_credits == original_credits
    
    def test_reset_credits_all_users(self):
        """Test resetting credits for all registered users"""
        # Create multiple users
        guest_id = "guest_123"
        user1_id = "auth0|user1"
        user2_id = "auth0|user2"
        
        # Deduct credits from all users
        self.service.deduct_credit(guest_id, is_guest=True, amount=3)
        self.service.deduct_credit(user1_id, is_guest=False, amount=10)
        self.service.deduct_credit(user2_id, is_guest=False, amount=15)
        
        # Reset all users
        self.service.reset_credits()
        
        # Check that only registered users were reset
        guest_credits = self.service.get_user_credits(guest_id, is_guest=True)
        user1_credits = self.service.get_user_credits(user1_id, is_guest=False)
        user2_credits = self.service.get_user_credits(user2_id, is_guest=False)
        
        assert guest_credits.available_credits == settings.credit_system.max_guest_credits - 3  # Not reset
        assert user1_credits.available_credits == settings.credit_system.max_registered_credits  # Reset
        assert user2_credits.available_credits == settings.credit_system.max_registered_credits  # Reset
    
    def test_get_credit_status_guest(self):
        """Test getting credit status for guest user"""
        user_id = "guest_123"
        
        # Deduct some credits
        self.service.deduct_credit(user_id, is_guest=True, amount=3)
        
        # Get status
        status = self.service.get_credit_status(user_id, is_guest=True)
        
        assert status.available_credits == settings.credit_system.max_guest_credits - 3
        assert status.max_credits == settings.credit_system.max_guest_credits
        assert status.is_guest is True
        assert status.can_reset is False
        assert status.next_reset_time is None
    
    def test_get_credit_status_registered(self):
        """Test getting credit status for registered user"""
        user_id = "auth0|123456"
        
        # Deduct some credits
        self.service.deduct_credit(user_id, is_guest=False, amount=10)
        
        # Get status
        status = self.service.get_credit_status(user_id, is_guest=False)
        
        assert status.available_credits == settings.credit_system.max_registered_credits - 10
        assert status.max_credits == settings.credit_system.max_registered_credits
        assert status.is_guest is False
        assert status.can_reset is True
        assert status.next_reset_time is not None
        assert isinstance(status.next_reset_time, datetime)
    
    @patch('app.services.credit_service.datetime')
    def test_auto_reset_credits(self, mock_datetime):
        """Test automatic credit reset for registered users"""
        user_id = "auth0|123456"
        
        # Set up mock time
        base_time = datetime(2025, 7, 24, 12, 0, 0)
        mock_datetime.utcnow.return_value = base_time
        
        # Create user and deduct credits
        self.service.deduct_credit(user_id, is_guest=False, amount=20)
        credits = self.service.get_user_credits(user_id, is_guest=False)
        assert credits.available_credits == settings.credit_system.max_registered_credits - 20
        
        # Advance time past reset interval
        future_time = base_time + timedelta(hours=settings.credit_system.credit_reset_interval_hours + 1)
        mock_datetime.utcnow.return_value = future_time
        
        # Check credits (should trigger auto-reset)
        available = self.service.check_credits(user_id, is_guest=False)
        assert available == settings.credit_system.max_registered_credits
    
    def test_transaction_logging(self):
        """Test that transactions are properly logged"""
        user_id = "auth0|123456"
        
        # Perform various operations
        self.service.get_user_credits(user_id, is_guest=False)  # Allocate
        self.service.deduct_credit(user_id, is_guest=False, amount=5)  # Deduct
        self.service.reset_credits(user_id)  # Reset
        
        # Get transactions
        transactions = self.service.get_user_transactions(user_id)
        
        assert len(transactions) == 3
        
        # Check transaction types (in reverse chronological order)
        assert transactions[0].transaction_type == "reset"
        assert transactions[1].transaction_type == "deduct"
        assert transactions[2].transaction_type == "allocate"
        
        # Check amounts
        assert transactions[0].amount > 0  # Reset amount
        assert transactions[1].amount == 5  # Deduct amount
        assert transactions[2].amount == settings.credit_system.max_registered_credits  # Allocate amount
    
    def test_transaction_limit(self):
        """Test that transaction history is limited to prevent memory issues"""
        user_id = "auth0|123456"
        
        # Create many transactions
        for i in range(15000):
            self.service._log_transaction(f"user_{i}", "deduct", 1, "test")
        
        # Should be limited to 5000 after cleanup
        assert len(self.service._credit_transactions) == 5000
    
    def test_deduct_credit_zero_amount(self):
        """Test deducting zero credits"""
        user_id = "guest_123"
        initial_credits = self.service.check_credits(user_id, is_guest=True)
        
        # Deduct 0 credits
        result = self.service.deduct_credit(user_id, is_guest=True, amount=0)
        assert result is True
        
        # Credits should remain unchanged
        final_credits = self.service.check_credits(user_id, is_guest=True)
        assert final_credits == initial_credits
    
    def test_deduct_credit_negative_amount(self):
        """Test deducting negative credits (should fail)"""
        user_id = "guest_123"
        initial_credits = self.service.check_credits(user_id, is_guest=True)
        
        # Try to deduct negative credits
        result = self.service.deduct_credit(user_id, is_guest=True, amount=-5)
        assert result is False
        
        # Credits should remain unchanged
        final_credits = self.service.check_credits(user_id, is_guest=True)
        assert final_credits == initial_credits
    
    def test_guest_user_cannot_reset_credits(self):
        """Test that guest users cannot have their credits reset"""
        user_id = "guest_123"
        
        # Deduct some credits
        self.service.deduct_credit(user_id, is_guest=True, amount=5)
        credits_before = self.service.get_user_credits(user_id, is_guest=True)
        
        # Try to reset (should be ignored)
        self.service.reset_credits(user_id)
        
        # Credits should remain the same
        credits_after = self.service.get_user_credits(user_id, is_guest=True)
        assert credits_after.available_credits == credits_before.available_credits
    
    def test_concurrent_credit_operations(self):
        """Test concurrent credit operations on the same user"""
        user_id = "auth0|123456"
        
        # Simulate concurrent deductions
        results = []
        for i in range(10):
            result = self.service.deduct_credit(user_id, is_guest=False, amount=5)
            results.append(result)
        
        # Count successful deductions
        successful_deductions = sum(1 for r in results if r)
        
        # Check final credits
        final_credits = self.service.check_credits(user_id, is_guest=False)
        expected_credits = settings.credit_system.max_registered_credits - (successful_deductions * 5)
        
        assert final_credits == expected_credits
    
    def test_credit_status_with_auto_reset(self):
        """Test credit status calculation when auto-reset is triggered"""
        user_id = "auth0|123456"
        
        with patch('app.services.credit_service.datetime') as mock_datetime:
            # Set up initial time
            base_time = datetime(2025, 7, 24, 12, 0, 0)
            mock_datetime.utcnow.return_value = base_time
            
            # Create user and deduct credits
            self.service.deduct_credit(user_id, is_guest=False, amount=30)
            
            # Advance time past reset interval
            future_time = base_time + timedelta(hours=settings.credit_system.credit_reset_interval_hours + 1)
            mock_datetime.utcnow.return_value = future_time
            
            # Get status (should trigger auto-reset)
            status = self.service.get_credit_status(user_id, is_guest=False)
            
            assert status.available_credits == settings.credit_system.max_registered_credits
            assert status.max_credits == settings.credit_system.max_registered_credits
            assert status.is_guest is False
            assert status.can_reset is True
    
    def test_user_transactions_ordering(self):
        """Test that user transactions are returned in correct order (most recent first)"""
        user_id = "auth0|123456"
        
        # Create user and perform multiple operations with delays
        with patch('app.services.credit_service.datetime') as mock_datetime:
            base_time = datetime(2025, 7, 24, 12, 0, 0)
            
            # First operation
            mock_datetime.utcnow.return_value = base_time
            self.service.get_user_credits(user_id, is_guest=False)
            
            # Second operation
            mock_datetime.utcnow.return_value = base_time + timedelta(minutes=1)
            self.service.deduct_credit(user_id, is_guest=False, amount=10)
            
            # Third operation
            mock_datetime.utcnow.return_value = base_time + timedelta(minutes=2)
            self.service.deduct_credit(user_id, is_guest=False, amount=5)
            
            # Get transactions
            transactions = self.service.get_user_transactions(user_id)
            
            # Should be in reverse chronological order
            assert len(transactions) == 3
            assert transactions[0].transaction_type == "deduct"
            assert transactions[0].amount == 5  # Most recent
            assert transactions[1].transaction_type == "deduct"
            assert transactions[1].amount == 10  # Second most recent
            assert transactions[2].transaction_type == "allocate"  # Oldest
    
    def test_get_user_transactions_limit(self):
        """Test that get_user_transactions respects the limit parameter"""
        user_id = "auth0|123456"
        
        # Create multiple transactions
        for i in range(10):
            self.service.deduct_credit(user_id, is_guest=False, amount=1)
        
        # Get limited transactions
        transactions = self.service.get_user_transactions(user_id, limit=5)
        
        assert len(transactions) <= 5
        
        # Get all transactions
        all_transactions = self.service.get_user_transactions(user_id, limit=100)
        
        assert len(all_transactions) == 11  # 10 deductions + 1 initial allocation