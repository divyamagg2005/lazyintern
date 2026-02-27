"""
Gmail OAuth Token Generator (Web Application Flow)
This version works with your existing web application credentials.
"""

from google_auth_oauthlib.flow import InstalledAppFlow
import json
from pathlib import Path

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

def generate_token():
    secrets_dir = Path("secrets")
    secrets_dir.mkdir(exist_ok=True)
    
    # Use your existing web credentials
    credentials_path = secrets_dir / "client_secret_491999044903-b38fuutfmg31n2kllhou9fpaiofe0tuv.apps.googleusercontent.com.json"
    token_path = secrets_dir / "gmail_token.json"
    
    if not credentials_path.exists():
        print(f"❌ Error: {credentials_path} not found!")
        return
    
    print(f"✓ Found credentials file: {credentials_path}")
    print("\n🔐 Starting OAuth flow...")
    print("A browser window will open on port 8000...")
    print("Please log in and click 'Allow'\n")
    
    try:
        # Create OAuth flow with specific port to match redirect URI
        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_path), 
            SCOPES,
            redirect_uri='http://localhost:8000/auth/callback'
        )
        
        # Run local server on port 8000 to match your redirect URI
        creds = flow.run_local_server(
            port=8000,
            authorization_prompt_message='Please visit this URL: {url}',
            success_message='Authorization successful! You can close this window.',
            open_browser=True
        )
        
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
        
        print(f"\n✅ Token saved successfully to: {token_path}")
        print("\n✓ You can now use the Gmail API!")
        print("✓ This token will auto-refresh when needed.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nIf you see 'redirect_uri_mismatch', you need to:")
        print("1. Go to: https://console.cloud.google.com/apis/credentials")
        print("2. Click on your OAuth client ID")
        print("3. Make sure 'http://localhost:8000/auth/callback' is in Authorized redirect URIs")
        print("4. Save and wait 5 minutes for changes to propagate")
        print("\nOR use Desktop Application credentials instead (see FIX_GMAIL_OAUTH.md)")

if __name__ == "__main__":
    print("=" * 60)
    print("Gmail OAuth Token Generator (Web Flow)")
    print("=" * 60)
    generate_token()
