from fastapi import APIRouter, HTTPException, Depends, Request
from app.models.query import QueryRequest, QueryResponse
from app.services import GeminiService, ProductParserService, ContextManagerService
from app.middleware.auth import get_optional_user
from app.services.guest_action_service import guest_action_service
from typing import Dict, Any, Optional

router = APIRouter()

# Create singleton instances of services
gemini_service = GeminiService()
product_parser_service = ProductParserService()
context_manager_service = ContextManagerService()


@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    req: Request,
    user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Process a natural language query and return product recommendations.
    
    This endpoint accepts a user query and optional conversation context,
    processes it using the Gemini API, and returns structured product recommendations.
    The response is validated and processed by the ProductParserService.
    
    Authentication:
    - Authenticated users have unlimited access
    - Guest users are limited to a configured number of actions
    """
    try:
        # Check if user is authenticated
        if user is None:
            # This is a guest user, get a unique identifier (IP address in this case)
            guest_id = str(req.client.host)
            
            # Check if guest has reached the action limit
            if guest_action_service.is_limit_reached(guest_id):
                raise HTTPException(
                    status_code=403,
                    detail="Guest action limit reached. Please log in to continue."
                )
            
            # Track the guest action
            guest_action_service.track_action(guest_id, "chat")
        
        # Process the query using the GeminiService
        response = await gemini_service.process_query(
            query=request.query,
            conversation_context=request.conversation_context
        )
        
        # Add remaining actions count for guest users
        if user is None:
            guest_id = str(req.client.host)
            remaining_actions = guest_action_service.get_remaining_actions(guest_id)
            response.metadata = response.metadata or {}
            response.metadata["remaining_guest_actions"] = remaining_actions
        
        return response
        
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )