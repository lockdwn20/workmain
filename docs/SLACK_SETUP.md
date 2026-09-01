WorkmAIn
SLACK_SETUP.md v2.0
20260625

---

# Slack Integration Setup

This document covers the full setup process for WorkmAIn's Slack integration:
outbound report posting (Phase 8) and inbound Socket Mode DM interface (Phase 13).

---

## Overview

WorkmAIn uses a Slack **Bot Token** (`xoxb-`) for API calls and a **Socket Mode
App-Level Token** (`xapp-`) for the persistent WebSocket connection. There is no
user-level OAuth flow — the bot is installed to the workspace once and both tokens
are stored statically in `.env`.

Two capability tiers require different scopes and app configuration:

| Tier | Feature | Phase |
|------|---------|-------|
| **Outbound** | Post weekly draft to a channel | Phase 8 |
| **Inbound** | Receive DMs, parse intent, Block Kit buttons, conversational EOD | Phase 13 |

Both tiers use the same app. Adding inbound support requires additional Bot Token
scopes, a Socket Mode App-Level Token, and several one-time app configuration
changes, followed by a workspace reinstall.

---

## Step 1 — Create the Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps) and click
   **Create New App → From scratch**
2. Name: `WorkmAIn` (or your preferred display name)
3. Select the target workspace
4. Click **Create App**

---

## Step 2 — Configure Bot Token Scopes

Navigate to **Features → OAuth & Permissions → Bot Token Scopes**.

### Phase 8 — Outbound Only

| Scope | Purpose |
|-------|---------|
| `chat:write` | Post messages to channels |
| `auth:test` | Validate token via `auth.test` API call |

### Phase 13 — Add Inbound DM Support

Add these scopes to the existing Phase 8 set:

| Scope | Purpose |
|-------|---------|
| `im:write` | Open DM channels via `conversations.open` |
| `im:read` | List IM channels via `conversations.list` |

**Note:** `im:history` (previously required for polling) is no longer needed.
If it is already present from a prior setup it is harmless but can be removed.

**Important:** Every time scopes are added, Slack requires the app to be
reinstalled to the workspace before the new scopes take effect (see Step 6).

---

## Step 3 — Enable the Messages Tab (Inbound only)

Without this setting, users cannot send messages to the bot and receive
the error: *"Sending messages to this app has been turned off."*

1. In the left sidebar → **Features → App Home**
2. Under **Show Tabs**, find **Messages Tab**
3. Enable **"Allow users to send Slash commands and messages from the
   messages tab"**
4. Save changes

---

## Step 4 — Enable Socket Mode and Configure Events (Inbound only)

Socket Mode delivers inbound messages and Block Kit button interactions over a
persistent outbound WebSocket. No public endpoint or tunnel is required.

### 4a — Enable Socket Mode

1. In the left sidebar → **Settings → Socket Mode**
2. Toggle **Enable Socket Mode** on

### 4b — Subscribe to Bot Events

1. In the left sidebar → **Features → Event Subscriptions**
2. Toggle **Enable Events** on
3. Under **Subscribe to bot events**, click **Add Bot User Event**
4. Add: `message.im`
5. Click **Save Changes**

### 4c — Enable Interactivity (Block Kit buttons)

1. In the left sidebar → **Features → Interactivity & Shortcuts**
2. Toggle **Interactivity** on
3. No Request URL is needed — Socket Mode delivers interaction payloads
   over the WebSocket
4. Click **Save Changes**

---

## Step 5 — Generate the App-Level Token

The `xapp-` App-Level Token is separate from the Bot Token and is required for
Socket Mode. It is generated once and stored in `.env`.

1. In the left sidebar → **Settings → Basic Information**
2. Scroll to **App-Level Tokens**
3. Click **Generate Token and Scopes**
4. Name the token (e.g. `workmain-socket`)
5. Add scope: `connections:write`
6. Click **Generate**
7. Copy the token (begins with `xapp-`)

Add it to `.env` (chmod 600):

```bash
SLACK_SOCKET_TOKEN=xapp-your-token-here
```

App-Level Tokens do not expire unless manually revoked.

---

## Step 6 — Install to Workspace and Obtain the Bot Token

1. Navigate to **Settings → Install App**
2. Click **Install to Workspace** (or **Reinstall** if updating scopes)
3. Review the requested permissions and click **Allow**
4. Copy the **Bot User OAuth Token** (begins with `xoxb-`)

Add it to `.env` (chmod 600):

```bash
SLACK_BOT_TOKEN=xoxb-your-token-here
```

The Bot Token does not expire unless manually revoked.

Whenever Bot Token scopes are added or removed, a yellow banner appears at
the top of the app settings page:

> *"You've changed the permission scopes… Reinstall your app"*

Click **Reinstall to Workspace** and re-authorize. If the token changes,
update `SLACK_BOT_TOKEN` in `.env`, then run:

```bash
workmain slack auth
systemctl --user restart workmain-notify
```

---

## Step 7 — WorkmAIn CLI Configuration

### Validate the Bot Token

```bash
workmain slack auth
```

Expected output: team name, bot user, and "authenticated" status.

### Set the report posting channel (Phase 8)

The outbound weekly post target is stored per-client:

```bash
workmain slack set channel "#your-channel-name"
```

Requires an active client (`workmain clients set active <name>`).

### Set the operator user ID (Phase 13 — inbound DMs)

The daemon opens a DM channel with you at startup. It needs your Slack user ID
to do so.

**Find your Slack user ID:**
- Slack → click your avatar → **Profile** → kebab menu (⋮) → **Copy member ID**
- Starts with `U` (e.g. `U123456789A`)

**Set it:**

```bash
workmain slack set operator-user-id U123456789A
```

This writes `operator_user_id` to
`~/.workmain/integrations/slack/config.json` (chmod 600).

The daemon calls `conversations.open()` at startup to resolve the DM channel.

---

## Config and State Files

| File | Purpose | Permissions |
|------|---------|-------------|
| `.env` — `SLACK_BOT_TOKEN` | Bot Token (`xoxb-`) | 600 |
| `.env` — `SLACK_SOCKET_TOKEN` | App-Level Token (`xapp-`) for Socket Mode | 600 |
| `~/.workmain/integrations/slack/config.json` | workspace_name, operator_user_id | 600 |
| `~/.workmain/daemon/conversation_state.json` | Pending confirmation actions and T5 EOD session state (persisted across restarts) | 600 |

None of these files should be committed to version control.

---

## Useful Diagnostic Commands

```bash
# Validate token and show workspace/bot info
workmain slack auth

# Show auth state, recent posts, and channel configuration
workmain slack status

# Interactive setup checklist
workmain slack setup

# Confirm operator_user_id is set
cat ~/.workmain/integrations/slack/config.json

# Watch daemon log in real time
journalctl --user -u workmain-notify -f
```

Expected daemon log on startup with Socket Mode connected:

```
WorkmAIn daemon starting.
Socket Mode client connecting...
DM channel resolved: D0XXXXXXXXX (operator=U123456789A)
Scheduler starting (blocking).
```

Expected log when a DM is received:

```
WorkmAInSocketClient: dispatching message event ts=...
Slack DM received: user=U123456789A ts=... text='...'
```

---

## Active Commands

| Command | What It Does |
|---------|-------------|
| `workmain slack auth [--reauth]` | Validate token, cache workspace name |
| `workmain slack status` | Auth state, recent posts, channel config |
| `workmain slack setup` | Interactive setup checklist |
| `workmain slack set channel <ch>` | Set posting channel for active client |
| `workmain slack set workspace` | Show workspace config path (informational) |
| `workmain slack set operator-user-id <id>` | Set your Slack user ID for DM resolution |
| `workmain slack post weekly [flags]` | Generate → preview → post weekly draft |

---

## Scope Reference (Complete)

| Scope | Type | Tier | Required By |
|-------|------|------|-------------|
| `chat:write` | Bot Token | Outbound | `workmain slack post weekly` |
| `auth:test` | Bot Token | Both | `workmain slack auth` |
| `im:write` | Bot Token | Inbound | DM channel resolution at startup |
| `im:read` | Bot Token | Inbound | DM channel list |
| `connections:write` | App-Level Token | Inbound | Socket Mode WebSocket connection |
