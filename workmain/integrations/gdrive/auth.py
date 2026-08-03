"""
OAuth2 credential management for Google Drive integration.
WSL-safe: uses run_console() (copy-paste URL + code) — no browser spawn.

Token file:       ~/.workmain/integrations/gdrive/token.json  (chmod 600)
Credentials file: ~/.workmain/integrations/gdrive/credentials.json  (chmod 600)
Scope:            https://www.googleapis.com/auth/drive.file
  (least-privilege — app can only see files it creates)
"""

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


CREDENTIALS_PATH = Path.home() / ".workmain" / "integrations" / "gdrive" / "credentials.json"
TOKEN_PATH       = Path.home() / ".workmain" / "integrations" / "gdrive" / "token.json"
SCOPES           = ["https://www.googleapis.com/auth/drive.file"]


class GDriveAuthError(Exception):
    """Raised when Google Drive authentication fails or credentials are missing."""


def get_credentials() -> Credentials:
    """
    Load and return valid Google Drive credentials.

    Behaviour:
    - If TOKEN_PATH exists and is valid: return immediately.
    - If token is expired but has a refresh token: refresh silently.
    - If no token or refresh fails: run WSL-safe console flow (run_console),
      which prints a URL for the user to visit and waits for a pasted auth code.
    - Saves the token to TOKEN_PATH (chmod 600) after any new auth.

    Returns:
        Valid google.oauth2.credentials.Credentials instance.

    Raises:
        GDriveAuthError: If credentials.json is missing.
    """
    if not CREDENTIALS_PATH.exists():
        raise GDriveAuthError(
            f"Google Drive credentials not found at {CREDENTIALS_PATH}.\n"
            "Download your OAuth client secret from Google Cloud Console\n"
            "and place it at that path (chmod 600)."
        )

    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # WSL-safe console flow — prints URL, waits for pasted code
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_console()

        # Persist token (chmod 600)
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json())
        TOKEN_PATH.chmod(0o600)

    return creds


def get_service():
    """
    Build and return an authenticated Google Drive v3 service.

    Returns:
        Authenticated Drive v3 Resource object.

    Raises:
        GDriveAuthError: If credentials.json is missing.
    """
    creds = get_credentials()
    return build("drive", "v3", credentials=creds)


def is_authenticated() -> bool:
    """
    Return True if a valid (non-expired) token exists without attempting refresh.

    Used by `gdocs status` for a quick auth state check — does not trigger
    any OAuth flow.

    Returns:
        True if TOKEN_PATH exists and the token is currently valid.
    """
    if not TOKEN_PATH.exists():
        return False
    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        return creds is not None and creds.valid
    except Exception:
        return False
