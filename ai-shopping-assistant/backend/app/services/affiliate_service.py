"""
AffiliateService for generating product links with affiliate tags.
"""
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import Dict, Optional
from app.config import settings

class AffiliateService:
    """Service for generating affiliate links for various e-commerce platforms."""
    
    def __init__(self):
        """Initialize the AffiliateService with configuration from environment variables."""
        self.affiliate_tag = settings.affiliate_tag
        self.affiliate_program = settings.affiliate_program
        
        # Mapping of domains to their affiliate parameter names
        self.affiliate_params = {
            "amazon.in": "tag",
            "flipkart.com": "affid",
            # Add more e-commerce platforms as needed
        }
    
    def generate_affiliate_link(self, product_url: str) -> str:
        """
        Generate an affiliate link by adding the appropriate affiliate tag to the URL.
        
        Args:
            product_url: The original product URL.
            
        Returns:
            str: The product URL with affiliate tag added.
        """
        if not product_url or not self.affiliate_tag:
            return product_url
        
        try:
            # Parse the URL
            parsed_url = urlparse(product_url)
            
            # Check if this is a supported domain
            domain = self._extract_domain(parsed_url.netloc)
            if not domain or domain not in self.affiliate_params:
                return product_url
            
            # Get the appropriate parameter name for this domain
            param_name = self.affiliate_params[domain]
            
            # Parse the query string
            query_params = parse_qs(parsed_url.query)
            
            # Add or update the affiliate tag
            query_params[param_name] = [self.affiliate_tag]
            
            # Rebuild the query string
            new_query = urlencode(query_params, doseq=True)
            
            # Rebuild the URL with the new query string
            new_url = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                new_query,
                parsed_url.fragment
            ))
            
            return new_url
            
        except Exception:
            # If any error occurs, return the original URL
            return product_url
    
    def _extract_domain(self, netloc: str) -> Optional[str]:
        """
        Extract the base domain from a netloc string.
        
        Args:
            netloc: The network location part of a URL (e.g., 'www.amazon.in').
            
        Returns:
            Optional[str]: The base domain if it's a supported e-commerce site, None otherwise.
        """
        # Remove port if present
        if ":" in netloc:
            netloc = netloc.split(":", 1)[0]
        
        # Check for supported domains
        for domain in self.affiliate_params.keys():
            if domain in netloc:
                return domain
        
        return None
    
    def is_supported_domain(self, url: str) -> bool:
        """
        Check if the URL is from a supported e-commerce domain.
        
        Args:
            url: The URL to check.
            
        Returns:
            bool: True if the domain is supported, False otherwise.
        """
        try:
            parsed_url = urlparse(url)
            domain = self._extract_domain(parsed_url.netloc)
            return domain is not None
        except Exception:
            return False