"""
Tests for the GeminiService.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException

from app.services.gemini_service import GeminiService
from app.models.query import ConversationContext, ChatMessage, QueryResponse

class TestGeminiService:
    """Test cases for the GeminiService."""
    
    def setup_method(self):
        """Set up the test environment."""
        self.service = GeminiService()
    
    @pytest.mark.asyncio
    @patch('app.services.gemini_service.genai')
    @patch('app.services.gemini_service.ProductParserService')
    @patch('app.services.gemini_service.ContextManagerService')
    async def test_process_query_success(self, mock_context_manager, mock_product_parser, mock_genai):
        """Test successful query processing."""
        # Mock the GenerativeModel
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Mock the chat session
        mock_chat = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        
        # Mock the chat response
        mock_response = MagicMock()
        mock_response.text = '{"products": [], "recommendationsSummary": "Test summary"}'
        mock_chat.send_message_async = AsyncMock(return_value=mock_response)
        
        # Mock the product parser
        mock_parser_instance = mock_product_parser.return_value
        mock_parser_instance.parse_response.return_value = QueryResponse(
            query="test query",
            products=[],
            recommendations_summary="Test summary"
        )
        
        # Mock the context manager
        mock_context_manager_instance = mock_context_manager.return_value
        mock_context_manager_instance.add_message.return_value = ConversationContext(
            messages=[
                ChatMessage(id="1", text="test query", sender="user", timestamp="2023-07-19T10:00:00Z")
            ]
        )
        mock_context_manager_instance.merge_context_with_query.return_value = "Enhanced test query"
        
        # Call the method
        result = await self.service.process_query("test query")
        
        # Verify the result
        assert isinstance(result, QueryResponse)
        assert result.query == "test query"
        assert result.recommendations_summary == "Test summary"
        
        # Verify the mocks were called correctly
        mock_context_manager_instance.add_message.assert_called()
        mock_context_manager_instance.merge_context_with_query.assert_called()
        mock_chat.send_message_async.assert_called()
        mock_parser_instance.parse_response.assert_called_with("test query", mock_response.text)
    
    @pytest.mark.asyncio
    @patch('app.services.gemini_service.genai')
    @patch('app.services.gemini_service.ProductParserService')
    @patch('app.services.gemini_service.ContextManagerService')
    async def test_process_query_with_context(self, mock_context_manager, mock_product_parser, mock_genai):
        """Test query processing with conversation context."""
        # Mock the GenerativeModel
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Mock the chat session
        mock_chat = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        
        # Mock the chat response
        mock_response = MagicMock()
        mock_response.text = '{"products": [], "recommendationsSummary": "Test summary"}'
        mock_chat.send_message_async = AsyncMock(return_value=mock_response)
        
        # Mock the product parser
        mock_parser_instance = mock_product_parser.return_value
        mock_parser_instance.parse_response.return_value = QueryResponse(
            query="follow-up query",
            products=[],
            recommendations_summary="Test summary"
        )
        
        # Create a conversation context
        context = ConversationContext(
            messages=[
                ChatMessage(id="1", text="initial query", sender="user", timestamp="2023-07-19T10:00:00Z"),
                ChatMessage(id="2", text="initial response", sender="system", timestamp="2023-07-19T10:00:05Z")
            ]
        )
        
        # Mock the context manager
        mock_context_manager_instance = mock_context_manager.return_value
        mock_context_manager_instance.add_message.return_value = context
        mock_context_manager_instance.merge_context_with_query.return_value = "Enhanced follow-up query"
        
        # Call the method
        result = await self.service.process_query("follow-up query", context)
        
        # Verify the result
        assert isinstance(result, QueryResponse)
        assert result.query == "follow-up query"
        
        # Verify the mocks were called correctly
        mock_context_manager_instance.add_message.assert_called()
        mock_context_manager_instance.merge_context_with_query.assert_called()
        mock_model.start_chat.assert_called_with(history=[
            {"role": "user", "parts": ["initial query"]},
            {"role": "model", "parts": ["initial response"]}
        ])
        mock_chat.send_message_async.assert_called_with("Enhanced follow-up query")
    
    @pytest.mark.asyncio
    @patch('app.services.gemini_service.genai')
    async def test_send_message_with_retry_success(self, mock_genai):
        """Test successful message sending with retry logic."""
        # Mock the chat
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_chat.send_message_async = AsyncMock(return_value=mock_response)
        
        # Call the method
        result = await self.service._send_message_with_retry(mock_chat, "test message")
        
        # Verify the result
        assert result == mock_response
        
        # Verify the mock was called correctly
        mock_chat.send_message_async.assert_called_once_with("test message")
    
    @pytest.mark.asyncio
    @patch('app.services.gemini_service.genai')
    @patch('app.services.gemini_service.time')
    async def test_send_message_with_retry_failure(self, mock_time, mock_genai):
        """Test message sending with retry logic when all attempts fail."""
        # Mock the chat
        mock_chat = MagicMock()
        mock_chat.send_message_async = AsyncMock(side_effect=Exception("Test error"))
        
        # Call the method and expect an exception
        with pytest.raises(HTTPException) as excinfo:
            await self.service._send_message_with_retry(mock_chat, "test message")
        
        # Verify the exception
        assert excinfo.value.status_code == 500
        assert "Failed to get response from Gemini API" in excinfo.value.detail
        
        # Verify the mock was called correctly
        assert mock_chat.send_message_async.call_count == self.service.max_retries + 1
        assert mock_time.sleep.call_count == self.service.max_retries