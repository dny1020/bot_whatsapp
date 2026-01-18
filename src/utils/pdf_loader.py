"""
PDF and document loader for knowledge base
Extracts text from PDFs and adds to RAG system
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
from datetime import datetime

try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

from .logger import get_logger

logger = get_logger(__name__)


class DocumentLoader:
    """Load documents into knowledge base"""
    
    def __init__(self):
        self.supported_formats = [".pdf", ".txt", ".md"]
        if not PDF_SUPPORT:
            logger.warning("pypdf2_not_installed", 
                         message="Install PyPDF2 for PDF support: pip install PyPDF2")
    
    def load_pdf(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """Extract text from PDF and create knowledge entries"""
        if not PDF_SUPPORT:
            raise ImportError("PyPDF2 not installed. Run: pip install PyPDF2")
        
        entries = []
        
        try:
            with open(pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract text from each page
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text().strip()
                    
                    if text:
                        # Split into chunks (for better retrieval)
                        chunks = self._chunk_text(text, max_length=500)
                        
                        for chunk_idx, chunk in enumerate(chunks, 1):
                            entry_id = hashlib.md5(
                                f"{pdf_path.name}_page{page_num}_chunk{chunk_idx}".encode()
                            ).hexdigest()[:12]
                            
                            entries.append({
                                "id": entry_id,
                                "type": "document",
                                "content": chunk,
                                "metadata": {
                                    "source": str(pdf_path.name),
                                    "page": page_num,
                                    "chunk": chunk_idx,
                                    "format": "pdf",
                                    "loaded_at": datetime.utcnow().isoformat()
                                }
                            })
                
                logger.info("pdf_loaded", 
                          file=pdf_path.name, 
                          pages=len(pdf_reader.pages),
                          entries=len(entries))
        
        except Exception as e:
            logger.error("pdf_load_error", file=str(pdf_path), error=str(e))
            raise
        
        return entries
    
    def load_text_file(self, txt_path: Path) -> List[Dict[str, Any]]:
        """Load plain text or markdown file"""
        entries = []
        
        try:
            with open(txt_path, "r", encoding="utf-8") as file:
                text = file.read().strip()
            
            # Split into chunks
            chunks = self._chunk_text(text, max_length=500)
            
            for chunk_idx, chunk in enumerate(chunks, 1):
                entry_id = hashlib.md5(
                    f"{txt_path.name}_chunk{chunk_idx}".encode()
                ).hexdigest()[:12]
                
                entries.append({
                    "id": entry_id,
                    "type": "document",
                    "content": chunk,
                    "metadata": {
                        "source": str(txt_path.name),
                        "chunk": chunk_idx,
                        "format": txt_path.suffix[1:],
                        "loaded_at": datetime.utcnow().isoformat()
                    }
                })
            
            logger.info("text_file_loaded", 
                      file=txt_path.name,
                      entries=len(entries))
        
        except Exception as e:
            logger.error("text_load_error", file=str(txt_path), error=str(e))
            raise
        
        return entries
    
    def load_directory(self, dir_path: Path) -> List[Dict[str, Any]]:
        """Load all supported documents from directory"""
        all_entries = []
        
        for file_path in dir_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in self.supported_formats:
                try:
                    if file_path.suffix == ".pdf":
                        entries = self.load_pdf(file_path)
                    else:
                        entries = self.load_text_file(file_path)
                    
                    all_entries.extend(entries)
                
                except Exception as e:
                    logger.error("file_load_failed", file=str(file_path), error=str(e))
                    continue
        
        logger.info("directory_loaded", 
                   path=str(dir_path),
                   total_entries=len(all_entries))
        
        return all_entries
    
    def _chunk_text(self, text: str, max_length: int = 500) -> List[str]:
        """Split text into chunks for better retrieval"""
        # Simple sentence-based chunking
        sentences = text.replace('\n', ' ').split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Add period back if it was removed
            if not sentence.endswith('.'):
                sentence += '.'
            
            # If adding this sentence exceeds max_length, start new chunk
            if len(current_chunk) + len(sentence) > max_length and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks


# Global instance
document_loader = DocumentLoader()
