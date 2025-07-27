from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.query import QueryRequest, QueryResponse
from app.services import GeminiService, ProductParserService, ContextManagerService
from app.middleware.auth import get_optional_user
from app.services.credit_service import credit_service
from app.services.query_cache_service import query_cache_service
from app.middleware.credit_middleware import validate_credits, deduct_credit, get_credit_status, CreditExhaustedException
from app.database.manager import get_db_session
from app.middleware.database_error_handlers import handle_database_errors
from typing import Dict, Any, Optional
import json

router = APIRouter()

# Create singleton instances of services
gemini_service = GeminiService()
product_parser_service = ProductParserService()
context_manager_service = ContextManagerService()


@router.post("/query", response_model=QueryResponse)
@handle_database_errors
async def process_query(
    request: QueryRequest,
    req: Request,
    user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Process a natural language query and return product recommendations.
    
    This endpoint accepts a user query and optional conversation context,
    processes it using the Gemini API, and returns structured product recommendations.
    The response is validated and processed by the ProductParserService.
    
    Features:
    - Server-side caching to avoid duplicate processing
    - Credit-based usage tracking for guests and registered users
    - Cache hit/miss tracking and statistics
    """
    try:
        # Generate cache key for the query
        conversation_context_str = None
        if request.conversation_context:
            # Convert conversation context to string for caching
            conversation_context_str = json.dumps(request.conversation_context.model_dump(), sort_keys=True)
        
        query_hash = query_cache_service.generate_query_hash(
            query=request.query,
            conversation_context=conversation_context_str
        )
        
        # Check cache first
        cached_result = query_cache_service.get_cached_result(query_hash)
        if cached_result:
            # Return cached result without deducting credits
            response = QueryResponse(**cached_result)
            
            # Add cache indicator and credit info to metadata
            response.metadata = response.metadata or {}
            response.metadata["cached"] = True
            response.metadata["cache_hit"] = True
            
            # Add credit information
            credits_info = await get_credit_status(req, user, session)
            response.metadata.update(credits_info)
            
            return response
        
        # Not in cache, validate and deduct credits before processing
        await validate_credits(req, user, session)
        await deduct_credit(req, user, session)
        
        # Process the query using the GeminiService
        response = await gemini_service.process_query(
            query=request.query,
            conversation_context=request.conversation_context
        )
        
        # Cache the result for future use
        query_cache_service.cache_result(query_hash, response.model_dump())
        
        # Add cache and credit metadata
        response.metadata = response.metadata or {}
        response.metadata["cached"] = False
        response.metadata["cache_hit"] = False
        
        # Add credit information after deduction
        credits_info = await get_credit_status(req, user, session)
        response.metadata.update(credits_info)
        
        return response
        
    except CreditExhaustedException:
        # Re-raise credit exhaustion exceptions (handled by middleware)
        raise
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )