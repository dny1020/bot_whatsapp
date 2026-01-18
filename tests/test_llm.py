"""
Test LLM Service
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.backend.llm_service import LLMService, LLMProvider


class TestLLMService:
    """Test LLM service"""
    
    def setup_method(self):
        self.llm = LLMService()
    
    def test_provider_determination(self):
        """Test provider is determined correctly"""
        assert self.llm.provider in [
            LLMProvider.OPENAI,
            LLMProvider.ANTHROPIC,
            LLMProvider.GROQ,
            LLMProvider.LOCAL
        ]
    
    def test_model_name_set(self):
        """Test model name is set"""
        assert self.llm.model_name is not None
        assert len(self.llm.model_name) > 0
    
    @pytest.mark.asyncio
    async def test_generate_response_fallback(self):
        """Test generate response with local fallback"""
        # Force local provider
        original_provider = self.llm.provider
        self.llm.provider = LLMProvider.LOCAL
        
        response = await self.llm.generate_response("Test prompt")
        
        assert isinstance(response, str)
        assert len(response) > 0
        
        # Restore
        self.llm.provider = original_provider
    
    @pytest.mark.asyncio
    async def test_extract_intent(self):
        """Test intent extraction"""
        # This will use fallback if no API key configured
        intent = await self.llm.extract_intent("Hola, quiero ver el menú")
        
        assert isinstance(intent, str)
    
    @pytest.mark.asyncio
    async def test_extract_entities(self):
        """Test entity extraction"""
        entities = await self.llm.extract_entities("Mi dirección es Calle 123")
        
        assert isinstance(entities, dict)
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_openai_call(self, mock_post):
        """Test OpenAI API call with mock"""
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": "Test response"}
            }],
            "usage": {"total_tokens": 10}
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Force OpenAI provider
        original_provider = self.llm.provider
        original_key = self.llm.model_name
        
        self.llm.provider = LLMProvider.OPENAI
        
        # Mock settings
        with patch('src.backend.llm_service.settings') as mock_settings:
            mock_settings.openai_api_key = "test_key"
            
            response = await self.llm._generate_openai(
                "Test prompt",
                "System prompt",
                0.7,
                100
            )
            
            assert response == "Test response"
        
        # Restore
        self.llm.provider = original_provider


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
