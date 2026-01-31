#!/usr/bin/env python3
"""
Test Chat Terminal - Versión simplificada sin DB
Solo prueba RAG + Groq LLM
"""
import sys
import asyncio
import time
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

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

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Check required env vars
if not os.getenv('GROQ_API_KEY'):
    print(f"{Colors.FAIL}❌ Error: GROQ_API_KEY no configurada en .env{Colors.ENDC}")
    sys.exit(1)

# Import with error handling
try:
    import httpx
except ImportError as e:
    print(f"{Colors.FAIL}❌ Error importando módulos: {e}{Colors.ENDC}")
    print(f"{Colors.WARNING}💡 Instala dependencias:{Colors.ENDC}")
    print(f"   pip install httpx")
    sys.exit(1)


class SimpleChat:
    """Simple chat without database dependencies"""
    
    def __init__(self):
        self.chat_history = []
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.groq_model = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        
        self.total_tokens = 0
        self.total_time = 0
        self.message_count = 0
    
    def print_header(self):
        """Print welcome header"""
        print("\n" + "="*70)
        print(f"{Colors.HEADER}{Colors.BOLD}🤖 Bot WhatsApp - Test Chat (Groq Only){Colors.ENDC}")
        print("="*70)
        print(f"{Colors.OKCYAN}💡 Chat directo con Groq LLM (sin base de datos){Colors.ENDC}")
        print()
        print(f"{Colors.WARNING}Comandos:{Colors.ENDC}")
        print("  • /quit, /salir      - Salir")
        print("  • /clear             - Limpiar historial")
        print("  • /stats             - Ver estadísticas")
        print("="*70 + "\n")
    
    def print_stats(self):
        """Print statistics"""
        print(f"\n{Colors.OKGREEN}📊 Estadísticas:{Colors.ENDC}")
        print(f"  • Mensajes: {self.message_count}")
        print(f"  • Tokens: ~{self.total_tokens}")
        print(f"  • Tiempo: {self.total_time:.2f}s")
        if self.message_count > 0:
            print(f"  • Promedio: {self.total_time/self.message_count:.2f}s/msg")
        print()
    
    async def send_message(self, message: str):
        """Send message and get response"""
        print(f"\n{Colors.OKBLUE}👤 Tú:{Colors.ENDC} {message}")
        
        start = time.time()
        
        try:
            # Build prompt (sin RAG, solo chat directo)
            system_prompt = """Eres un asistente de soporte técnico para un ISP (proveedor de internet).

Ayudas a clientes con:
- Problemas de conexión a internet
- Configuración de router/modem
- Planes y tarifas
- Facturación
- Instalaciones nuevas
- Soporte técnico general

Sé conciso, profesional y amable. Responde en español."""
            
            messages = [{"role": "system", "content": system_prompt}]
            
            if self.chat_history:
                messages.extend(self.chat_history[-4:])
            
            messages.append({"role": "user", "content": message})
            
            # Call Groq
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.groq_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.groq_model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 512
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    print(f"\n{Colors.FAIL}❌ Error Groq: {response.status_code}{Colors.ENDC}")
                    print(f"   {response.text}")
                    return
                
                data = response.json()
                answer = data["choices"][0]["message"]["content"]
            
            elapsed = time.time() - start
            
            # Update stats
            self.message_count += 1
            self.total_time += elapsed
            estimated_tokens = (len(message) + len(answer)) // 4
            self.total_tokens += estimated_tokens
            
            # Update history
            self.chat_history.append({"role": "user", "content": message})
            self.chat_history.append({"role": "assistant", "content": answer})
            
            if len(self.chat_history) > 10:
                self.chat_history = self.chat_history[-10:]
            
            # Print response
            print(f"\n{Colors.OKGREEN}🤖 Bot:{Colors.ENDC} {answer}")
            print(f"\n{Colors.WARNING}⏱️  {elapsed:.2f}s | ~{estimated_tokens} tokens{Colors.ENDC}")
            
        except Exception as e:
            print(f"\n{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
    
    
    async def run(self):
        """Run chat"""
        self.print_header()
        
        print(f"{Colors.OKGREEN}✅ Conectado a Groq: {self.groq_model}{Colors.ENDC}\n")
        
        while True:
            try:
                user_input = input(f"{Colors.BOLD}> {Colors.ENDC}").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['/quit', '/salir']:
                    print(f"\n{Colors.OKCYAN}👋 ¡Hasta luego!{Colors.ENDC}")
                    self.print_stats()
                    break
                
                elif user_input.lower() == '/clear':
                    self.chat_history = []
                    print(f"\n{Colors.OKGREEN}✅ Historial limpiado{Colors.ENDC}\n")
                    continue
                
                elif user_input.lower() == '/stats':
                    self.print_stats()
                    continue
                
                await self.send_message(user_input)
                
            except KeyboardInterrupt:
                print(f"\n\n{Colors.OKCYAN}👋 Interrumpido{Colors.ENDC}")
                self.print_stats()
                break
            except EOFError:
                break


async def main():
    chat = SimpleChat()
    await chat.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Adiós!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
