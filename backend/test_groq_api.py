"""Test Groq API to diagnose 400 errors."""

import httpx
import json
from core.config import settings

def test_groq_api():
    """Test Groq API with a simple request."""
    
    print(f"Testing Groq API...")
    print(f"Model: {settings.groq_model}")
    print(f"API Key: {settings.groq_api_key[:20]}..." if settings.groq_api_key else "NOT SET")
    
    if not settings.groq_api_key:
        print("ERROR: GROQ_API_KEY not set")
        return
    
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
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say hello in JSON format with a 'message' field."}
                ],
                "temperature": 0.7,
                "max_tokens": 100,
                "response_format": {"type": "json_object"}
            },
            timeout=30.0
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            print(f"\nSuccess! Content: {content}")
        else:
            print(f"\nError: {response.status_code}")
            print(f"Details: {response.text}")
            
    except Exception as e:
        print(f"\nException: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_groq_api()
