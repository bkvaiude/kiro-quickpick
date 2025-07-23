from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class ProductCriteria(BaseModel):
    """Model for storing extracted product criteria from previous queries."""
    category: Optional[str] = None
    price_range: Optional[Dict[str, float]] = None  # {"min": float, "max": float}
    features: Optional[List[str]] = None
    brand: Optional[str] = None
    marketplace: Optional[str] = None


class ChatMessage(BaseModel):
    """Model for a single chat message in the conversation history."""
    id: str
    text: str
    sender: str = Field(..., description="Either 'user' or 'system'")
    timestamp: str


class ConversationContext(BaseModel):
    """Model for the conversation context including message history and extracted criteria."""
    messages: List[ChatMessage] = Field(default_factory=list)
    last_query: Optional[str] = None
    last_product_criteria: Optional[ProductCriteria] = None


class QueryRequest(BaseModel):
    """Model for the query request from the frontend."""
    query: str = Field(..., description="The user's natural language query")
    conversation_context: Optional[ConversationContext] = None


class Product(BaseModel):
    """Model for a product recommendation."""
    title: str
    price: float
    rating: float
    features: List[str]
    pros: List[str]
    cons: List[str]
    link: str


class QueryResponse(BaseModel):
    """Model for the response to a query request."""
    query: str
    products: List[Product]
    recommendations_summary: str
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None