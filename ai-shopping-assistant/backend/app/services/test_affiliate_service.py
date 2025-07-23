"""
Tests for the AffiliateService.
"""
import unittest
from unittest.mock import patch, MagicMock
from app.services.affiliate_service import AffiliateService

class TestAffiliateService(unittest.TestCase):
    """Test cases for the AffiliateService."""
    
    @patch('app.services.affiliate_service.settings')
    def test_generate_affiliate_link_amazon(self, mock_settings):
        """Test generating an affiliate link for Amazon."""
        # Mock settings
        mock_settings.affiliate_tag = "myaffiliatetagtest-21"
        mock_settings.affiliate_program = "amazon"
        
        # Create service instance
        service = AffiliateService()
        
        # Test Amazon URL
        original_url = "https://www.amazon.in/product/dp/B0ABCDEF12"
        expected_url = "https://www.amazon.in/product/dp/B0ABCDEF12?tag=myaffiliatetagtest-21"
        
        result = service.generate_affiliate_link(original_url)
        self.assertEqual(result, expected_url)
    
    @patch('app.services.affiliate_service.settings')
    def test_generate_affiliate_link_flipkart(self, mock_settings):
        """Test generating an affiliate link for Flipkart."""
        # Mock settings
        mock_settings.affiliate_tag = "myaffiliatetagtest"
        mock_settings.affiliate_program = "flipkart"
        
        # Create service instance
        service = AffiliateService()
        
        # Test Flipkart URL
        original_url = "https://www.flipkart.com/product/p/ABCDE"
        expected_url = "https://www.flipkart.com/product/p/ABCDE?affid=myaffiliatetagtest"
        
        result = service.generate_affiliate_link(original_url)
        self.assertEqual(result, expected_url)
    
    @patch('app.services.affiliate_service.settings')
    def test_generate_affiliate_link_with_existing_params(self, mock_settings):
        """Test generating an affiliate link for a URL that already has query parameters."""
        # Mock settings
        mock_settings.affiliate_tag = "myaffiliatetagtest-21"
        mock_settings.affiliate_program = "amazon"
        
        # Create service instance
        service = AffiliateService()
        
        # Test URL with existing parameters
        original_url = "https://www.amazon.in/product/dp/B0ABCDEF12?param1=value1&param2=value2"
        expected_url = "https://www.amazon.in/product/dp/B0ABCDEF12?param1=value1&param2=value2&tag=myaffiliatetagtest-21"
        
        result = service.generate_affiliate_link(original_url)
        self.assertEqual(result, expected_url)
    
    @patch('app.services.affiliate_service.settings')
    def test_generate_affiliate_link_unsupported_domain(self, mock_settings):
        """Test generating an affiliate link for an unsupported domain."""
        # Mock settings
        mock_settings.affiliate_tag = "myaffiliatetagtest-21"
        mock_settings.affiliate_program = "amazon"
        
        # Create service instance
        service = AffiliateService()
        
        # Test unsupported domain
        original_url = "https://www.example.com/product/123"
        
        result = service.generate_affiliate_link(original_url)
        self.assertEqual(result, original_url)  # Should return the original URL unchanged
    
    @patch('app.services.affiliate_service.settings')
    def test_generate_affiliate_link_empty_url(self, mock_settings):
        """Test generating an affiliate link with an empty URL."""
        # Mock settings
        mock_settings.affiliate_tag = "myaffiliatetagtest-21"
        mock_settings.affiliate_program = "amazon"
        
        # Create service instance
        service = AffiliateService()
        
        # Test empty URL
        original_url = ""
        
        result = service.generate_affiliate_link(original_url)
        self.assertEqual(result, "")  # Should return the empty string
    
    @patch('app.services.affiliate_service.settings')
    def test_generate_affiliate_link_no_tag(self, mock_settings):
        """Test generating an affiliate link when no affiliate tag is configured."""
        # Mock settings with empty affiliate tag
        mock_settings.affiliate_tag = ""
        mock_settings.affiliate_program = "amazon"
        
        # Create service instance
        service = AffiliateService()
        
        # Test URL
        original_url = "https://www.amazon.in/product/dp/B0ABCDEF12"
        
        result = service.generate_affiliate_link(original_url)
        self.assertEqual(result, original_url)  # Should return the original URL unchanged

if __name__ == "__main__":
    unittest.main()