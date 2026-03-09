"""
WorkmAIn Outlook Integration Package
outlook/__init__.py v1.0
20260309

Outlook (Microsoft Graph API) integration package.
Provides OAuth client for calendar sync and email draft creation.

Version History:
- v1.0: Gate 0.2 — moved from integrations/outlook_client.py (Phase 7)
"""

from workmain.integrations.outlook.client import OutlookClient, get_outlook_client

__all__ = ["OutlookClient", "get_outlook_client"]
__version__ = "1.0"
