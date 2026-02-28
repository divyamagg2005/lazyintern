"""
Gmail OAuth Authorization Script
Run this once to authorize Gmail API access.
"""

from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from core.config import settings

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def authorize_gmail():
    """Authorize Gmail API and save token."""
    
    print("=" * 70)
    print("Gmail API Authorization")
    print("=" * 70)
    
    # Check if client secret exists
    client_secret_path = Path(settings.gmail_oauth_client_path)
    if not client_secret_path.exists():
        print(f"\n❌ ERROR: OAuth client file not found!")
        print(f"Expected location: {client_secret_path}")
        print(f"\nPlease:")
        print("1. Download OAuth credentials from Google Cloud Console")
        print("2. Place the file at: backend/secrets/client_secret_*.json")
        print("3. Update GMAIL_OAUTH_CLIENT_PATH in .env if needed")
        return
    
    print(f"\n✓ Found OAuth client file: {client_secret_path.name}")
    
    # Check if token already exists
    token_path = Path(settings.gmail_token_path)
    if token_path.exists():
        print(f"\n⚠️  Token already exists at: {token_path}")
        response = input("Do you want to re-authorize? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Authorization cancelled.")
            return
        print("\nDeleting existing token...")
        token_path.unlink()
    
    # Start OAuth flow
    print("\n" + "=" * 70)
    print("Starting OAuth flow...")
    print("=" * 70)
    print("\nYour browser will open shortly.")
    print("Please:")
    print("1. Sign in to your Gmail account")
    print("2. Click 'Advanced' if you see a warning")
    print("3. Click 'Go to LazyIntern (unsafe)'")
    print("4. Click 'Allow' to grant Gmail send permissions")
    print("\nWaiting for authorization...")
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_secret_path), 
            SCOPES
        )
        creds = flow.run_local_server(port=8080)
        
        # Save token
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")
        
        print("\n" + "=" * 70)
        print("✓ Authorization successful!")
        print("=" * 70)
        print(f"\nToken saved to: {token_path}")
        print("\nYou can now send emails via Gmail API.")
        print("\nNext steps:")
        print("1. Test email sending: python test_gmail_send.py")
        print("2. Send all drafts: python send_all_drafts.py")
        
    except Exception as e:
        print(f"\n❌ Authorization failed: {e}")
        print("\nTroubleshooting:")
        print("- Make sure you're using the correct Google account")
        print("- Check that your email is added as a test user in OAuth consent screen")
        print("- Try using an incognito browser window")

if __name__ == "__main__":
    authorize_gmail()
