#!/usr/bin/env python3
"""Headless OAuth setup - generates authorization URL for user to open manually."""

import os
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file"
]

CONFIG_DIR = Path.home() / ".neon_blonde"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"
TOKEN_FILE = CONFIG_DIR / "token.json"

def main():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("Neon Blonde OAuth Setup (Headless)")
    print("="*70 + "\n")
    
    if not CREDENTIALS_FILE.exists():
        print(f"❌ credentials.json not found at: {CREDENTIALS_FILE}")
        return False
    
    print("📝 Reading credentials...")
    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_FILE), 
        SCOPES
    )
    
    print("🔗 Generating authorization URL...\n")
    auth_url, _ = flow.authorization_url(prompt='consent')
    
    print("COPY THIS LINK AND PASTE INTO YOUR BROWSER:")
    print("-" * 70)
    print(auth_url)
    print("-" * 70)
    print("\n✅ After you authorize in the browser, the token will be saved.\n")
    
    # Run the local server to catch the redirect
    print("⏳ Waiting for authorization (local server listening on localhost:8080)...\n")
    try:
        credentials = flow.run_local_server(port=8080, open_browser=False)
        
        # Save the token
        token_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f)
        
        print("✅ Token saved successfully!")
        print(f"📁 Location: {TOKEN_FILE}\n")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
