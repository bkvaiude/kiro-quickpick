"""
Tests for the ContextManagerService.
"""
import pytest
from app.models.query import ConversationContext, ProductCriteria
from app.services.context_manager_service import ContextManagerService


class TestContextManagerService:
    """Test cases for the ContextManagerService."""
    
    def setup_method(self):
        """Set up the test environment."""
        self.context_manager = ContextManagerService()
    
    def test_add_message(self):
        """Test adding messages to the conversation context."""
        # Start with no context
        context = None
        
        # Add a user message
        context = self.context_manager.add_message(context, "I'm looking for a smartphone under ₹15000", "user")
        
        # Verify context was created and message was added
        assert context is not None
        assert len(context.messages) == 1
        assert context.messages[0].sender == "user"
        assert context.messages[0].text == "I'm looking for a smartphone under ₹15000"
        assert context.last_query == "I'm looking for a smartphone under ₹15000"
        
        # Add a system message
        context = self.context_manager.add_message(context, "Here are some recommendations...", "system")
        
        # Verify message was added
        assert len(context.messages) == 2
        assert context.messages[1].sender == "system"
        assert context.last_query == "I'm looking for a smartphone under ₹15000"  # Should not change
    
    def test_extract_product_criteria_category(self):
        """Test extracting product category from queries."""
        # Test with a simple query
        criteria = self.context_manager.extract_product_criteria("I want to buy a new phone")
        assert criteria.category == "phone"
        
        # Test with a different category
        criteria = self.context_manager.extract_product_criteria("Looking for a good laptop")
        assert criteria.category == "laptop"
        
        # Test with multiple categories (should pick the first one)
        criteria = self.context_manager.extract_product_criteria("Should I buy a phone or a laptop?")
        assert criteria.category == "phone"
    
    def test_extract_product_criteria_price(self):
        """Test extracting price ranges from queries."""
        # Test "under X" pattern
        criteria = self.context_manager.extract_product_criteria("I need a phone under ₹15000")
        assert criteria.price_range is not None
        assert criteria.price_range.get("max") == 15000
        
        # Test "above X" pattern
        criteria = self.context_manager.extract_product_criteria("Looking for phones above ₹20000")
        assert criteria.price_range is not None
        assert criteria.price_range.get("min") == 20000
        
        # Test "between X and Y" pattern
        criteria = self.context_manager.extract_product_criteria("Find me laptops between ₹30000 and ₹50000")
        assert criteria.price_range is not None
        assert criteria.price_range.get("min") == 30000
        assert criteria.price_range.get("max") == 50000
        
        # Test with "k" notation
        criteria = self.context_manager.extract_product_criteria("I want a phone under 15k")
        assert criteria.price_range is not None
        assert criteria.price_range.get("max") == 15000
    
    def test_extract_product_criteria_features(self):
        """Test extracting product features from queries."""
        # Test RAM extraction
        criteria = self.context_manager.extract_product_criteria("I want a phone with 8GB RAM")
        assert criteria.features is not None
        assert "8GB RAM" in criteria.features
        
        # Test storage extraction
        criteria = self.context_manager.extract_product_criteria("Looking for a laptop with 512GB SSD")
        assert criteria.features is not None
        assert "512GB Storage" in criteria.features
        
        # Test camera extraction
        criteria = self.context_manager.extract_product_criteria("I need a phone with 48MP camera")
        assert criteria.features is not None
        assert "48MP Camera" in criteria.features
        
        # Test multiple features
        criteria = self.context_manager.extract_product_criteria("Find me a phone with 8GB RAM and 5000mAh battery")
        assert criteria.features is not None
        assert "8GB RAM" in criteria.features
        assert "5000mAh Battery" in criteria.features
        
        # Test 5G feature
        criteria = self.context_manager.extract_product_criteria("I want a 5G phone")
        assert criteria.features is not None
        assert "5G Support" in criteria.features
    
    def test_extract_product_criteria_brand(self):
        """Test extracting brand from queries."""
        # Test with a phone brand
        criteria = self.context_manager.extract_product_criteria("I'm looking for a Samsung phone")
        assert criteria.brand == "samsung"
        
        # Test with a laptop brand
        criteria = self.context_manager.extract_product_criteria("I want to buy a Dell laptop")
        assert criteria.brand == "dell"
    
    def test_extract_product_criteria_marketplace(self):
        """Test extracting marketplace from queries."""
        # Test with Amazon
        criteria = self.context_manager.extract_product_criteria("Find me phones on Amazon")
        assert criteria.marketplace == "amazon"
        
        # Test with Flipkart
        criteria = self.context_manager.extract_product_criteria("I want to buy from Flipkart")
        assert criteria.marketplace == "flipkart"
    
    def test_update_existing_criteria(self):
        """Test updating existing criteria with new information."""
        # Start with some existing criteria
        existing = ProductCriteria(
            category="phone",
            price_range={"max": 20000},
            features=["8GB RAM"]
        )
        
        # Update with new information
        criteria = self.context_manager.extract_product_criteria(
            "I want it to have a 48MP camera and be from Samsung",
            existing
        )
        
        # Verify the criteria was updated correctly
        assert criteria.category == "phone"  # Unchanged
        assert criteria.price_range.get("max") == 20000  # Unchanged
        assert "8GB RAM" in criteria.features  # Kept from existing
        assert "48MP Camera" in criteria.features  # Added new
        assert criteria.brand == "samsung"  # Added new
    
    def test_generate_context_prompt(self):
        """Test generating a context prompt from conversation context."""
        # Create a context with product criteria
        criteria = ProductCriteria(
            category="phone",
            price_range={"min": 15000, "max": 25000},
            features=["8GB RAM", "5G Support"],
            brand="samsung",
            marketplace="amazon"
        )
        
        context = ConversationContext(
            messages=[],
            last_query="What about with better camera?",
            last_product_criteria=criteria
        )
        
        # Generate the context prompt
        prompt = self.context_manager.generate_context_prompt(context)
        
        # Verify the prompt contains all the criteria
        assert "Product type: phone" in prompt
        assert "Brand preference: samsung" in prompt
        assert "Price range:" in prompt
        assert "15000" in prompt
        assert "25000" in prompt
        assert "Key features: 8GB RAM, 5G Support" in prompt
        assert "Preferred marketplace: amazon" in prompt
    
    def test_merge_context_with_query(self):
        """Test merging context with a new query."""
        # Create a context with product criteria
        criteria = ProductCriteria(
            category="phone",
            price_range={"max": 15000},
            features=["8GB RAM"]
        )
        
        context = ConversationContext(
            messages=[],
            last_query="I want a phone under 15000 with 8GB RAM",
            last_product_criteria=criteria
        )
        
        # Merge with a new query
        enhanced_query = self.context_manager.merge_context_with_query("What about with 5G?", context)
        
        # Verify the enhanced query contains both the context and the new query
        assert "Product type: phone" in enhanced_query
        assert "Price range: under ₹15000" in enhanced_query
        assert "Key features: 8GB RAM" in enhanced_query
        assert "Current query: What about with 5G?" in enhanced_query
    
    def test_max_context_messages(self):
        """Test that the context maintains only the maximum number of messages."""
        # Create a new context
        context = None
        
        # Add more messages than the maximum
        for i in range(15):  # Assuming max_context_messages is 10
            context = self.context_manager.add_message(context, f"Message {i}", "user" if i % 2 == 0 else "system")
        
        # Verify that only the last max_context_messages are kept
        assert len(context.messages) == self.context_manager.max_context_messages
        assert context.messages[0].text == f"Message {15 - self.context_manager.max_context_messages}"