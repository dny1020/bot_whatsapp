import asyncio
import sys
import os
import httpx
import uuid

# Configuration
WEBHOOK_URL = "http://localhost:8001/webhook"  # Adjust if webhook is on different port
TEST_PHONE = "123456789"

async def send_mock_message(text: str):
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "mock_account_id",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"display_phone_number": "123456", "phone_number_id": "123456"},
                            "contacts": [{"profile": {"name": "Demo User"}, "wa_id": TEST_PHONE}],
                            "messages": [
                                {
                                    "from": TEST_PHONE,
                                    "id": str(uuid.uuid4()),
                                    "timestamp": "1671234567",
                                    "text": {"body": text},
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(WEBHOOK_URL, json=payload)
            if response.status_code != 200:
                print(f"Error: Webhook returned {response.status_code}")
    except Exception as e:
        print(f"Error connecting to webhook: {e}")

async def main():
    print("=== WhatsApp Bot Terminal Demo ===")
    print(f"Target Webhook: {WEBHOOK_URL}")
    print("Type your message below (type 'exit' to quit)")
    print("-" * 34)
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['exit', 'quit']:
                break
            
            await send_mock_message(user_input)
            # Small delay to let the bot process and print (since it's mock mode)
            await asyncio.sleep(1)
            
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    if len(sys.argv) > 1:
        WEBHOOK_URL = sys.argv[1]
    asyncio.run(main())
