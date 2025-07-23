# AI Shopping Assistant API Documentation

This document provides detailed information about the API endpoints available in the AI Shopping Assistant backend.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://ai-shopping-assistant-api.onrender.com`

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

## API Endpoints

### Health Check

#### `GET /`

Returns the API status and version information.

**Response**:
```json
{
  "message": "Welcome to AI Shopping Assistant API",
  "status": "healthy",
  "version": "0.1.0"
}
```

#### `GET /health`

Simple health check endpoint.

**Response**:
```json
{
  "status": "healthy"
}
```

### Query Processing

#### `POST /api/query`

Process a natural language query and return product recommendations.

**Request Body**:
```json
{
  "query": "string",
  "conversation_context": {
    "messages": [
      {
        "id": "string",
        "text": "string",
        "sender": "user | system",
        "timestamp": "string (ISO format)"
      }
    ],
    "last_query": "string (optional)",
    "last_product_criteria": {
      "category": "string (optional)",
      "price_range": {
        "min": "number (optional)",
        "max": "number (optional)"
      },
      "features": ["string (optional)"],
      "brand": "string (optional)",
      "marketplace": "string (optional)"
    }
  }
}
```

**Response**:
```json
{
  "query": "string",
  "products": [
    {
      "title": "string",
      "price": "number",
      "rating": "number",
      "features": ["string"],
      "pros": ["string"],
      "cons": ["string"],
      "link": "string"
    }
  ],
  "recommendations_summary": "string",
  "error": "string (optional)"
}
```

**Example Request**:
```json
{
  "query": "Tell me the best 5G phone under ₹12,000 with 8GB RAM from Amazon India",
  "conversation_context": {
    "messages": []
  }
}
```

**Example Response**:
```json
{
  "query": "Tell me the best 5G phone under ₹12,000 with 8GB RAM from Amazon India",
  "products": [
    {
      "title": "Redmi 12 5G",
      "price": 11999,
      "rating": 4.2,
      "features": [
        "8GB RAM + 128GB Storage",
        "Snapdragon 4 Gen 2",
        "5000mAh Battery",
        "50MP Dual Camera"
      ],
      "pros": [
        "Good performance for the price",
        "Excellent battery life",
        "Clean MIUI interface"
      ],
      "cons": [
        "Average camera quality",
        "Plastic build",
        "No fast charging"
      ],
      "link": "https://www.amazon.in/Redmi-12-5G-8GB-128GB/dp/B0C9JFHBK2?tag=myaffiliateID"
    },
    {
      "title": "Realme Narzo 60x 5G",
      "price": 11999,
      "rating": 4.0,
      "features": [
        "8GB RAM + 128GB Storage",
        "MediaTek Dimensity 6100+",
        "5000mAh Battery",
        "50MP AI Camera"
      ],
      "pros": [
        "Fast 33W charging",
        "Good display quality",
        "Sleek design"
      ],
      "cons": [
        "Average performance",
        "Bloatware issues",
        "Limited software updates"
      ],
      "link": "https://www.amazon.in/Realme-Narzo-60x-5G/dp/B0CGXF7Z5L?tag=myaffiliateID"
    },
    {
      "title": "Poco M6 Pro 5G",
      "price": 11999,
      "rating": 4.1,
      "features": [
        "8GB RAM + 128GB Storage",
        "Snapdragon 4 Gen 2",
        "5000mAh Battery",
        "50MP AI Dual Camera"
      ],
      "pros": [
        "Good performance",
        "Clean software experience",
        "Decent camera for the price"
      ],
      "cons": [
        "Slow charging",
        "Average build quality",
        "No ultra-wide camera"
      ],
      "link": "https://www.amazon.in/Poco-M6-Pro-5G/dp/B0CBNVZ3QW?tag=myaffiliateID"
    }
  ],
  "recommendations_summary": "Based on your requirements for a 5G phone under ₹12,000 with 8GB RAM, the Redmi 12 5G offers the best overall value with good performance from the Snapdragon 4 Gen 2 processor and excellent battery life. The Poco M6 Pro 5G is a close second with similar specifications but a slightly better camera experience. The Realme Narzo 60x 5G stands out with its faster 33W charging but falls behind in overall performance."
}
```

**Error Responses**:

- **400 Bad Request**: Invalid request format
  ```json
  {
    "detail": "Invalid request format"
  }
  ```

- **500 Internal Server Error**: Server-side error
  ```json
  {
    "detail": "Error processing query: [error message]"
  }
  ```

## Rate Limiting

Currently, there is no explicit rate limiting implemented. However, the Gemini API has its own rate limits that will affect the backend service.

## Error Handling

The API uses standard HTTP status codes:

- **200 OK**: Request successful
- **400 Bad Request**: Invalid request format
- **500 Internal Server Error**: Server-side error

## Data Models

### QueryRequest

```python
class QueryRequest(BaseModel):
    query: str = Field(..., description="The user's natural language query")
    conversation_context: Optional[ConversationContext] = None
```

### ConversationContext

```python
class ConversationContext(BaseModel):
    messages: List[ChatMessage] = Field(default_factory=list)
    last_query: Optional[str] = None
    last_product_criteria: Optional[ProductCriteria] = None
```

### ChatMessage

```python
class ChatMessage(BaseModel):
    id: str
    text: str
    sender: str = Field(..., description="Either 'user' or 'system'")
    timestamp: str
```

### ProductCriteria

```python
class ProductCriteria(BaseModel):
    category: Optional[str] = None
    price_range: Optional[Dict[str, float]] = None  # {"min": float, "max": float}
    features: Optional[List[str]] = None
    brand: Optional[str] = None
    marketplace: Optional[str] = None
```

### QueryResponse

```python
class QueryResponse(BaseModel):
    query: str
    products: List[Product]
    recommendations_summary: str
    error: Optional[str] = None
```

### Product

```python
class Product(BaseModel):
    title: str
    price: float
    rating: float
    features: List[str]
    pros: List[str]
    cons: List[str]
    link: str
```