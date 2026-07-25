"""
WorkmAIn CLI
Slack Command Group
slack.py v1.8
20260724

CLI commands for posting reports to Slack.

Commands:
- slack setup                           # Interactive setup checklist
- slack auth [--reauth]                 # Validate Bot Token, cache workspace name
- slack status                          # Auth state + recent Slack posts
- slack set channel <channel>           # Set Slack channel for the active client
- slack set workspace                   # Show workspace config file path (informational)
- slack post PERIOD [flags]             # Generate/review (shared runner) → post; PERIOD=weekly|daily|monthly

Version History:
- v1.0: Initial implementation (Phase 8 Gate 3/4)
- v1.1: Fix post-weekly generation — replace subprocess (invalid --start/--end flags)
        with direct Python API call via get_report_generator()
- v1.2: Phase 9 Gate 1 — updated hint text from 'report save' to 'reports save'
- v1.3: CLI Standardization Sprint Part 1 (WU-2) — renamed command `post-weekly` → `post`;
        added required PERIOD argument (weekly|daily|monthly); guards non-weekly with
        NotImplementedError; renamed function slack_post_weekly → slack_post
- v1.4: Phase 11 Gate 5 — stamp active_client_id on Report INSERT in slack post weekly
- v1.5: Phase 11.5 Gate 2 — retire `slack channel set` (wrote to config.json);
        add `slack set` subgroup with `channel` (writes to clients.slack_channel) and
        `workspace` (informational, no writes); update post-weekly channel resolution
        to read clients.slack_channel first, config.json fallback second;
        update slack status/auth/setup channel display to use same resolution order
- v1.6: Phase 13 Sprint 2 Gate 3 — add `slack set operator-user-id` command for
        inbound DM polling setup
- v1.7: Item #50 hotfix — remove private _format_date_display(), import
        format_date_display() from workmain.utils.date_format instead
- v1.8: Item #61 Gate 4 (Design Rules 9-11) — slack_post()'s entire
        generate → preview → [y/n/e] → own-editor → upsert-with-no-status
        sequence replaced by a call to the shared
        eod_workflow._run_report_review_step() (report_type='weekly_client',
        label='Weekly', require_active_client=True,
        generation_error_fatal=False) — the same runner Friday's weekly EOD
        review uses. Slack delivery is now a separate step after the
        review runner completes, firing only when the resulting status is
        confirmed/corrected; posts report.corrected_content or
        report.content and updates slack_message_ts/slack_channel/
        slack_workspace_name on that same row (no second upsert, no second
        row). --regenerate removed (its staleness-prompt logic has no
        equivalent under G2's confirmed-report re-review design; confirmed
        with Ray). --force/already_posted() REPOST guard kept, relocated
        to the delivery step. --dry-run now short-circuits before the
        review runner with a caller-specific message (still zero side
        effects) instead of previewing staged file content. Removed:
        _run_generation(), _staged_report_path(), _show_preview(),
        _edit_in_editor() (Design Rule 3 — deferred here from Gate 2, now
        dead), _PROJECT_ROOT/_STAGING_REPORTS (no longer referenced).
        _run_slack_weekly_step (eod_workflow.py) traced and confirmed to
        need no changes (Design Rule 11) — it only shells this command as
        a subprocess with no --date.
"""

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.rule import Rule
from rich.table import Table

from workmain.database.connection import get_db
from workmain.database.models import Report
from workmain.integrations.slack.auth import (
    SlackAuthError,
    get_token,
    is_authenticated,
    load_slack_config,
    save_slack_config,
    get_default_channel,
)
from workmain.integrations.slack.client import (
    SlackClient,
    SlackClientError,
    already_posted,
    format_for_slack,
    get_slack_client,
)
from workmain.utils.date_format import format_date_display


console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_channel(channel: str) -> str:
    """Ensure channel name has a # prefix."""
    channel = channel.strip()
    if not channel.startswith("#"):
        channel = f"#{channel}"
    return channel


def _parse_date_arg(date_str: Optional[str]) -> date:
    """Parse YYYYMMDD string to date, defaulting to today."""
    if date_str is None:
        return date.today()
    try:
        return datetime.strptime(date_str, "%Y%m%d").date()
    except ValueError:
        raise click.BadParameter(
            f"Invalid date '{date_str}'. Expected format: YYYYMMDD (e.g. 20260312)."
        )


def get_draft_date_range(anchor: date) -> tuple:
    """
    Return (monday, anchor) for the ISO week containing anchor.

    Args:
        anchor: End date of the range (typically today/Thursday).

    Returns:
        Tuple of (monday, anchor) as date objects.
    """
    monday = anchor - timedelta(days=anchor.weekday())  # weekday() Mon=0
    return monday, anchor


def _resolve_client_channel(session) -> Optional[str]:
    """
    Return the active client's slack_channel, or None if not set.

    Does not fall back to config.json — caller decides fallback behavior.
    """
    from workmain.database.repositories.system_state_repository import SystemStateRepository
    from workmain.database.repositories.client_repository import ClientRepository
    state_repo = SystemStateRepository(session)
    active_client_id = state_repo.get_int('active_client_id')
    if active_client_id:
        client = ClientRepository(session).get_by_id(active_client_id)
        if client and client.slack_channel:
            return client.slack_channel
    return None


def _resolve_slack_channel(session) -> Optional[str]:
    """
    Resolve the Slack channel for post-weekly.

    Priority:
      1. clients.slack_channel for active client (if set)
      2. config.json default_channel (fallback — may be absent post-migration)
      3. None (caller raises error)
    """
    channel = _resolve_client_channel(session)
    if channel:
        return channel
    # Fallback: get_default_channel() returns None silently if key absent.
    return get_default_channel()


def _get_display_channel(session) -> Optional[str]:
    """
    Return the channel string for status/auth/setup display purposes.

    Same resolution order as _resolve_slack_channel() but returns None
    silently rather than raising — display callers decide how to show absence.
    """
    return _resolve_slack_channel(session)


# ---------------------------------------------------------------------------
# Command group
# ---------------------------------------------------------------------------

@click.group()
def slack():
    """Slack integration — post reports to a channel."""


# ---------------------------------------------------------------------------
# slack auth
# ---------------------------------------------------------------------------

@slack.command("auth")
@click.option("--reauth", is_flag=True, default=False,
              help="Re-validate token even if workspace is already cached.")
def slack_auth(reauth: bool):
    """Validate Bot Token against Slack API and cache workspace name."""
    cfg = load_slack_config()

    # If already authenticated and not re-authing, short-circuit
    if cfg.get("workspace_name") and not reauth:
        console.print(
            f"\n[green]✓ Already authenticated[/green] — {cfg['workspace_name']}"
        )
        console.print("  Run with [bold]--reauth[/bold] to re-validate after a token change.")
        return

    # Check token present
    try:
        token = get_token()
    except SlackAuthError as e:
        console.print(f"\n[red]✗ {e}[/red]")
        console.print("  Run: [bold]workmain slack setup[/bold]")
        return

    # Call auth.test
    try:
        client = SlackClient(token)
        info = client.test_connection()
    except SlackClientError as e:
        console.print(f"\n[red]✗ Token validation failed:[/red] {e}")
        console.print("  Your token may be revoked or incorrect.")
        console.print(
            "  Edit .env and replace SLACK_BOT_TOKEN, then run: "
            "[bold]workmain slack auth --reauth[/bold]"
        )
        return

    # Cache workspace name
    cfg["workspace_name"] = info["team"]
    save_slack_config(cfg)

    db = get_db()
    session = db.get_session()
    try:
        channel = _get_display_channel(session) or "(not set)"
    finally:
        session.close()

    console.print(f"\n[green]✓ Slack authenticated[/green]")
    console.print(f"  Workspace:       {info['team']}")
    console.print(f"  Bot user:        {info['user']}")
    console.print(f"  Channel:         {channel}")
    console.print(f"  Config saved to: ~/.workmain/integrations/slack/config.json")


# ---------------------------------------------------------------------------
# slack status
# ---------------------------------------------------------------------------

@slack.command("status")
def slack_status():
    """Show Slack auth state and recent post history."""
    cfg = load_slack_config()

    console.print("\n[bold cyan]WorkmAIn — Slack Status[/bold cyan]")
    console.print(Rule())

    # Auth state
    if is_authenticated():
        workspace = cfg.get("workspace_name", "(not cached — run workmain slack auth)")
        console.print(f"  Auth:            [green]✓ Token present[/green]")
        console.print(f"  Workspace:       {workspace}")
    else:
        console.print("  Auth:            [red]✗ SLACK_BOT_TOKEN not set[/red]")
        console.print("  Run: [bold]workmain slack setup[/bold]")

    db = get_db()
    session = db.get_session()
    try:
        channel = _get_display_channel(session)

        from workmain.database.repositories.system_state_repository import SystemStateRepository
        from workmain.database.repositories.client_repository import ClientRepository
        active_client_id = SystemStateRepository(session).get_int('active_client_id')
        if active_client_id:
            client = ClientRepository(session).get_by_id(active_client_id)
            client_name = client.name if client else "(unknown)"
            if channel:
                console.print(f"  Channel:         {channel} (Client: {client_name})")
            else:
                console.print(f"  Channel:         (not configured for {client_name})")
        else:
            console.print(f"  Channel:         {channel or '(not configured)'}")

        console.print()

        rows = (
            session.query(Report)
            .filter(Report.slack_message_ts.isnot(None))
            .order_by(Report.report_date.desc())
            .limit(5)
            .all()
        )

        if not rows:
            console.print("  [dim]No reports have been posted to Slack.[/dim]")
        else:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Date", style="cyan")
            table.add_column("Channel")
            table.add_column("Workspace")
            table.add_column("Timestamp (ts)")

            for r in rows:
                ts_display = (r.slack_message_ts or "")[:20]
                table.add_row(
                    str(r.report_date),
                    r.slack_channel or "",
                    r.slack_workspace_name or "",
                    ts_display,
                )
            console.print(table)
    finally:
        session.close()


# ---------------------------------------------------------------------------
# slack set subgroup
# ---------------------------------------------------------------------------

@slack.group("set")
def slack_set():
    """Configure Slack settings for the active client."""


@slack_set.command("channel")
@click.argument("channel")
def slack_set_channel(channel: str):
    """Set the Slack channel for the currently active client.

    Normalizes the channel name (adds # if absent).

    Sets the Slack channel for the currently active client.
    Use 'workmain clients set active' to switch clients.

    \b
    Examples:
      workmain slack set channel "#int-gmf-csirt"
      workmain slack set channel int-gmf-csirt
    """
    channel = _normalize_channel(channel)

    db = get_db()
    session = db.get_session()
    try:
        from workmain.database.repositories.system_state_repository import SystemStateRepository
        from workmain.database.repositories.client_repository import ClientRepository
        active_client_id = SystemStateRepository(session).get_int('active_client_id')
        if not active_client_id:
            console.print(
                "\n[red]✗ No active client set.[/red]"
                "\n  Run 'workmain clients set active <name>' first."
            )
            return

        client_repo = ClientRepository(session)
        client = client_repo.update(active_client_id, slack_channel=channel)
        console.print(
            f"\n[green]✓[/green] Slack channel for '[bold]{client.name}[/bold]' "
            f"set to '[bold]{channel}[/bold]'."
        )
    finally:
        session.close()


@slack_set.command("workspace")
def slack_set_workspace():
    """Show current workspace name and config file path (informational, no writes).

    Workspace configuration is managed via the Slack config file.
    To change the workspace, edit the "workspace_name" field in that file.

    \b
    Example:
      workmain slack set workspace
    """
    cfg = load_slack_config()
    workspace = cfg.get("workspace_name")
    config_path = Path.home() / ".workmain" / "integrations" / "slack" / "config.json"

    console.print()
    if workspace:
        console.print("Workspace configuration is managed via the Slack config file.")
        console.print()
        console.print(f"  Current workspace: {workspace}")
        console.print(f"  Config file:       {config_path}")
        console.print()
        console.print('  To change the workspace, edit the "workspace_name" field in that file.')
    else:
        console.print("[yellow]Workspace name not yet cached.[/yellow]")
        console.print(f"  Config file: {config_path}")
        console.print()
        console.print("  Run [bold]workmain slack auth[/bold] to authenticate and cache the workspace name.")
    console.print()


@slack_set.command("operator-user-id")
@click.argument("user_id")
def slack_set_operator_user_id(user_id: str):
    """Set your Slack user ID for inbound DM polling.

    The daemon uses this to find the DM channel where you send messages to
    the bot. Set it once — the channel ID is then cached automatically.

    Find your user ID: Slack → click your avatar → Profile →
    kebab menu (⋮) → Copy member ID. Starts with 'U'.

    \b
    Example:
      workmain slack set operator-user-id U0A1B2C3D4
    """
    from workmain.integrations.slack.auth import save_operator_user_id, get_operator_user_id
    user_id = user_id.strip()
    if not user_id.upper().startswith('U'):
        console.print()
        console.print("[yellow]⚠  Slack user IDs typically start with 'U' (e.g. U0A1B2C3D4).[/yellow]")
        console.print("  Find it: Slack → avatar → Profile → ⋮ → Copy member ID")
        console.print()
    save_operator_user_id(user_id)
    console.print()
    console.print(f"[green]✓[/green] Operator user ID set to [bold]{user_id}[/bold].")
    console.print("  The daemon poll loop will use this to find your DM channel with the bot.")
    console.print()


# ---------------------------------------------------------------------------
# slack setup
# ---------------------------------------------------------------------------

@slack.command("setup")
def slack_setup():
    """Interactive setup checklist for Slack integration."""
    console.print("\n[bold cyan]WorkmAIn — Slack Setup[/bold cyan]")
    console.print("─" * 46)

    token_present = is_authenticated()
    cfg = load_slack_config()
    workspace_name = cfg.get("workspace_name")
    bot_user = None
    token_valid = False
    api_error = None

    # Try live validation if token is present
    if token_present:
        try:
            token = get_token()
            client = SlackClient(token)
            info = client.test_connection()
            token_valid = True
            workspace_name = info["team"]
            bot_user = info["user"]
            # Cache the result
            cfg["workspace_name"] = workspace_name
            save_slack_config(cfg)
        except SlackClientError as e:
            token_valid = False
            api_error = str(e)

    # Resolve channel via DB
    db = get_db()
    session = db.get_session()
    try:
        channel = _get_display_channel(session)
    finally:
        session.close()

    if not token_present:
        # Nothing configured — show full instructions
        console.print("[dim][?][/dim] Step 1: Create Slack app")
        console.print("[dim][?][/dim] Step 2: Configure bot scopes")
        console.print("[dim][?][/dim] Step 3: Install to workspace")
        console.print("[red][✗][/red] Step 4: Add token to .env")
        console.print("[dim][ ][/dim] Step 5: Validate token          [dim](waiting on Step 4)[/dim]")
        console.print("[dim][ ][/dim] Step 6: Set default channel     [dim](waiting on Step 4)[/dim]")
        console.print("[dim][ ][/dim] Step 7: Invite bot to channel   [dim](waiting on Step 6)[/dim]")
        console.print()
        console.print("To complete Steps 1–4:")
        console.print("  1. Go to https://api.slack.com/apps")
        console.print("  2. Create New App → From scratch → name it WorkmAIn")
        console.print("  3. OAuth & Permissions → Bot Token Scopes → add:")
        console.print("       [bold]chat:write[/bold]    (post messages)")
        console.print("       [bold]auth:read[/bold]     (token validation)")
        console.print("  4. Click Install to Workspace → Allow")
        console.print("  5. Copy Bot User OAuth Token (starts with xoxb-)")
        console.print("  6. Add to .env:")
        console.print("       SLACK_BOT_TOKEN=xoxb-your-token-here")
        console.print()
        console.print("Run [bold]workmain slack setup[/bold] again after adding the token.")
        return

    # Token present
    console.print("[green][✓][/green] Steps 1–3: Slack app created and installed")
    console.print("[green][✓][/green] Step 4: Token found")

    if token_valid:
        console.print(
            f"[green][✓][/green] Step 5: Token valid — {workspace_name} (bot: {bot_user})"
        )
    else:
        console.print(f"[red][✗][/red] Step 5: Token validation failed: {api_error}")
        console.print()
        console.print("  Your token may be revoked, expired, or incorrectly copied.")
        console.print("  To replace it:")
        console.print("    1. Go to https://api.slack.com/apps → your app → OAuth & Permissions")
        console.print("    2. Reinstall app or copy the existing Bot User OAuth Token")
        console.print("    3. Edit .env and update SLACK_BOT_TOKEN")
        console.print("    4. Run: [bold]workmain slack auth --reauth[/bold]")
        console.print()
        console.print("Run [bold]workmain slack setup[/bold] again after updating the token.")
        return

    if not channel:
        console.print("[red][✗][/red] Step 6: Channel not configured for active client")
        console.print("[dim][ ][/dim] Step 7: Invite bot to channel   [dim](waiting on Step 6)[/dim]")
        console.print()
        console.print("To complete Step 6:")
        console.print("  [bold]workmain slack set channel <channel>[/bold]")
        console.print()
        console.print("Then invite the bot in Slack:")
        console.print("  [bold]/invite @WorkmAIn[/bold]")
        console.print("  (must be done in each channel you want to post to)")
        console.print()
        console.print("Run [bold]workmain slack setup[/bold] again to verify.")
    else:
        console.print(f"[green][✓][/green] Step 6: Channel: {channel}")
        console.print(f"[dim][?][/dim] Step 7: Bot invited to {channel}?")
        console.print(
            f"  If not yet done: [bold]/invite @WorkmAIn[/bold]  "
            f"(in Slack, in {channel})"
        )
        console.print()
        console.print(
            "Setup complete. Run [bold]workmain slack status[/bold] "
            "to see integration state."
        )
        console.print()
        console.print(
            "[dim]To replace your token: edit .env → update SLACK_BOT_TOKEN → "
            "run: workmain slack auth --reauth[/dim]"
        )


# ---------------------------------------------------------------------------
# slack post PERIOD
# ---------------------------------------------------------------------------

@slack.command("post")
@click.argument("period", type=click.Choice(["weekly", "daily", "monthly"]))
@click.option("-d", "--date", "date_str", default=None, metavar="YYYYMMDD",
              help="Anchor date for the weekly range (default: today).")
@click.option("--channel", default=None,
              help="Override the default channel for this post.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Show what would happen — no message sent, no DB record.")
@click.option("--force", is_flag=True, default=False,
              help="Post even if this date was already posted (REPOST).")
def slack_post(
    period: str,
    date_str: Optional[str],
    channel: Optional[str],
    dry_run: bool,
    force: bool,
):
    """Post a report period draft to Slack (PERIOD: weekly, daily, monthly).

    Generation and review are handled by the same interactive [v/e/c/s]
    menu the EOD weekly report step uses (Item #61 Gate 4) — this command
    drives that flow, then offers to post the confirmed/corrected result
    to Slack as a separate step. A [s]kip (or any non-confirmed exit)
    posts nothing, matching prior default-to-no-post behavior.

    \b
    Examples:
      workmain slack post weekly
      workmain slack post weekly --dry-run
      workmain slack post weekly -d 20260327 --channel #reports
    """
    if period != "weekly":
        raise NotImplementedError(
            f"slack post {period} is not yet implemented."
        )

    # -----------------------------------------------------------------------
    # Channel resolution (Option B: dedicated mini-session before generation)
    # -----------------------------------------------------------------------
    if channel:
        target_channel = _normalize_channel(channel)
    else:
        db = get_db()
        _ch_session = db.get_session()
        try:
            target_channel = _resolve_slack_channel(_ch_session)
        finally:
            _ch_session.close()

        if not target_channel:
            console.print(
                "\n[red]✗ No Slack channel configured.[/red]"
            )
            console.print("  Run:")
            console.print("    [bold]workmain slack set channel <channel>[/bold]")
            console.print("  or set a default in ~/.workmain/integrations/slack/config.json")
            return

    # -----------------------------------------------------------------------
    # Auth check
    # -----------------------------------------------------------------------
    try:
        token = get_token()
    except SlackAuthError as e:
        console.print(f"\n[red]✗ {e}[/red]")
        console.print("  Run: [bold]workmain slack setup[/bold]")
        return

    # -----------------------------------------------------------------------
    # Date range
    # -----------------------------------------------------------------------
    anchor = _parse_date_arg(date_str)
    monday, _ = get_draft_date_range(anchor)
    end_str = anchor.strftime("%Y-%m-%d")
    monday_display = format_date_display(monday)
    anchor_display = format_date_display(anchor)

    if dry_run:
        console.print(
            f"\n[yellow][DRY RUN][/yellow] Would generate and review the "
            f"weekly_client report for {end_str}, then prompt to post to "
            f"{target_channel}."
        )
        console.print("[yellow][DRY RUN][/yellow] No message sent. No database record created.")
        return

    # -----------------------------------------------------------------------
    # Generate-or-reuse + interactive [v/e/c/s] review (Item #61 Gate 4,
    # Design Rule 9) — same shared runner the EOD weekly step uses.
    # -----------------------------------------------------------------------
    from workmain.workflows.eod_workflow import _run_report_review_step
    _run_report_review_step(
        dry_run=False,
        target_date=anchor,
        report_type='weekly_client',
        label='Weekly',
        require_active_client=True,
        generation_error_fatal=False,
    )

    # -----------------------------------------------------------------------
    # Delivery — separate step after the review runner completes (Design
    # Rule 10). Fires only when review ended confirmed/corrected; updates
    # the same row the review produced — no second upsert, no second row.
    # -----------------------------------------------------------------------
    db = get_db()
    session = db.get_session()
    try:
        from workmain.database.repositories.reports_repo import get_reports_repository
        repo = get_reports_repository(session)
        reports = repo.list_reports(
            report_type='weekly_client',
            start_date=anchor,
            end_date=anchor,
            limit=1,
        )
        report = reports[0] if reports else None

        if report is None or report.status not in ('confirmed', 'corrected'):
            console.print(
                "\n[yellow]No confirmed/corrected weekly report for "
                f"{end_str} — no message posted.[/yellow]"
            )
            return

        cfg = load_slack_config()
        workspace_name = cfg.get("workspace_name", "")

        if already_posted(session, anchor) and not force:
            console.print(
                f"\n[yellow]⚠ Weekly draft for {end_str} was already posted "
                f"to {target_channel}.[/yellow]"
            )
            console.print("  Use [bold]--force[/bold] to post again.")
            return

        post_choice = click.prompt(
            f"\nPost Weekly to {target_channel}? [y]es / [n]o",
            default="n",
        )
        if post_choice.lower() != "y":
            console.print("Cancelled. No message posted.")
            return

        report_content = report.corrected_content or report.content
        draft_header = f"*[DRAFT — For Review]* Week of {monday_display}–{anchor_display}\n\n"
        slack_content = draft_header + format_for_slack(report_content)

        try:
            client = SlackClient(token)
            message_ts = client.post_message(target_channel, slack_content)
        except SlackClientError as e:
            console.print(f"\n[red]✗ Slack post failed:[/red] {e}")
            return

        report.slack_message_ts = message_ts
        report.slack_channel = target_channel
        report.slack_workspace_name = workspace_name
        session.commit()

        console.print(f"\n[green]✓ Posted to {target_channel}[/green]")
        console.print(f"  Workspace:  {workspace_name}")
        console.print(f"  Period:     {monday_display} – {anchor_display}")
        console.print(f"  Timestamp:  {message_ts}")
        console.print("  Report record updated (reports table)")
    finally:
        session.close()
