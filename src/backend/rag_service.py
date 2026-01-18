"""
RAG (Retrieval-Augmented Generation) Service
Vector database for knowledge retrieval
"""
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
import hashlib
from datetime import datetime
from ..utils.config import settings, business_config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class RAGService:
    """Service for retrieval-augmented generation"""
    
    def __init__(self):
        self.knowledge_base = self._load_knowledge_base()
        self.embeddings_enabled = self._check_embeddings_support()
        
        logger.info("rag_service_initialized", 
                   kb_entries=len(self.knowledge_base),
                   embeddings=self.embeddings_enabled)
    
    def _check_embeddings_support(self) -> bool:
        """Check if embeddings are available"""
        # Can integrate with sentence-transformers, OpenAI embeddings, etc.
        return bool(settings.openai_api_key or settings.use_local_embeddings)
    
    def _load_knowledge_base(self) -> List[Dict[str, Any]]:
        """Load knowledge base from configuration and files"""
        kb = []
        
        # Add business information
        business = business_config.get("business", {})
        kb.append({
            "id": "business_info",
            "type": "business",
            "content": f"Información del negocio: {business.get('name')}. {business.get('description')}. "
                      f"Teléfono: {business.get('phone')}. Email: {business.get('email')}.",
            "metadata": business
        })
        
        # Add menu items
        menu = business_config.get("menu", {})
        for category in menu.get("categories", []):
            for item in category.get("items", []):
                kb.append({
                    "id": f"product_{item.get('id')}",
                    "type": "product",
                    "content": f"{item.get('name')}: {item.get('description')}. "
                              f"Precio: ${item.get('price')}. Categoría: {category.get('name')}.",
                    "metadata": item
                })
        
        # Add delivery zones
        delivery = business_config.get("delivery", {})
        for zone in delivery.get("zones", []):
            kb.append({
                "id": f"zone_{zone.get('name')}",
                "type": "delivery_zone",
                "content": f"Zona de entrega: {zone.get('name')}. "
                          f"Radio: {zone.get('radius_km')}km. "
                          f"Costo: ${zone.get('delivery_fee')}. "
                          f"Tiempo estimado: {zone.get('estimated_time_minutes')} minutos.",
                "metadata": zone
            })
        
        # Add working hours
        hours = delivery.get("working_hours", {})
        if hours:
            hours_text = "Horarios de atención: "
            for day, schedule in hours.items():
                hours_text += f"{day}: {schedule.get('open')} - {schedule.get('close')}. "
            
            kb.append({
                "id": "working_hours",
                "type": "hours",
                "content": hours_text,
                "metadata": hours
            })
        
        # Add payment methods
        payment_methods = business_config.get("payment_methods", [])
        if payment_methods:
            payment_text = "Métodos de pago disponibles: "
            payment_text += ", ".join([m.get("name") for m in payment_methods if m.get("enabled")])
            
            kb.append({
                "id": "payment_methods",
                "type": "payment",
                "content": payment_text,
                "metadata": payment_methods
            })
        
        # Load custom knowledge base files if they exist
        kb_path = Path(__file__).parent.parent.parent / "config" / "knowledge_base.json"
        if kb_path.exists():
            try:
                with open(kb_path, "r", encoding="utf-8") as f:
                    custom_kb = json.load(f)
                    kb.extend(custom_kb)
                    logger.info("custom_knowledge_loaded", entries=len(custom_kb))
            except Exception as e:
                logger.error("knowledge_load_error", error=str(e))
        
        return kb
    
    def search(
        self,
        query: str,
        top_k: int = 3,
        filter_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search knowledge base (simple keyword matching)"""
        query_lower = query.lower()
        results = []
        
        for entry in self.knowledge_base:
            # Filter by type if specified
            if filter_type and entry.get("type") != filter_type:
                continue
            
            # Simple keyword matching (can be replaced with embeddings)
            content_lower = entry.get("content", "").lower()
            
            # Calculate relevance score
            score = 0
            query_words = query_lower.split()
            for word in query_words:
                if len(word) > 2:  # Skip very short words
                    if word in content_lower:
                        score += 1
            
            if score > 0:
                results.append({
                    **entry,
                    "relevance_score": score
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        logger.info("rag_search", query=query, results_count=len(results[:top_k]))
        return results[:top_k]
    
    def get_context_for_llm(
        self,
        query: str,
        max_entries: int = 3
    ) -> str:
        """Get relevant context for LLM prompt"""
        results = self.search(query, top_k=max_entries)
        
        if not results:
            return "No se encontró información relevante en la base de conocimiento."
        
        context = "Información relevante:\n\n"
        for idx, result in enumerate(results, 1):
            context += f"{idx}. {result.get('content')}\n"
        
        return context
    
    def find_product_by_name(self, product_name: str) -> Optional[Dict[str, Any]]:
        """Find product by name using fuzzy matching"""
        results = self.search(product_name, top_k=5, filter_type="product")
        
        if not results:
            return None
        
        # Return best match
        best_match = results[0]
        return best_match.get("metadata")
    
    def get_delivery_info(self, address: str = None) -> Dict[str, Any]:
        """Get delivery information"""
        results = self.search("delivery zone", filter_type="delivery_zone")
        
        zones = [r.get("metadata") for r in results]
        
        # If address provided, try to determine zone (simplified)
        selected_zone = zones[0] if zones else None
        
        return {
            "zones": zones,
            "selected_zone": selected_zone,
            "available": len(zones) > 0
        }
    
    def get_business_hours(self) -> Optional[Dict[str, Any]]:
        """Get business hours"""
        results = self.search("horarios", filter_type="hours")
        
        if results:
            return results[0].get("metadata")
        
        return None
    
    def add_to_knowledge_base(
        self,
        content: str,
        entry_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add new entry to knowledge base"""
        entry_id = hashlib.md5(
            f"{entry_type}_{content}_{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:12]
        
        entry = {
            "id": entry_id,
            "type": entry_type,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.knowledge_base.append(entry)
        
        logger.info("knowledge_entry_added", entry_id=entry_id, type=entry_type)
        return entry_id
    
    def save_knowledge_base(self):
        """Save custom knowledge base to file"""
        kb_path = Path(__file__).parent.parent.parent / "config" / "knowledge_base.json"
        
        # Save only custom entries (not auto-generated ones)
        custom_entries = [
            e for e in self.knowledge_base 
            if e.get("created_at") and not e.get("id").startswith(("business_", "product_", "zone_"))
        ]
        
        try:
            with open(kb_path, "w", encoding="utf-8") as f:
                json.dump(custom_entries, f, indent=2, ensure_ascii=False)
            
            logger.info("knowledge_base_saved", entries=len(custom_entries))
        except Exception as e:
            logger.error("knowledge_save_error", error=str(e))


# Global RAG service instance
rag_service = RAGService()
