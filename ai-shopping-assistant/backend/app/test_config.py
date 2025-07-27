"""
Tests for the configuration system
"""
import os
import pytest
from unittest.mock import patch
from app.config import CreditSystemConfig, Settings


class TestCreditSystemConfig:
    """Test the credit system configuration"""
    
    def test_default_values(self):
        """Test that default values are set correctly"""
        config = CreditSystemConfig()
        assert config.max_guest_credits == 10
        assert config.max_registered_credits == 50
        assert config.credit_reset_interval_hours == 24
        assert config.cache_validity_minutes == 60
    
    def test_from_env_with_defaults(self):
        """Test loading from environment with default values"""
        config = CreditSystemConfig.from_env()
        assert config.max_guest_credits >= 0
        assert config.max_registered_credits >= 0
        assert config.credit_reset_interval_hours >= 0
        assert config.cache_validity_minutes >= 0
    
    @patch.dict(os.environ, {
        'MAX_GUEST_CREDITS': '15',
        'MAX_REGISTERED_CREDITS': '100',
        'CREDIT_RESET_INTERVAL_HOURS': '12',
        'CACHE_VALIDITY_MINUTES': '30'
    })
    def test_from_env_with_custom_values(self):
        """Test loading custom values from environment"""
        config = CreditSystemConfig.from_env()
        assert config.max_guest_credits == 15
        assert config.max_registered_credits == 100
        assert config.credit_reset_interval_hours == 12
        assert config.cache_validity_minutes == 30
    
    def test_settings_integration(self):
        """Test that the credit system config is properly integrated into Settings"""
        settings = Settings()
        assert hasattr(settings, 'credit_system')
        assert isinstance(settings.credit_system, CreditSystemConfig)
        assert settings.credit_system.max_guest_credits > 0
        assert settings.credit_system.max_registered_credits > 0


if __name__ == "__main__":
    # Run a simple test to verify configuration loading
    print("Testing configuration system...")
    
    # Test default configuration
    config = CreditSystemConfig()
    print(f"Default config: {config}")
    
    # Test environment-based configuration
    env_config = CreditSystemConfig.from_env()
    print(f"Environment config: {env_config}")
    
    # Test settings integration
    settings = Settings()
    print(f"Settings credit config: {settings.credit_system}")
    
    print("Configuration system test completed successfully!")