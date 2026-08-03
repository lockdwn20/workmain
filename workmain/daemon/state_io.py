"""
Shared read/write primitives for daemon state files under
WORKMAIN_STATE_DIR/daemon/. Consolidates the previously-duplicated
last_inspection.json writers in daemon.py and eod_workflow.py (Item #60).
"""

import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Optional


def daemon_state_path(filename: str) -> Path:
    """Return the path for a daemon state file under WORKMAIN_STATE_DIR/daemon/."""
    state_dir = Path(os.environ.get('WORKMAIN_STATE_DIR', '~/.workmain')).expanduser()
    return state_dir / 'daemon' / filename


def write_last_inspection(observations: list, summary: str, target_date: date) -> None:
    """Write inspection results to the daemon state file for status display."""
    path = daemon_state_path('last_inspection.json')
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    payload = {
        'run_at': datetime.now().isoformat(timespec='seconds'),
        'target_date': str(target_date),
        'observations': [
            {'type': o.type.value, 'message': o.message, 'acknowledged': o.acknowledged}
            for o in observations
        ],
        'summary': summary,
    }
    path.write_text(json.dumps(payload, indent=2))


def read_last_inspection() -> Optional[dict]:
    """Return the last_inspection.json payload, or None if absent/unreadable."""
    path = daemon_state_path('last_inspection.json')
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def matches_target_date(payload: dict, expected_date: date) -> bool:
    """True if payload's recorded target_date matches expected_date."""
    return payload.get('target_date') == str(expected_date)
