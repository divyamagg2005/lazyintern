import httpx
from core.config import settings

print("Testing Groq API directly...")
print(f"Using key: {settings.groq_api_key[:10]}...")
print(f"Model: {settings.groq_model}")

try:
    response = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": settings.groq_model,
            "messages": [
                {"role": "user", "content": "Say hello in 5 words"}
            ],
            "temperature": 0.7,
            "max_tokens": 50
        },
        timeout=30.0
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    
    if response.status_code == 200:
        print("\n✓ SUCCESS! Groq API is working!")
    else:
        print(f"\n✗ FAILED with status {response.status_code}")
        
except Exception as e:
    print(f"\n✗ Error: {e}")
