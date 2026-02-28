from core.config import settings

print(f"Key length: {len(settings.groq_api_key)}")
print(f"Starts with gsk_: {settings.groq_api_key.startswith('gsk_')}")
print(f"First 10 chars: {settings.groq_api_key[:10]}")
