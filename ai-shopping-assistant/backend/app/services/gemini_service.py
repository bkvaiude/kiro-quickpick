"""
GeminiService for handling communication with the Gemini API.
"""
import time
import json
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from google.generativeai.types.generation_types import StopCandidateException
from fastapi import HTTPException

from app.config import settings
from app.models.query import ConversationContext, Product, QueryResponse
from app.services.product_parser_service import ProductParserService
from app.services.context_manager_service import ContextManagerService

# Configure the Gemini API with the API key
genai.configure(api_key=settings.gemini_api_key)

class GeminiService:
    """Service for interacting with the Gemini API."""
    
    def __init__(self):
        """Initialize the GeminiService."""
        self.system_prompt = self._create_system_prompt()
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config=GenerationConfig(
                temperature=0.2,  # Lower temperature for more deterministic responses
                top_p=0.95,
                top_k=40,
                max_output_tokens=4096,
            )
        )
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        self.product_parser = ProductParserService()
        self.context_manager = ContextManagerService()
    
    def _create_system_prompt(self) -> str:
        """
        Create the system prompt for structured JSON responses.
        
        Returns:
            str: The system prompt for the Gemini API.
        """
        return """
            You are an AI shopping assistant designed specifically for Indian users. Your role is to recommend relevant products based strictly on the user's query by fetching the latest and most accurate product data.

            **CRITICAL INSTRUCTION:**
            You must scrape and use data **exclusively from Amazon India ([https://www.amazon.in/](https://www.amazon.in/))**. Do not fetch or include data from any other e-commerce website. All product links must be validated and confirmed as live and functional before including them in the response.

            ---

            **RESPONSE FORMAT:**
            Respond **with raw JSON only** (no markdown, no explanations, no additional text). Use the following structure:

            ```json
            {
            "products": [
                {
                "title": "Product Name",
                "price": 12999,
                "rating": 4.5,
                "features": ["Feature 1", "Feature 2"],
                "pros": ["Pro 1", "Pro 2"],
                "cons": ["Con 1", "Con 2"],
                "link": "https://www.amazon.in/example-product"
                }
            ],
            "recommendationsSummary": "Summarize why these products are recommended."
            }
            ```

            ---

            **RULES TO FOLLOW:**

            1. Scrape only from **amazon.in** — absolutely no other sources.
            2. Product links must be verified as valid and accessible before adding.
            3. If the user query includes "phone", return 3 phone recommendations.
            4. If the query includes "TV", return 3 TV recommendations.
            5. For all other queries, return an empty `products` array with an explanation in `recommendationsSummary`.
            6. Use Indian market context:
            * Prices in Indian Rupees (₹)
            * Product links must be valid amazon.in URLs
            7. **Do not include any text outside the JSON.**
            8. **Do not use markdown code blocks (e.g., \`\`\`json).**
            9. **Do not add any explanations before or after the JSON.**
            10. Always respond **with raw JSON only**, fully conforming to the specified format.
        """
    
    async def process_query(self, query: str, conversation_context: Optional[ConversationContext] = None) -> QueryResponse:
        """
        Process a user query using the Gemini API.
        
        Args:
            query: The user's natural language query.
            conversation_context: Optional conversation context from previous interactions.
            
        Returns:
            QueryResponse: The structured response with product recommendations.
            
        Raises:
            HTTPException: If there's an error processing the query.
        """
        try:
            # Update conversation context with the new user query
            conversation_context = self.context_manager.add_message(
                conversation_context, query, "user"
            )
            
            # Enhance the query with context from previous interactions
            enhanced_query = self.context_manager.merge_context_with_query(
                query, conversation_context
            )
            
            # Add a reminder to return JSON format
            enhanced_query = f"{enhanced_query}\n\nRemember to respond with VALID JSON ONLY, no markdown or explanatory text."
            
            # Prepare the conversation history if available
            history = []
            
            # Always add system prompt as the first message
            history.append({"role": "user", "parts": [self.system_prompt]})
            history.append({"role": "model", "parts": ["I'll respond with valid JSON only."]})
            
            if conversation_context and conversation_context.messages:
                for msg in conversation_context.messages[-5:]:  # Use last 5 messages for context
                    role = "user" if msg.sender == "user" else "model"
                    history.append({"role": role, "parts": [msg.text]})
            
            # Create the chat session with history including system prompt
            chat = self.model.start_chat(history=history)
            
            # Send the enhanced user query with JSON reminder
            enhanced_query = f"{enhanced_query}\n\nIMPORTANT: Respond with VALID JSON ONLY. No markdown, no code blocks, no explanations."
            response = await self._send_message_with_retry(chat, enhanced_query)
            
            # Parse the response
            result = self._parse_response(query, response.text)
            
            # Update conversation context with the system response
            self.context_manager.add_message(
                conversation_context, 
                f"Recommendations for: {query}\n{result.recommendations_summary}", 
                "system"
            )
            
            return result
            
        except Exception as e:
            # Log the error for debugging
            print(f"Error processing query: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing query with Gemini API: {str(e)}"
            )
    
    async def _send_message_with_retry(self, chat, message: str, attempt: int = 1):
        """
        Send a message to the Gemini API with retry logic.
        
        Args:
            chat: The chat session.
            message: The message to send.
            attempt: The current attempt number.
            
        Returns:
            The response from the Gemini API.
            
        Raises:
            HTTPException: If all retry attempts fail.
        """
        try:
            return await chat.send_message_async(message)
        except StopCandidateException as e:
            # Handle content filtering issues
            raise HTTPException(
                status_code=400,
                detail="The query contains content that cannot be processed. Please rephrase your query."
            )
        except Exception as e:
            if attempt <= self.max_retries:
                # Exponential backoff
                wait_time = self.retry_delay * (2 ** (attempt - 1))
                time.sleep(wait_time)
                return await self._send_message_with_retry(chat, message, attempt + 1)
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to get response from Gemini API after {self.max_retries} attempts: {str(e)}"
                )
    
    def _parse_response(self, query: str, response_text: str) -> QueryResponse:
        """
        Parse the JSON response from Gemini API using the ProductParserService.
        
        Args:
            query: The original user query.
            response_text: The text response from the Gemini API.
            
        Returns:
            QueryResponse: The structured response with product recommendations.
            
        Raises:
            HTTPException: If the response cannot be parsed as valid JSON.
        """
        # Delegate parsing and validation to the ProductParserService
        return self.product_parser.parse_response(query, response_text)