from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str
    supabase_service_role_key: str
    supabase_anon_key: str | None = None

    groq_api_key: str | None = None
    groq_model: str = "llama-3.1-70b-versatile"

    hunter_api_key: str | None = None
    firecrawl_api_key: str | None = None

    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_from_number: str | None = None
    approver_to_number: str | None = None
    public_base_url: str | None = None

    gmail_oauth_client_path: str = "secrets/gmail_oauth_client.json"
    gmail_token_path: str = "secrets/gmail_token.json"
    gmail_sender: str = "me"
    gmail_account_created_date: str | None = None

    enable_smtp_ping: bool = False


settings = Settings()  # singleton

