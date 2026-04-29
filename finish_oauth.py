#!/usr/bin/env python3
"""
Run this script on your Mac to complete OAuth token exchange.
The authorization code has been obtained; this exchanges it for the token.
"""

import json
import requests
from pathlib import Path

# Authorization code from the Google redirect
AUTH_CODE = "4/0AeoWuM_PraNmm5zGcplb0ZB8T93j2yM8y2tLcpl-V6iHKyhe38YVQ5KvIITRDKT2REARJQ"

CONFIG_DIR = Path.home() / ".neon_blonde"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"
TOKEN_FILE = CONFIG_DIR / "token.json"

print("\n" + "="*70)
print("Completing OAuth Token Exchange")
print("="*70 + "\n")

# Load credentials
try:
    with open(CREDENTIALS_FILE, 'r') as f:
        creds = json.load(f)['installed']
except FileNotFoundError:
    print(f"❌ credentials.json not found at {CREDENTIALS_FILE}")
    exit(1)

# Exchange code for token
token_url = "https://oauth2.googleapis.com/token"
payload = {
    'code': AUTH_CODE,
    'client_id': creds['client_id'],
    'client_secret': creds['client_secret'],
    'redirect_uri': 'http://localhost:8080/',
    'grant_type': 'authorization_code'
}

print("🔄 Exchanging authorization code for token...")
try:
    response = requests.post(token_url, data=payload)
    
    if response.status_code == 200:
        token_data = response.json()
        
        # Save token
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f, indent=2)
        
        print("✅ Token saved successfully!")
        print(f"📁 Location: {TOKEN_FILE}\n")
        print("Next step: Run the deployment checklist to add GitHub Secrets.\n")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        exit(1)
        
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
