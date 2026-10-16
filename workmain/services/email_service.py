"""
Service layer for email drafts: builds a draft from the newest saved report
for a template and saves it to staging/email/. Shared by the email and
reports CLI groups and the EOD workflow. Functions take a session and return
frozen dataclasses; none opens, commits or rolls back a session.
"""

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from workmain.database.repositories.email_repository import get_email_repository
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.services.exceptions import NoReportFoundError

# Project root: workmain/services/email_service.py -> 3 parents up
_PROJECT_ROOT = Path(__file__).parent.parent.parent
REPORTS_DIR = _PROJECT_ROOT / "staging" / "reports"
EMAIL_DIR = _PROJECT_ROOT / "staging" / "email"


@dataclass(frozen=True)
class EmailDraft:
    """An email draft built from a saved report."""

    template: str
    subject: str
    to: Tuple[str, ...]
    cc: Tuple[str, ...]
    report_date: date
    content: str


@dataclass(frozen=True)
class SavedDraft:
    """An email draft and the file it was saved to."""

    draft: EmailDraft
    path: Path


def _find_latest_report(template: str) -> Optional[Path]:
    """Return the most recently modified report file for the given template."""
    matches = list(REPORTS_DIR.glob(f"{template}_*.md"))
    if not matches:
        return None
    return max(matches, key=lambda p: p.stat().st_mtime)


def _extract_report_date(report_path: Path) -> date:
    """Extract date from report filename (<template>_<YYYY-MM-DD>.md)."""
    m = re.search(r'_(\d{4}-\d{2}-\d{2})\.', report_path.name)
    if m:
        return date.fromisoformat(m.group(1))
    return date.today()


def _build_subject(template: str, report_date: date) -> str:
    """Build email subject line from template name and report date."""
    name = template.lower()
    if 'daily' in name:
        return f"Daily Report — {report_date.strftime('%d %b %Y')}"
    elif 'weekly' in name:
        week_start = report_date - timedelta(days=report_date.weekday())
        return f"Weekly Report — Week of {week_start.strftime('%d %b %Y')}"
    elif 'monthly' in name:
        return f"Monthly Report — {report_date.strftime('%B %Y')}"
    else:
        title = template.replace('_', ' ').title()
        return f"{title} — {report_date.strftime('%d %b %Y')}"


def _build_draft_content(
    subject: str,
    to_list: Tuple[str, ...],
    cc_list: Tuple[str, ...],
    body: str,
    draft_date: datetime,
) -> str:
    """Build draft file content in standard format."""
    lines = []
    if to_list:
        lines.append(f"To: {', '.join(to_list)}")
    if cc_list:
        lines.append(f"CC: {', '.join(cc_list)}")
    lines.append(f"Subject: {subject}")
    lines.append(f"Date: {draft_date.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(body)
    return "\n".join(lines)


def _draft_recipients(
    session: Session,
    template: str,
) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    """Look up recipients for a template using client-aware resolution.

    Merges global recipients (NULL client_id) with client-scoped recipients
    for the active client. Deduplicates by email address (client-scoped role
    wins on conflict).

    Args:
        session: Session the lookup runs on.
        template: Report template name.

    Returns:
        (to, cc) tuples of email addresses.
    """
    active_client_id = SystemStateRepository(session).get_int('active_client_id')
    assignments = get_email_repository(session).list_for_client(template, active_client_id)
    seen: dict[str, str] = {}  # email -> role
    for a in assignments:
        email = a.recipient.email
        if email not in seen:
            seen[email] = a.recipient_type
        elif a.client_id is not None:
            # Client-scoped record overrides global
            seen[email] = a.recipient_type
    to_list = tuple(e for e, r in seen.items() if r == 'to')
    cc_list = tuple(e for e, r in seen.items() if r == 'cc')
    return to_list, cc_list


def build_draft(session: Session, template: str) -> EmailDraft:
    """Build an email draft from the newest saved report for a template.

    Args:
        session: Session the recipient lookup runs on.
        template: Report template name.

    Returns:
        The draft. ``to`` and ``cc`` are empty when no recipients are assigned.

    Raises:
        NoReportFoundError: No saved report matches the template.
    """
    report_path = _find_latest_report(template)
    if report_path is None:
        raise NoReportFoundError(template)

    report_date = _extract_report_date(report_path)
    body = report_path.read_text(encoding='utf-8')
    subject = _build_subject(template, report_date)
    to_list, cc_list = _draft_recipients(session, template)
    content = _build_draft_content(subject, to_list, cc_list, body, datetime.now())
    return EmailDraft(
        template=template,
        subject=subject,
        to=to_list,
        cc=cc_list,
        report_date=report_date,
        content=content,
    )


def save_draft(session: Session, template: str) -> SavedDraft:
    """Build an email draft and save it to the staging email directory.

    Args:
        session: Session the recipient lookup runs on.
        template: Report template name.

    Returns:
        The draft and the path it was written to.

    Raises:
        NoReportFoundError: No saved report matches the template. Nothing is
            written.
    """
    draft = build_draft(session, template)
    EMAIL_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{template}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    draft_path = EMAIL_DIR / filename
    draft_path.write_text(draft.content, encoding='utf-8')
    draft_path.chmod(0o644)
    return SavedDraft(draft=draft, path=draft_path)
