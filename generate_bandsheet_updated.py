#!/usr/bin/env python3
"""
Generate Neon Blonde Band Sheet from Google Docs Master Schedule.
Reads Master Schedule Google Doc and Calendar API for member availability.
Outputs as JSON in existing bandsheet format.
"""

import json
import sys
import os
import base64
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build

# Configuration
CALENDAR_ID = "neonblondevc@gmail.com"
PT_TZ = ZoneInfo("America/Los_Angeles")

# IMPORTANT: Set this to your Master Schedule Google Doc ID
# You can find it in the URL: https://docs.google.com/document/d/{DOC_ID}/edit
MASTER_SCHEDULE_DOC_ID = os.getenv("MASTER_SCHEDULE_DOC_ID", "")

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/documents.readonly"
]

CONFIG_DIR = Path.home() / ".neon_blonde"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"
TOKEN_FILE = CONFIG_DIR / "token.json"


def get_credentials():
    """Load or refresh OAuth credentials."""
    creds = None
    
    # First, check for base64-encoded token (GitHub Actions)
    oauth_token_b64 = os.getenv("NEON_BLONDE_OAUTH_TOKEN_B64")
    if oauth_token_b64:
        try:
            token_json = base64.b64decode(oauth_token_b64).decode('utf-8')
            token_dict = json.loads(token_json)
            creds = Credentials.from_authorized_user_info(token_dict, SCOPES)
            print("✓ Loaded credentials from NEON_BLONDE_OAUTH_TOKEN_B64", file=sys.stderr)
            return creds
        except Exception as e:
            print(f"✗ Failed to decode NEON_BLONDE_OAUTH_TOKEN_B64: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Try loading from token file (local development)
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        print("✓ Loaded credentials from token.json", file=sys.stderr)
    
    # Refresh if needed
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            print("✓ Refreshed OAuth token", file=sys.stderr)
        except RefreshError as e:
            print(f"✗ Token refresh failed: {e}", file=sys.stderr)
            print("Run: python3 finish_oauth.py", file=sys.stderr)
            sys.exit(1)
    
    # If no creds at all, need user to authorize
    if not creds:
        print("✗ No credentials found. Run: python3 finish_oauth.py", file=sys.stderr)
        sys.exit(1)
    
    return creds

