"""
Test Gmail API by sending a test email to yourself.
"""

from outreach.gmail_client import _load_credentials, _build_service, _create_message_with_attachment
from core.config import settings
from pathlib import Path

def test_gmail():
    """Send a test email to verify Gmail API works."""
    
    print("=" * 70)
    print("Gmail API Test")
    print("=" * 70)
    
    # Load credentials
    print("\n1. Loading Gmail credentials...")
    try:
        creds = _load_credentials()
        print("   ✓ Credentials loaded successfully")
    except Exception as e:
        print(f"   ❌ Failed to load credentials: {e}")
        print("\n   Please run: python authorize_gmail.py")
        return
    
    # Build service
    print("\n2. Building Gmail service...")
    try:
        service = _build_service()
        print("   ✓ Gmail service ready")
    except Exception as e:
        print(f"   ❌ Failed to build service: {e}")
        return
    
    # Get user's email
    print("\n3. Getting your email address...")
    try:
        profile = service.users().getProfile(userId='me').execute()
        user_email = profile.get('emailAddress')
        print(f"   ✓ Sending from: {user_email}")
    except Exception as e:
        print(f"   ❌ Failed to get profile: {e}")
        return
    
    # Check for resume
    resume_path = Path(__file__).resolve().parent / "data" / "resume.pdf"
    has_resume = resume_path.exists()
    if has_resume:
        print(f"\n4. Resume found: {resume_path.name}")
    else:
        print(f"\n4. ⚠️  Resume not found at: {resume_path}")
        print("   Email will be sent without attachment")
    
    # Create test message
    print("\n5. Creating test email...")
    subject = "LazyIntern Gmail API Test"
    body = """Hi,

This is a test email from LazyIntern to verify Gmail API is working correctly.

If you're seeing this, the setup was successful!

Best regards,
LazyIntern Bot
"""
    
    try:
        msg = _create_message_with_attachment(
            to=user_email,
            subject=subject,
            body=body,
            attachment_path=resume_path if has_resume else None
        )
        print("   ✓ Test email created")
    except Exception as e:
        print(f"   ❌ Failed to create message: {e}")
        return
    
    # Send email
    print(f"\n6. Sending test email to {user_email}...")
    try:
        result = service.users().messages().send(
            userId=settings.gmail_sender, 
            body=msg
        ).execute()
        
        message_id = result.get('id')
        print(f"   ✓ Email sent successfully!")
        print(f"   Message ID: {message_id}")
        print(f"\n" + "=" * 70)
        print("SUCCESS!")
        print("=" * 70)
        print(f"\nCheck your inbox: {user_email}")
        print("You should receive the test email within a few seconds.")
        
        if has_resume:
            print("\n✓ Resume attachment included")
        
        print("\nGmail API is working correctly!")
        print("\nNext step: Send all 16 pending drafts")
        print("Run: python send_all_drafts.py")
        
    except Exception as e:
        print(f"   ❌ Failed to send email: {e}")
        print("\nTroubleshooting:")
        print("- Check your internet connection")
        print("- Verify Gmail API is enabled in Google Cloud Console")
        print("- Try re-authorizing: python authorize_gmail.py")

if __name__ == "__main__":
    test_gmail()
