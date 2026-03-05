WorkmAIn
OAUTH_SETUP.md v1.0
20260305

---

# Outlook OAuth Setup — Microsoft Graph API

This document describes what is required to enable live Outlook calendar sync
and email send functionality in WorkmAIn.

These features are currently stubbed. The infrastructure (scopes, token file,
client class) is complete. Only credential provisioning is required to activate.

---

## What Is Blocked

Corporate Azure AD access restrictions prevent direct OAuth app registration
at this time. When app registration becomes available, follow this guide.

---

## Azure AD App Registration Requirements

A Global Administrator (or Application Administrator) on the organization's
Azure AD tenant must:

1. Register a new application in Azure Active Directory
2. Grant the following API permissions (Microsoft Graph, Delegated):
   - `Calendars.Read` — read calendar events
   - `Mail.ReadWrite` — create and read email drafts
   - `Mail.Send` — send email
3. Grant admin consent for the above permissions
4. Create a client secret under the app registration
5. Note the Application (client) ID, client secret value, and Directory (tenant) ID

---

## Required .env Variables

Add the following to `.env` (chmod 600) once app registration is complete:

```
OUTLOOK_CLIENT_ID=<Application (client) ID from Azure AD>
OUTLOOK_CLIENT_SECRET=<Client secret value from Azure AD>
OUTLOOK_TENANT_ID=<Directory (tenant) ID from Azure AD>
```

These are the static Azure AD app registration credentials. They are distinct
from the user tokens (access_token / refresh_token) which rotate automatically
and are stored separately in the token file.

---

## Required OAuth Scopes

The following Microsoft Graph API scopes must be granted during app registration:

| Scope | Type | Purpose |
|-------|------|---------|
| `Calendars.Read` | Delegated | Read calendar events via Graph API |
| `Mail.ReadWrite` | Delegated | Create and read email drafts |
| `Mail.Send` | Delegated | Send email from Outlook |

---

## Token File

After a successful OAuth authentication flow, user tokens are stored at:

```
~/.workmain/outlook_tokens.json
```

Permissions: chmod 600 (set automatically on write)

Structure:
```json
{
  "access_token": "",
  "refresh_token": "",
  "expires_at": "",
  "scopes": []
}
```

This file contains user-specific tokens that rotate. It is separate from the
`.env` app registration credentials. Do not commit either file to version control.

---

## Commands That Activate Once OAuth Is Configured

| Command | What It Does |
|---------|-------------|
| `workmain calendar today sync` | Pull today's events from Outlook via Graph API |
| `workmain calendar week sync` | Pull this week's events from Outlook |
| `workmain calendar month sync` | Pull this month's events from Outlook |
| `workmain calendar today/week/month` | Live data (no --offline needed) |
| `workmain email save <template>` | Generate draft and push to Outlook Drafts |
| `workmain email send <template>` | Send draft via Outlook |
| `workmain report send <template>` | Generate report and send via email pipeline |

Until OAuth is configured, use the ICS import path for calendar data:
```
workmain calendar import <file.ics>
```

---

## Implementation Notes (For Future Implementer)

- OAuth flow is implemented in `workmain/integrations/outlook_client.py`
- All method signatures, docstrings, and token file management are complete
- To activate: provision credentials in `.env`, implement the `authenticate()`
  method body using MSAL (Microsoft Authentication Library for Python),
  then implement `refresh_token()` and `is_authenticated()`
- The calendar and email CLI commands import `OutlookClient` from
  `workmain.integrations.outlook_client` — no import changes needed

MSAL package: `pip install msal`
Microsoft Graph API docs: https://learn.microsoft.com/en-us/graph/api/overview
