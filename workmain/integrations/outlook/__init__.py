"""
Outlook (Microsoft Graph API) integration package.
Provides OAuth client for calendar sync and email draft creation.
"""

from workmain.integrations.outlook.client import OutlookClient, get_outlook_client

__all__ = ["OutlookClient", "get_outlook_client"]
