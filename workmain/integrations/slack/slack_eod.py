"""
WorkmAIn Slack EOD Surface
Slack EOD Surface v1.0
20260611

Slack I/O surface for the T1 morning briefing and T5 EOD conversational
workflow. Plain-text I/O in Sprint 2. Block Kit UX upgrade in Sprint 3.

Version History:
- v1.0: Phase 13 Sprint 2 Gate 5 — T1 morning briefing builder stub;
        T5 EOD conversational flow added in Gate 6
"""

from __future__ import annotations


def build_morning_briefing(meetings: list, tasks: list, unresolved_count: int) -> str:
    """Build the T1 morning briefing plain-text string.

    Args:
        meetings:          Non-cancelled Meeting objects for today, sorted by
                           start_time ascending.
        tasks:             Active TaskStatus objects (all statuses == 'active').
        unresolved_count:  Count of unacknowledged daemon observations from
                           yesterday's last_inspection.json. 0 means omit section.

    Returns:
        Plain-text morning briefing suitable for a Slack DM.
    """
    lines = ["☀ Good morning. Here's your day:"]

    # Meetings section — always shown; message varies when empty
    lines.append("")
    lines.append("📅 Meetings today:")
    if meetings:
        for m in meetings:
            start = m.start_time.strftime('%H:%M')
            duration_min = int(round(m.duration_hours * 60))
            lines.append(f"• {start} — {m.title} ({duration_min} min)")
    else:
        lines.append("No meetings scheduled today.")

    # Tasks section — omitted entirely when empty
    if tasks:
        lines.append("")
        lines.append("📋 Carry-forward tasks:")
        for task in tasks:
            content = task.note.content if task.note else str(task.id)
            preview = content[:120] + ("…" if len(content) > 120 else "")
            lines.append(f"• {preview}")

    # Unresolved observations — omitted when count is zero
    if unresolved_count:
        plural = "s" if unresolved_count != 1 else ""
        lines.append("")
        lines.append(
            f"Yesterday's unresolved items: {unresolved_count} flagged "
            f"observation{plural} (run workmain eod to review)"
        )

    return "\n".join(lines)
