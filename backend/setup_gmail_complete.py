"""
Complete Gmail API Setup Wizard
Guides you through the entire setup process.
"""

from pathlib import Path
from core.config import settings

def check_oauth_file():
    """Check if OAuth client file exists."""
    client_path = Path(settings.gmail_oauth_client_path)
    return client_path.exists(), client_path

def check_token_file():
    """Check if token file exists."""
    token_path = Path(settings.gmail_token_path)
    return token_path.exists(), token_path

def print_step(number, title):
    """Print a step header."""
    print(f"\n{'='*70}")
    print(f"STEP {number}: {title}")
    print('='*70)

def main():
    """Run the complete setup wizard."""
    
    print("="*70)
    print("Gmail API Setup Wizard")
    print("="*70)
    print("\nThis wizard will guide you through setting up Gmail API.")
    print("Estimated time: 10 minutes")
    
    # Step 1: Check OAuth credentials
    print_step(1, "Check OAuth Credentials")
    
    oauth_exists, oauth_path = check_oauth_file()
    
    if oauth_exists:
        print(f"✓ OAuth credentials found: {oauth_path.name}")
    else:
        print(f"✗ OAuth credentials NOT found")
        print(f"\nExpected location: {oauth_path}")
        print("\nYou need to:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project (or select existing)")
        print("3. Enable Gmail API")
        print("4. Create OAuth 2.0 credentials (Desktop app)")
        print("5. Download the JSON file")
        print("6. Place it at: backend/secrets/client_secret_*.json")
        print("\nDetailed instructions: See GMAIL_API_SETUP_GUIDE.md")
        
        input("\nPress Enter when you've placed the OAuth file...")
        
        # Check again
        oauth_exists, oauth_path = check_oauth_file()
        if not oauth_exists:
            print("\n✗ File still not found. Please check the path and try again.")
            return
        else:
            print(f"\n✓ OAuth credentials found: {oauth_path.name}")
    
    # Step 2: Check token
    print_step(2, "Check Authorization Token")
    
    token_exists, token_path = check_token_file()
    
    if token_exists:
        print(f"✓ Token found: {token_path.name}")
        print("\nYou're already authorized!")
        
        response = input("\nDo you want to re-authorize? (yes/no): ").strip().lower()
        if response in ['yes', 'y']:
            print("\nDeleting existing token...")
            token_path.unlink()
            token_exists = False
    
    if not token_exists:
        print("\nStarting authorization process...")
        print("\nThis will:")
        print("1. Open your browser")
        print("2. Ask you to sign in to Gmail")
        print("3. Request permission to send emails")
        print("4. Save the authorization token")
        
        response = input("\nReady to authorize? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("\nSetup cancelled.")
            return
        
        print("\nRunning authorization...")
        import authorize_gmail
        authorize_gmail.authorize_gmail()
        
        # Check if token was created
        token_exists, token_path = check_token_file()
        if not token_exists:
            print("\n✗ Authorization failed. Token not created.")
            return
    
    # Step 3: Test email sending
    print_step(3, "Test Email Sending")
    
    print("\nWe'll send a test email to verify everything works.")
    response = input("Send test email? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print("\nSending test email...")
        import test_gmail_send
        test_gmail_send.test_gmail()
    else:
        print("\nSkipped test email.")
    
    # Step 4: Send all drafts
    print_step(4, "Send Pending Drafts")
    
    # Count pending drafts
    from core.supabase_db import db
    result = db.client.table("email_drafts").select("id", count="exact").eq("status", "generated").execute()
    pending_count = result.count or 0
    
    if pending_count == 0:
        print("\nNo pending drafts to send.")
    else:
        print(f"\nYou have {pending_count} pending draft(s) ready to send.")
        response = input(f"\nSend all {pending_count} emails now? (yes/no): ").strip().lower()
        
        if response in ['yes', 'y']:
            print("\nSending all drafts...")
            import send_all_drafts
            send_all_drafts.send_all_pending_drafts()
        else:
            print("\nSkipped sending drafts.")
            print(f"\nYou can send them later by running:")
            print("  python send_all_drafts.py")
    
    # Final summary
    print("\n" + "="*70)
    print("SETUP COMPLETE!")
    print("="*70)
    print("\n✓ Gmail API configured")
    print("✓ Authorization token saved")
    print("✓ Ready to send emails")
    
    print("\nYour pipeline is now fully operational!")
    print("\nNext steps:")
    print("1. Run pipeline: python -m scheduler.cycle_manager --once")
    print("2. Approve drafts via SMS: Reply 'YES {code}'")
    print("3. Emails send automatically on approval")
    print("4. Monitor replies in Gmail")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
    except Exception as e:
        print(f"\n\nSetup failed: {e}")
        import traceback
        traceback.print_exc()
