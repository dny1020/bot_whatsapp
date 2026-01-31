#!/usr/bin/env python3
"""
Test Chat Terminal - Prueba el bot directamente desde la terminal
Permite chatear y ver cómo consume Groq + RAG
"""
import sys
import asyncio
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backend.support_service import support_service
from src.backend.rag_service_v2 import rag_service
from src.utils.logger import setup_logging, get_logger

# Colors for terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

setup_logging()
logger = get_logger(__name__)


class TerminalChat:
    """Interactive chat in terminal"""
    
    def __init__(self):
        self.chat_history = []
        self.total_tokens = 0
        self.total_time = 0
        self.message_count = 0
    
    def print_header(self):
        """Print welcome header"""
        print("\n" + "="*70)
        print(f"{Colors.HEADER}{Colors.BOLD}🤖 Bot WhatsApp - Terminal Chat Test{Colors.ENDC}")
        print("="*70)
        print(f"{Colors.OKCYAN}💡 Prueba el bot con RAG vectorial y Groq LLM{Colors.ENDC}")
        print()
        print(f"{Colors.WARNING}Comandos especiales:{Colors.ENDC}")
        print("  • /quit, /exit, /salir  - Salir del chat")
        print("  • /clear, /limpiar      - Limpiar historial")
        print("  • /stats                - Ver estadísticas")
        print("  • /rag <query>          - Probar solo RAG (sin LLM)")
        print("="*70 + "\n")
    
    def print_stats(self):
        """Print chat statistics"""
        print(f"\n{Colors.OKGREEN}📊 Estadísticas:{Colors.ENDC}")
        print(f"  • Mensajes enviados: {self.message_count}")
        print(f"  • Tokens estimados: {self.total_tokens}")
        print(f"  • Tiempo total: {self.total_time:.2f}s")
        if self.message_count > 0:
            print(f"  • Tiempo promedio: {self.total_time/self.message_count:.2f}s/mensaje")
        print()
    
    async def test_rag_only(self, query: str):
        """Test RAG retrieval without LLM"""
        print(f"\n{Colors.OKCYAN}🔍 Búsqueda RAG:{Colors.ENDC} {query}\n")
        
        start = time.time()
        results = rag_service.retrieve(query, k=3)
        elapsed = time.time() - start
        
        if not results:
            print(f"{Colors.WARNING}⚠️  No se encontraron documentos relevantes{Colors.ENDC}\n")
            return
        
        print(f"{Colors.OKGREEN}✅ Encontrados {len(results)} documentos en {elapsed:.2f}s:{Colors.ENDC}\n")
        
        for i, doc in enumerate(results, 1):
            print(f"{Colors.BOLD}[{i}] {doc['source']}{Colors.ENDC} ({doc['type']})")
            print(f"    {doc['content'][:200]}...")
            print()
    
    async def send_message(self, message: str):
        """Send message and get response"""
        print(f"\n{Colors.OKBLUE}👤 Tú:{Colors.ENDC} {message}")
        
        # Start timer
        start = time.time()
        
        # Get AI response
        try:
            response = await support_service.get_ai_response(message, self.chat_history)
            elapsed = time.time() - start
            
            # Update stats
            self.message_count += 1
            self.total_time += elapsed
            # Estimate tokens (rough: ~4 chars per token)
            estimated_tokens = (len(message) + len(response)) // 4
            self.total_tokens += estimated_tokens
            
            # Update history
            self.chat_history.append({"role": "user", "content": message})
            self.chat_history.append({"role": "assistant", "content": response})
            
            # Keep history manageable (last 10 messages = 5 exchanges)
            if len(self.chat_history) > 10:
                self.chat_history = self.chat_history[-10:]
            
            # Print response
            print(f"\n{Colors.OKGREEN}🤖 Bot:{Colors.ENDC} {response}")
            print(f"\n{Colors.WARNING}⏱️  Tiempo: {elapsed:.2f}s | Tokens: ~{estimated_tokens}{Colors.ENDC}")
            
        except Exception as e:
            print(f"\n{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
            logger.error("terminal_chat_error", error=str(e))
    
    async def run(self):
        """Run interactive chat"""
        self.print_header()
        
        # Check RAG service
        docs_count = rag_service._count_documents()
        if docs_count == 0:
            print(f"{Colors.WARNING}⚠️  Advertencia: No hay documentos en docs/{Colors.ENDC}")
            print(f"{Colors.WARNING}   El bot responderá sin contexto RAG{Colors.ENDC}\n")
        else:
            print(f"{Colors.OKGREEN}✅ RAG activo con {docs_count} documentos{Colors.ENDC}\n")
        
        # Interactive loop
        while True:
            try:
                # Get user input
                user_input = input(f"{Colors.BOLD}> {Colors.ENDC}").strip()
                
                if not user_input:
                    continue
                
                # Check commands
                if user_input.lower() in ['/quit', '/exit', '/salir']:
                    print(f"\n{Colors.OKCYAN}👋 ¡Hasta luego!{Colors.ENDC}")
                    self.print_stats()
                    break
                
                elif user_input.lower() in ['/clear', '/limpiar']:
                    self.chat_history = []
                    print(f"\n{Colors.OKGREEN}✅ Historial limpiado{Colors.ENDC}\n")
                    continue
                
                elif user_input.lower() == '/stats':
                    self.print_stats()
                    continue
                
                elif user_input.lower().startswith('/rag '):
                    query = user_input[5:].strip()
                    if query:
                        await self.test_rag_only(query)
                    continue
                
                # Send message
                await self.send_message(user_input)
                
            except KeyboardInterrupt:
                print(f"\n\n{Colors.OKCYAN}👋 Interrumpido por usuario{Colors.ENDC}")
                self.print_stats()
                break
            
            except EOFError:
                break


async def main():
    """Main function"""
    chat = TerminalChat()
    await chat.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Adiós!")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        sys.exit(1)
