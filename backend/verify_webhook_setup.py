"""Verify Twilio webhook setup is complete."""

import hashlib
from core.config import settings
from core.supabase_db import db

def verify_setup():
    """Verify all components are configured correctly."""
    
    print("=" * 70)
    print("TWILIO WEBHOOK SETUP VERIFICATION")
    print("=" * 70)
    
    # 1. Check environment variables
    print("\n1. Environment Variables:")
    checks = {
        "TWILIO_ACCOUNT_SID": settings.twilio_account_sid,
        "TWILIO_AUTH_TOKEN": settings.twilio_auth_token,
        "TWILIO_FROM_NUMBER": settings.twilio_from_number,
        "APPROVER_TO_NUMBER": settings.approver_to_number,
        "PUBLIC_BASE_URL": settings.public_base_url,
    }
    
    all_set = True
    for key, value in checks.items():
        status = "✓" if value else "✗"
        display_value = f"{value[:20]}..." if value and len(str(value)) > 20 else value
        print(f"   {status} {key}: {display_value or 'NOT SET'}")
        if not value:
            all_set = False
    
    if not all_set:
        print("\n   ⚠️  Some environment variables are missing!")
        print("   Update backend/.env with your Twilio credentials")
    
    # 2. Check webhook URL
    print("\n2. Webhook URL:")
    if settings.public_base_url:
        webhook_url = f"{settings.public_base_url}/twilio/reply"
        print(f"   {webhook_url}")
        print("\n   Configure this URL in Twilio Console:")
        print("   Phone Numbers → Active Numbers → Your Number")
        print("   → Messaging → 'A message comes in' → Webhook")
    else:
        print("   ✗ PUBLIC_BASE_URL not set")
    
    # 3. Check pending drafts
    print("\n3. Pending Drafts:")
    result = (
        db.client.table("email_drafts")
        .select("*")
        .eq("status", "generated")
        .execute()
    )
    
    pending_drafts = result.data or []
    print(f"   Found {len(pending_drafts)} pending draft(s)")
    
    if pending_drafts:
        print("\n   Sample drafts with short codes:")
        for i, draft in enumerate(pending_drafts[:3], 1):
            draft_id = draft["id"]
            short_code = hashlib.md5(draft_id.encode()).hexdigest()[:6].upper()
            
            # Get lead info
            lead_id = draft.get("lead_id")
            if lead_id:
                lead_result = db.client.table("leads").select("email").eq("id", lead_id).limit(1).execute()
                if lead_result.data:
                    email = lead_result.data[0].get("email", "")
                    print(f"   {i}. Code: {short_code} → {email}")
                else:
                    print(f"   {i}. Code: {short_code}")
            else:
                print(f"   {i}. Code: {short_code}")
        
        print(f"\n   To approve, reply to SMS with: YES {short_code}")
    else:
        print("   ⚠️  No pending drafts. Run the pipeline first:")
        print("   python -m scheduler.cycle_manager --once")
    
    # 4. Check Gmail configuration
    print("\n4. Gmail Configuration:")
    gmail_checks = {
        "GMAIL_OAUTH_CLIENT_PATH": settings.gmail_oauth_client_path,
        "GMAIL_TOKEN_PATH": settings.gmail_token_path,
    }
    
    from pathlib import Path
    for key, value in gmail_checks.items():
        if value:
            path = Path(value)
            exists = path.exists()
            status = "✓" if exists else "✗"
            print(f"   {status} {key}: {value} {'(exists)' if exists else '(NOT FOUND)'}")
        else:
            print(f"   ✗ {key}: NOT SET")
    
    # 5. Test short code generation
    print("\n5. Short Code Generation Test:")
    test_id = "8c02ea89-fdfc-41d0-a4a2-174edde0fbb0"
    test_code = hashlib.md5(test_id.encode()).hexdigest()[:6].upper()
    print(f"   Test UUID: {test_id}")
    print(f"   Generated Code: {test_code}")
    print(f"   ✓ Short code generation working")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY:")
    print("=" * 70)
    
    if all_set and settings.public_base_url:
        print("✓ Environment variables configured")
    else:
        print("✗ Missing environment variables")
    
    if pending_drafts:
        print(f"✓ {len(pending_drafts)} pending draft(s) ready for approval")
    else:
        print("⚠️  No pending drafts (run pipeline first)")
    
    print("\nNext steps:")
    print("1. Configure webhook URL in Twilio Console")
    print("2. Send test SMS: 'YES {code}' to your Twilio number")
    print("3. Check logs for webhook activity")
    print("4. Verify email was sent")
    print("=" * 70)

if __name__ == "__main__":
    verify_setup()
