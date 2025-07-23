"""
ProductParserService for validating and processing Gemini API responses.
"""
import json
import re
from typing import Dict, List, Any, Tuple, Optional
from fastapi import HTTPException

from app.models.query import Product, QueryResponse
from app.services.affiliate_service import AffiliateService

class ProductParserService:
    """Service for parsing and validating product data from Gemini API responses."""
    
    def __init__(self):
        """Initialize the ProductParserService."""
        self.affiliate_service = AffiliateService()
    
    def parse_response(self, query: str, response_text: str) -> QueryResponse:
        """
        Parse and validate the JSON response from Gemini API.
        
        Args:
            query: The original user query.
            response_text: The text response from the Gemini API.
            
        Returns:
            QueryResponse: The structured and validated response with product recommendations.
            
        Raises:
            HTTPException: If the response cannot be parsed or validated.
        """
        try:
            # Extract JSON from the response text
            json_text = self._extract_json(response_text)
            
            # Parse the JSON
            data = self._parse_json(json_text)
            
            # Validate the structure
            self._validate_response_structure(data)
            
            # Convert to our response model with validation
            products = self._convert_products(data.get("products", []))
            
            return QueryResponse(
                query=query,
                products=products,
                recommendations_summary=data.get("recommendationsSummary", "")
            )
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error parsing Gemini API response: {str(e)}"
            )
    
    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from the response text, handling various formats.
        
        Args:
            text: The raw text response.
            
        Returns:
            str: The cleaned JSON text.
            
        Raises:
            HTTPException: If no valid JSON can be extracted.
        """
        # Clean the response text to extract only the JSON part
        text = text.strip()
        
        # Handle markdown code blocks
        if "```json" in text or "```" in text:
            # Extract content between ```json and ```
            match = re.search(r'```(?:json)?(.*?)```', text, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # If no code blocks, try to find JSON-like content
        # Look for opening curly brace and corresponding closing brace
        if '{' in text and '}' in text:
            start_idx = text.find('{')
            # Find the matching closing brace
            brace_count = 0
            for i in range(start_idx, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        return text[start_idx:i+1]
        
        # Try a more aggressive approach to find JSON
        # This will attempt to find any valid JSON object in the text
        try:
            for i in range(len(text)):
                if text[i] == '{':
                    for j in range(len(text), i, -1):
                        try:
                            potential_json = text[i:j]
                            json.loads(potential_json)  # Test if it's valid JSON
                            return potential_json
                        except json.JSONDecodeError:
                            continue
        except Exception:
            pass
        
        # If we couldn't extract JSON, return the original text
        # The JSON parser will handle the error if it's not valid JSON
        return text
    
    def _parse_json(self, json_text: str) -> Dict[str, Any]:
        """
        Parse the JSON text into a dictionary.
        
        Args:
            json_text: The JSON text to parse.
            
        Returns:
            Dict[str, Any]: The parsed JSON data.
            
        Raises:
            HTTPException: If the text cannot be parsed as valid JSON.
        """
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            # Log the problematic JSON text for debugging
            print(f"JSON Parse Error: {str(e)}")
            print(f"Problematic JSON text: {json_text[:200]}...")  # Print first 200 chars
            
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse Gemini API response as JSON: {str(e)}"
            )
    
    def _validate_response_structure(self, data: Dict[str, Any]) -> None:
        """
        Validate the structure of the parsed JSON data.
        
        Args:
            data: The parsed JSON data.
            
        Raises:
            HTTPException: If the data structure is invalid.
        """
        # Check if products key exists
        if "products" not in data:
            raise HTTPException(
                status_code=500,
                detail="Invalid response format: 'products' field is missing"
            )
        
        # Check if products is a list
        if not isinstance(data["products"], list):
            raise HTTPException(
                status_code=500,
                detail="Invalid response format: 'products' must be a list"
            )
        
        # Check if recommendationsSummary exists
        if "recommendationsSummary" not in data:
            raise HTTPException(
                status_code=500,
                detail="Invalid response format: 'recommendationsSummary' field is missing"
            )
    
    def _convert_products(self, product_data_list: List[Dict[str, Any]]) -> List[Product]:
        """
        Convert and validate the product data into Product models.
        
        Args:
            product_data_list: List of product data dictionaries.
            
        Returns:
            List[Product]: List of validated Product models.
            
        Raises:
            HTTPException: If any product data is invalid.
        """
        products = []
        
        for i, product_data in enumerate(product_data_list):
            try:
                # Validate required fields
                self._validate_product_fields(product_data, i)
                
                # Convert types and handle potential errors
                price = self._parse_price(product_data.get("price", 0), i)
                rating = self._parse_rating(product_data.get("rating", 0), i)
                
                # Validate and process the link
                validated_link = self._validate_link(product_data.get("link", ""), i)
                
                # Generate affiliate link
                affiliate_link = self.affiliate_service.generate_affiliate_link(validated_link)
                
                # Create the Product object
                product = Product(
                    title=product_data.get("title", ""),
                    price=price,
                    rating=rating,
                    features=self._ensure_list(product_data.get("features", [])),
                    pros=self._ensure_list(product_data.get("pros", [])),
                    cons=self._ensure_list(product_data.get("cons", [])),
                    link=affiliate_link
                )
                
                products.append(product)
                
            except ValueError as e:
                # Log the error but continue processing other products
                # This allows us to return partial results rather than failing completely
                continue
        
        return products
    
    def _validate_product_fields(self, product_data: Dict[str, Any], index: int) -> None:
        """
        Validate that a product has all required fields.
        
        Args:
            product_data: The product data dictionary.
            index: The index of the product in the list.
            
        Raises:
            ValueError: If any required field is missing.
        """
        required_fields = ["title", "price", "rating", "features", "pros", "cons", "link"]
        
        for field in required_fields:
            if field not in product_data:
                raise ValueError(f"Product {index + 1} is missing required field: {field}")
    
    def _parse_price(self, price_value: Any, index: int) -> float:
        """
        Parse and validate the price value.
        
        Args:
            price_value: The price value to parse.
            index: The index of the product in the list.
            
        Returns:
            float: The parsed price value.
            
        Raises:
            ValueError: If the price cannot be parsed as a float or is negative.
        """
        try:
            # Handle string representations with currency symbols
            if isinstance(price_value, str):
                # Remove currency symbols and commas
                price_value = re.sub(r'[₹,]', '', price_value)
                
            price = float(price_value)
            
            # Validate price is non-negative
            if price < 0:
                raise ValueError(f"Product {index + 1} has a negative price")
                
            return price
            
        except (ValueError, TypeError):
            raise ValueError(f"Product {index + 1} has an invalid price format")
    
    def _parse_rating(self, rating_value: Any, index: int) -> float:
        """
        Parse and validate the rating value.
        
        Args:
            rating_value: The rating value to parse.
            index: The index of the product in the list.
            
        Returns:
            float: The parsed rating value.
            
        Raises:
            ValueError: If the rating cannot be parsed as a float or is out of range.
        """
        try:
            rating = float(rating_value)
            
            # Validate rating is between 0 and 5
            if rating < 0 or rating > 5:
                raise ValueError(f"Product {index + 1} has a rating outside the valid range (0-5)")
                
            return rating
            
        except (ValueError, TypeError):
            raise ValueError(f"Product {index + 1} has an invalid rating format")
    
    def _ensure_list(self, value: Any) -> List[str]:
        """
        Ensure the value is a list of strings.
        
        Args:
            value: The value to check.
            
        Returns:
            List[str]: The value as a list of strings.
        """
        if not isinstance(value, list):
            return []
        
        # Convert all items to strings
        return [str(item) for item in value]
    
    def _validate_link(self, link: str, index: int) -> str:
        """
        Validate that a link is properly formatted.
        
        Args:
            link: The link to validate.
            index: The index of the product in the list.
            
        Returns:
            str: The validated link.
            
        Raises:
            ValueError: If the link is not a valid URL.
        """
        if not link:
            return ""
            
        # Basic URL validation
        if not link.startswith(("http://", "https://")):
            link = f"https://{link}"
            
        # Check if it's an Indian e-commerce site (for this application's requirements)
        valid_domains = ["amazon.in", "flipkart.com", "myntra.com", "snapdeal.com", "shopclues.com"]
        if not any(domain in link for domain in valid_domains):
            # Not raising an error here, just returning the link as is
            # This is a soft validation that doesn't block the response
            pass
            
        return link