"""List available Groq models."""

import httpx
from core.config import settings

def list_groq_models():
    """List available Groq models."""
    
    if not settings.groq_api_key:
        print("ERROR: GROQ_API_KEY not set")
        return
    
    try:
        response = httpx.get(
            "https://api.groq.com/openai/v1/models",
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            models = data.get("data", [])
            
            print(f"Available Groq Models ({len(models)}):\n")
            for model in models:
                model_id = model.get("id", "")
                owned_by = model.get("owned_by", "")
                print(f"  - {model_id} (by {owned_by})")
        else:
            print(f"Error: {response.status_code}")
            print(f"Details: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")


if __name__ == "__main__":
    list_groq_models()
