from __future__ import annotations

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str
    supabase_service_role_key: str
    supabase_anon_key: Optional[str] = None

    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"

    hunter_api_key: Optional[str] = None
    firecrawl_api_key: Optional[str] = None

    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_from_number: Optional[str] = None
    approver_to_number: Optional[str] = None
    public_base_url: Optional[str] = None

    gmail_oauth_client_path: str = "secrets/gmail_oauth_client.json"
    gmail_token_path: str = "secrets/gmail_token.json"
    gmail_sender: str = "me"

    enable_smtp_ping: bool = False


settings = Settings()  # singleton

