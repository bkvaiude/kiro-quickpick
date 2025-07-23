"""
ContextManagerService for managing conversation context and extracting product criteria.
"""
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from app.models.query import ConversationContext, ChatMessage, ProductCriteria


class ContextManagerService:
    """
    Service for managing conversation context, extracting product criteria,
    and maintaining conversation history.
    """
    
    def __init__(self):
        """Initialize the ContextManagerService."""
        # Common product categories for pattern matching
        self.product_categories = [
            "phone", "smartphone", "mobile", "laptop", "computer", "tablet", 
            "headphone", "earphone", "earbud", "tv", "television", "camera",
            "speaker", "smartwatch", "watch", "refrigerator", "fridge", 
            "washing machine", "air conditioner", "ac", "microwave"
        ]
        
        # Common marketplaces
        self.marketplaces = ["amazon", "flipkart", "myntra", "ajio", "croma", "reliance digital"]
        
        # Common brands by category
        self.brands = {
            "phone": ["samsung", "apple", "xiaomi", "redmi", "oneplus", "vivo", "oppo", "realme", "poco", "iqoo", "motorola", "nokia"],
            "laptop": ["hp", "dell", "lenovo", "asus", "acer", "apple", "msi", "microsoft", "lg", "samsung"],
            "headphone": ["boat", "sony", "jbl", "apple", "samsung", "oneplus", "realme", "noise", "skullcandy", "sennheiser", "bose"],
            "tv": ["samsung", "lg", "sony", "mi", "oneplus", "vu", "tcl", "thomson", "panasonic", "philips"],
        }
        
        # Maximum number of messages to keep in context
        self.max_context_messages = 10
    
    def add_message(self, context: Optional[ConversationContext], text: str, sender: str) -> ConversationContext:
        """
        Add a new message to the conversation context.
        
        Args:
            context: The current conversation context or None if this is the first message.
            text: The message text.
            sender: The message sender ('user' or 'system').
            
        Returns:
            ConversationContext: The updated conversation context.
        """
        # Initialize context if None
        if context is None:
            context = ConversationContext(messages=[], last_query=None, last_product_criteria=None)
        
        # Create a new message
        message = ChatMessage(
            id=str(uuid.uuid4()),
            text=text,
            sender=sender,
            timestamp=datetime.now().isoformat()
        )
        
        # Add the message to the context
        context.messages.append(message)
        
        # Limit the number of messages in context
        if len(context.messages) > self.max_context_messages:
            context.messages = context.messages[-self.max_context_messages:]
        
        # Update last query if this is a user message
        if sender == "user":
            context.last_query = text
            
            # Extract product criteria from the query
            extracted_criteria = self.extract_product_criteria(text, context.last_product_criteria)
            if extracted_criteria:
                context.last_product_criteria = extracted_criteria
        
        return context
    
    def extract_product_criteria(self, query: str, existing_criteria: Optional[ProductCriteria] = None) -> ProductCriteria:
        """
        Extract product criteria from a user query.
        
        Args:
            query: The user's query text.
            existing_criteria: Existing product criteria to update, if any.
            
        Returns:
            ProductCriteria: The extracted or updated product criteria.
        """
        # Initialize with existing criteria or create new
        criteria = existing_criteria or ProductCriteria()
        
        # Convert query to lowercase for easier pattern matching
        query_lower = query.lower()
        
        # Extract category
        if not criteria.category:
            for category in self.product_categories:
                if category in query_lower:
                    criteria.category = category
                    break
        
        # Extract price range
        if not criteria.price_range:
            criteria.price_range = {}
            
        # Look for price patterns like "under ₹20000" or "below 20k" or "between 10000 and 20000"
        under_pattern = r'under (?:₹|rs\.?|inr)?\s?(\d+(?:\.\d+)?)[k]?'
        under_match = re.search(under_pattern, query_lower)
        if under_match:
            price = float(under_match.group(1))
            if 'k' in under_match.group(0).lower():
                price *= 1000
            criteria.price_range["max"] = price
        
        # Look for "above X" or "more than X" patterns
        above_pattern = r'(?:above|more than) (?:₹|rs\.?|inr)?\s?(\d+(?:\.\d+)?)[k]?'
        above_match = re.search(above_pattern, query_lower)
        if above_match:
            price = float(above_match.group(1))
            if 'k' in above_match.group(0).lower():
                price *= 1000
            criteria.price_range["min"] = price
        
        # Look for "between X and Y" patterns
        between_pattern = r'between (?:₹|rs\.?|inr)?\s?(\d+(?:\.\d+)?)[k]? and (?:₹|rs\.?|inr)?\s?(\d+(?:\.\d+)?)[k]?'
        between_match = re.search(between_pattern, query_lower)
        if between_match:
            min_price = float(between_match.group(1))
            max_price = float(between_match.group(2))
            if 'k' in between_match.group(0).lower().split('and')[0]:
                min_price *= 1000
            if 'k' in between_match.group(0).lower().split('and')[1]:
                max_price *= 1000
            criteria.price_range["min"] = min_price
            criteria.price_range["max"] = max_price
        
        # Extract features (common specifications)
        features = []
        
        # RAM pattern (e.g., "8GB RAM" or "8 GB of RAM")
        ram_pattern = r'(\d+)\s?(?:gb|gig|gigabyte)s?\s(?:of\s)?ram'
        ram_match = re.search(ram_pattern, query_lower)
        if ram_match:
            features.append(f"{ram_match.group(1)}GB RAM")
        
        # Storage pattern (e.g., "128GB storage" or "1TB SSD")
        storage_pattern = r'(\d+)\s?(?:gb|tb|terabyte)s?\s(?:storage|ssd|hdd|memory)'
        storage_match = re.search(storage_pattern, query_lower)
        if storage_match:
            unit = "TB" if "tb" in storage_match.group(0).lower() else "GB"
            features.append(f"{storage_match.group(1)}{unit} Storage")
        
        # Camera pattern (e.g., "48MP camera")
        camera_pattern = r'(\d+)\s?(?:mp|megapixel)s?\s(?:camera)'
        camera_match = re.search(camera_pattern, query_lower)
        if camera_match:
            features.append(f"{camera_match.group(1)}MP Camera")
        
        # Display pattern (e.g., "6.5 inch display" or "15.6 inch screen")
        display_pattern = r'(\d+(?:\.\d+)?)\s?(?:inch|"|inches)\s(?:display|screen)'
        display_match = re.search(display_pattern, query_lower)
        if display_match:
            features.append(f"{display_match.group(1)}\" Display")
        
        # Battery pattern (e.g., "5000mAh battery")
        battery_pattern = r'(\d+)\s?(?:mah)\s(?:battery)'
        battery_match = re.search(battery_pattern, query_lower)
        if battery_match:
            features.append(f"{battery_match.group(1)}mAh Battery")
        
        # Processor pattern (e.g., "Snapdragon 888" or "i7 processor")
        processor_patterns = [
            r'(snapdragon\s\d+)',
            r'(dimensity\s\d+)',
            r'(exynos\s\d+)',
            r'(i\d+(?:-\d+)?)',
            r'(ryzen\s\d+)'
        ]
        for pattern in processor_patterns:
            processor_match = re.search(pattern, query_lower)
            if processor_match:
                features.append(f"{processor_match.group(1).title()} Processor")
                break
        
        # Check for 5G
        if "5g" in query_lower:
            features.append("5G Support")
        
        # Update features if we found any
        if features:
            if criteria.features:
                # Add new features without duplicates
                existing_features = set(criteria.features)
                for feature in features:
                    if feature not in existing_features:
                        criteria.features.append(feature)
            else:
                criteria.features = features
        
        # Extract brand
        if not criteria.brand:
            # Get all brands from all categories
            all_brands = []
            for brand_list in self.brands.values():
                all_brands.extend(brand_list)
            
            # Remove duplicates
            all_brands = list(set(all_brands))
            
            # Check if any brand is mentioned
            for brand in all_brands:
                if re.search(r'\b' + brand + r'\b', query_lower):
                    criteria.brand = brand
                    break
        
        # Extract marketplace
        if not criteria.marketplace:
            for marketplace in self.marketplaces:
                if marketplace in query_lower:
                    criteria.marketplace = marketplace
                    break
        
        return criteria
    
    def generate_context_prompt(self, context: ConversationContext) -> str:
        """
        Generate a prompt that includes relevant context from previous interactions.
        
        Args:
            context: The conversation context.
            
        Returns:
            str: A prompt that summarizes the conversation context.
        """
        if not context or not context.last_product_criteria:
            return ""
        
        prompt_parts = ["Based on our conversation, I understand you're looking for:"]
        
        criteria = context.last_product_criteria
        
        # Add category
        if criteria.category:
            prompt_parts.append(f"- Product type: {criteria.category}")
        
        # Add brand
        if criteria.brand:
            prompt_parts.append(f"- Brand preference: {criteria.brand}")
        
        # Add price range
        if criteria.price_range:
            price_range_str = ""
            if "min" in criteria.price_range and "max" in criteria.price_range:
                price_range_str = f"between ₹{criteria.price_range['min']} and ₹{criteria.price_range['max']}"
            elif "min" in criteria.price_range:
                price_range_str = f"above ₹{criteria.price_range['min']}"
            elif "max" in criteria.price_range:
                price_range_str = f"under ₹{criteria.price_range['max']}"
            
            if price_range_str:
                prompt_parts.append(f"- Price range: {price_range_str}")
        
        # Add features
        if criteria.features and len(criteria.features) > 0:
            prompt_parts.append(f"- Key features: {', '.join(criteria.features)}")
        
        # Add marketplace
        if criteria.marketplace:
            prompt_parts.append(f"- Preferred marketplace: {criteria.marketplace}")
        
        # Join all parts
        return "\n".join(prompt_parts)
    
    def merge_context_with_query(self, query: str, context: Optional[ConversationContext] = None) -> str:
        """
        Merge the user's query with relevant context from previous interactions.
        
        Args:
            query: The user's current query.
            context: The conversation context.
            
        Returns:
            str: The enhanced query with context.
        """
        if not context or not context.last_product_criteria:
            return query
        
        context_prompt = self.generate_context_prompt(context)
        if not context_prompt:
            return query
        
        # Combine the context with the query
        enhanced_query = f"{context_prompt}\n\nCurrent query: {query}\n\nPlease provide recommendations based on all the information above."
        
        return enhanced_query