"""
Test RAG Service
"""
import pytest
from src.backend.rag_service import RAGService


class TestRAGService:
    """Test RAG service"""
    
    def setup_method(self):
        self.rag = RAGService()
    
    def test_knowledge_base_loaded(self):
        """Test that knowledge base is loaded"""
        assert len(self.rag.knowledge_base) > 0
    
    def test_search_products(self):
        """Test searching for products"""
        results = self.rag.search("hamburguesa", top_k=3)
        
        # Should find results if hamburguesa is in menu
        assert isinstance(results, list)
    
    def test_search_with_type_filter(self):
        """Test filtered search"""
        results = self.rag.search("delivery", filter_type="delivery_zone")
        
        for result in results:
            assert result["type"] == "delivery_zone"
    
    def test_find_product_by_name(self):
        """Test finding specific product"""
        # This will work if product exists in config
        product = self.rag.find_product_by_name("pizza")
        
        if product:
            assert "name" in product or "id" in product
    
    def test_get_delivery_info(self):
        """Test getting delivery information"""
        info = self.rag.get_delivery_info()
        
        assert "zones" in info
        assert "available" in info
    
    def test_get_context_for_llm(self):
        """Test generating context for LLM"""
        context = self.rag.get_context_for_llm("horarios de atención")
        
        assert isinstance(context, str)
        assert len(context) > 0
    
    def test_add_to_knowledge_base(self):
        """Test adding new entry"""
        initial_count = len(self.rag.knowledge_base)
        
        entry_id = self.rag.add_to_knowledge_base(
            content="Nueva información de prueba",
            entry_type="test",
            metadata={"source": "test"}
        )
        
        assert entry_id is not None
        assert len(self.rag.knowledge_base) == initial_count + 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
