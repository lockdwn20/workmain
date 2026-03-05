"""
WorkmAIn Outlook Integration Client
Outlook Client v1.0
20260305

Single integration point for all Microsoft Graph API interactions.
All methods are stubbed — OAuth requires Azure AD app registration.

Both `workmain calendar` and `workmain email` import from this module.
Token management and scope declarations are complete so that future
OAuth implementation requires only credential provisioning, not
architectural changes.

OAuth Scopes required when Azure AD app registration is available:
    Calendars.Read   — read calendar events
    Mail.ReadWrite   — create and read email drafts
    Mail.Send        — send email

Token file: ~/.workmain/outlook_tokens.json  (chmod 600)
Client credentials: OUTLOOK_CLIENT_ID, OUTLOOK_CLIENT_SECRET,
                    OUTLOOK_TENANT_ID  in .env  (chmod 600)

See docs/OAUTH_SETUP.md for setup instructions.

Version History:
- v1.0: Initial stub implementation (Phase 6 Gate 2)
"""

import json
import os
from datetime import datetime
from pathlib import Path


# OAuth scopes required for full Outlook integration
REQUIRED_SCOPES = [
    "Calendars.Read",    # read calendar events
    "Mail.ReadWrite",    # create and read email drafts
    "Mail.Send",         # send email
]

# Token file location
TOKEN_FILE = Path.home() / ".workmain" / "outlook_tokens.json"

# Token file structure (written on first authenticate() call)
_TOKEN_STRUCTURE = {
    "access_token": "",
    "refresh_token": "",
    "expires_at": "",
    "scopes": [],
}

_STUB_MESSAGE = "OAuth requires Azure AD app registration. See docs/OAUTH_SETUP.md"


class OutlookClient:
    """
    Microsoft Graph API client for calendar and email operations.

    All methods raise NotImplementedError until Azure AD app registration
    credentials are provisioned in .env and OAuth flow is implemented.

    Token file path:  ~/.workmain/outlook_tokens.json
    Required .env vars:
        OUTLOOK_CLIENT_ID
        OUTLOOK_CLIENT_SECRET
        OUTLOOK_TENANT_ID
    """

    def __init__(self):
        self.client_id = os.getenv("OUTLOOK_CLIENT_ID")
        self.client_secret = os.getenv("OUTLOOK_CLIENT_SECRET")
        self.tenant_id = os.getenv("OUTLOOK_TENANT_ID")

    # ------------------------------------------------------------------
    # Token management (file helpers — usable once OAuth is implemented)
    # ------------------------------------------------------------------

    def _read_token_file(self) -> dict:
        """Read token file if it exists, return empty structure otherwise."""
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, "r") as f:
                return json.load(f)
        return dict(_TOKEN_STRUCTURE)

    def _write_token_file(self, tokens: dict) -> None:
        """Write token file with restricted permissions (chmod 600)."""
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(json.dumps(tokens, indent=2))
        TOKEN_FILE.chmod(0o600)

    # ------------------------------------------------------------------
    # OAuth methods (all stubbed)
    # ------------------------------------------------------------------

    def authenticate(self) -> None:
        """
        Initiate OAuth 2.0 flow against Azure AD.

        Requires app registration in organization's Azure AD tenant.
        Stores access_token and refresh_token to
        ~/.workmain/outlook_tokens.json (chmod 600).

        NotImplemented until Azure AD app registration is available.
        """
        raise NotImplementedError(_STUB_MESSAGE)

    def refresh_token(self) -> None:
        """
        Use stored refresh_token to obtain new access_token silently.

        Updates outlook_tokens.json with new token and expiry.
        NotImplemented until Azure AD app registration is available.
        """
        raise NotImplementedError(_STUB_MESSAGE)

    def is_authenticated(self) -> bool:
        """
        Check if valid tokens exist and are not expired.

        NotImplemented until Azure AD app registration is available.
        """
        raise NotImplementedError(_STUB_MESSAGE)

    # ------------------------------------------------------------------
    # Calendar methods (all stubbed)
    # ------------------------------------------------------------------

    def get_calendar_events(self, start: datetime, end: datetime) -> list[dict]:
        """
        Fetch calendar events from Microsoft Graph API.

        Endpoint: GET /me/calendarView?startDateTime=<start>&endDateTime=<end>

        Returns list of event dicts with:
            id, subject, start, end, isRecurring, seriesMasterId

        NotImplemented until Azure AD app registration is available.
        """
        raise NotImplementedError(_STUB_MESSAGE)

    # ------------------------------------------------------------------
    # Email methods (all stubbed)
    # ------------------------------------------------------------------

    def create_draft(
        self,
        subject: str,
        body: str,
        to: list[str],
        cc: list[str],
    ) -> str:
        """
        Create email draft in Outlook via Graph API.

        Endpoint: POST /me/messages
        Returns draft message ID.
        NotImplemented until Azure AD app registration is available.
        """
        raise NotImplementedError(_STUB_MESSAGE)

    def send_email(self, message_id: str) -> None:
        """
        Send a previously created draft.

        Endpoint: POST /me/messages/{id}/send
        NotImplemented until Azure AD app registration is available.
        """
        raise NotImplementedError(_STUB_MESSAGE)


def get_outlook_client() -> OutlookClient:
    """Factory function — returns OutlookClient instance."""
    return OutlookClient()
