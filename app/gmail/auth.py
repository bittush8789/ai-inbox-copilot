import os
import json
import logging
from pathlib import Path
from typing import Dict, Any
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from app.gmail.token_manager import load_stored_credentials, save_credentials, delete_stored_credentials

# Setup Logging
logger = logging.getLogger("gmail_auth")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.modify", "https://www.googleapis.com/auth/gmail.compose"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

def validate_gmail_setup() -> Dict[str, bool]:
    cred_path = Path(CREDENTIALS_FILE)
    if not cred_path.exists():
        return {
            "credentials_exists": False,
            "credentials_valid": False,
            "gmail_api_ready": False
        }
    try:
        with open(cred_path, "r") as f:
            data = json.load(f)
        installed = data.get("installed", {})
        required = ["client_id", "project_id", "auth_uri", "token_uri", "client_secret"]
        valid = all(key in installed for key in required)
        return {
            "credentials_exists": True,
            "credentials_valid": valid,
            "gmail_api_ready": valid
        }
    except Exception:
        return {
            "credentials_exists": True,
            "credentials_valid": False,
            "gmail_api_ready": False
        }

def get_gmail_credentials():
    diagnostics = validate_gmail_setup()
    if not diagnostics["credentials_exists"]:
        raise FileNotFoundError(
            "Gmail OAuth credentials not found.\n\n"
            "Please download OAuth Client credentials from Google Cloud Console and place:\n\n"
            "credentials.json\n\n"
            "inside the project root directory."
        )
    if not diagnostics["credentials_valid"]:
        raise ValueError(
            "Invalid credentials.json format.\n"
            "Please download a Desktop App OAuth Client from Google Cloud Console."
        )

    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(TOKEN_FILE, "w") as f:
                    f.write(creds.to_json())
            except Exception:
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                creds = None
        
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
            
    return creds

def get_gmail_service():
    creds = get_gmail_credentials()
    return build("gmail", "v1", credentials=creds)

def get_connected_email() -> str | None:
    try:
        service = get_gmail_service()
        profile = service.users().getProfile(userId="me").execute()
        return profile.get("emailAddress")
    except Exception:
        return None

def is_gmail_connected() -> bool:
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            creds = None
    if not creds:
        return False
    if creds.valid:
        return True
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
            return True
        except Exception:
            return False
    return False

def disconnect_gmail():
    if os.path.exists(TOKEN_FILE):
        try:
            os.remove(TOKEN_FILE)
        except Exception:
            pass
