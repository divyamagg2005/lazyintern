"""
Gmail OAuth Token Generator
Run this once to generate gmail_token.json in the secrets folder.
A browser window will open - log into your Gmail account and click Allow.
"""

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json
import os
from pathlib import Path

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

def generate_token():
    # Paths
    secrets_dir = Path("secrets")
    secrets_dir.mkdir(exist_ok=True)
    
    token_path = secrets_dir / "gmail_token.json"
    
    # Look for credentials file (try multiple names)
    possible_creds = [
        secrets_dir / "gmail_oauth_client.json",
        secrets_dir / "credentials.json",
    ]
    
    # Also check for any client_secret_*.json files
    for file in secrets_dir.glob("client_secret_*.json"):
        possible_creds.append(file)
    
    credentials_path = None
    for path in possible_creds:
        if path.exists():
            credentials_path = path
            break
    
    # Check if credentials file exists
    if not credentials_path:
        print(f"❌ Error: No credentials file found in {secrets_dir}!")
        print("\nPlease download your OAuth 2.0 Client ID credentials from:")
        print("https://console.cloud.google.com/apis/credentials")
        print(f"\nSave it as: {secrets_dir / 'gmail_oauth_client.json'}")
        return
    
    print(f"✓ Found credentials file: {credentials_path}")
    print("\n🔐 Starting OAuth flow...")
    print("A browser window will open. Please:")
    print("  1. Log into your Gmail account")
    print("  2. Click 'Allow' to grant permissions")
    print("  3. Wait for confirmation\n")
    
    try:
        # Create OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_path), 
            SCOPES
        )
        
        # Run local server to handle OAuth callback
        creds = flow.run_local_server(port=0)
        
        # Save token as JSON
        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        
        with open(token_path, 'w') as token_file:
            json.dump(token_data, token_file, indent=2)
        
        print(f"✅ Token saved successfully to: {token_path}")
        print("\n✓ You can now use the Gmail API!")
        print("✓ This token will auto-refresh when needed.")
        print("✓ You don't need to run this script again unless you revoke access.")
        
    except Exception as e:
        print(f"\n❌ Error during OAuth flow: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure you have the correct credentials file")
        print("  2. Check that Gmail API is enabled in Google Cloud Console")
        print("  3. Verify the OAuth consent screen is configured")
        print("  4. Try running the script again")

if __name__ == "__main__":
    print("=" * 60)
    print("Gmail OAuth Token Generator")
    print("=" * 60)
    generate_token()
