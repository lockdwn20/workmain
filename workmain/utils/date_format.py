"""
Plain module-level date display formatting — extracted from
workmain/cli/commands/slack.py's private _format_date_display(), which had
no CLI-specific dependency and gained a second caller
(slack_eod.py's build_morning_briefing()) outside that module. Same
category of fix as workmain/utils/time_parser.py's extraction in
Operations_Config_Correction_Sprint Gate 1 §1.0 — a formatting helper
trapped in the wrong layer, same rationale, same location.
"""

from datetime import date


def format_date_display(d: date) -> str:
    """Format date as 'Mon 09 Mar 2026'."""
    return d.strftime("%a %d %b %Y")
