"""Test Twilio webhook locally."""

import hashlib
import httpx
from core.supabase_db import db

def generate_short_code(draft_id: str) -> str:
    """Generate a 6-character short code from draft ID."""
    return hashlib.md5(draft_id.encode()).hexdigest()[:6].upper()

def test_webhook():
    """Test the Twilio webhook with a sample YES response."""
    
    # Get a pending draft
    result = (
        db.client.table("email_drafts")
        .select("*, leads(*)")
        .eq("status", "generated")
        .limit(1)
        .execute()
    )
    
    if not result.data:
        print("No pending drafts found. Run the pipeline first.")
        return
    
    draft = result.data[0]
    draft_id = draft["id"]
    short_code = generate_short_code(draft_id)
    
    lead = draft.get("leads")
    if lead:
        email = lead.get("email", "")
        print(f"\nFound pending draft:")
        print(f"  Draft ID: {draft_id}")
        print(f"  Short Code: {short_code}")
        print(f"  Email: {email}")
    else:
        print(f"\nFound pending draft: {draft_id}")
        print(f"Short Code: {short_code}")
    
    print(f"\nTo test the webhook, send an SMS to your Twilio number:")
    print(f"  YES {short_code}")
    print(f"\nOr test locally (requires ngrok and Twilio webhook configured):")
    print(f"  curl -X POST http://localhost:8000/twilio/reply \\")
    print(f"    -d 'Body=YES {short_code}' \\")
    print(f"    -d 'From=+1234567890'")
    
    print(f"\nWebhook URL to configure in Twilio console:")
    print(f"  https://your-ngrok-url.ngrok-free.app/twilio/reply")
    print(f"\nOr use the PUBLIC_BASE_URL from .env:")
    from core.config import settings
    if settings.public_base_url:
        print(f"  {settings.public_base_url}/twilio/reply")

if __name__ == "__main__":
    test_webhook()
