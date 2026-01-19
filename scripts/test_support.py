import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

# Mock the relative imports or ensure the structure is handled
# For testing purposes, we can simulate the environment
# Instead of direct import which fails due to .. naming in src/backend/support_service.py

async def test_kb_search():
    print("--- Testing KB Search ---")
    kb_path = os.path.join(os.getcwd(), 'config', 'knowledge_base.json')
    import json
    with open(kb_path, 'r', encoding='utf-8') as f:
        kb_data = json.load(f)
    
    def search_kb(query):
        query_lower = query.lower()
        relevant = []
        for item in kb_data:
            content = item.get("content", "").lower()
            keywords = item.get("metadata", {}).get("keywords", [])
            if any(kw.lower() in query_lower for kw in keywords) or query_lower in content:
                relevant.append(item.get("content"))
        return "\n\n".join(relevant) if relevant else "No found"

    queries = ["no tengo internet", "cambiar contraseña wifi", "pagar factura", "planes"]
    for q in queries:
        result = search_kb(q)
        print(f"Query: {q}")
        print(f"Result: {result[:100]}...")
        print("-" * 20)

async def main():
    await test_kb_search()

if __name__ == "__main__":
    asyncio.run(main())
