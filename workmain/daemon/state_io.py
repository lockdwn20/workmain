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


def write_json_atomic(path, payload, mode: int = 0o600) -> None:
    """Write payload as JSON to path atomically.

    Writes a sibling temp file, flushes, fsyncs, sets the mode, then
    os.replace()s it into place so a crash or full disk mid-write can never
    truncate the live file. Owns parent-directory creation (mode 0o700) so
    callers do not.
    """
    path = Path(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    with open(tmp, 'w') as f:
        json.dump(payload, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.chmod(tmp, mode)
    os.replace(tmp, path)


def write_last_inspection(observations: list, summary: str, target_date: date) -> None:
    """Write inspection results to the daemon state file for status display."""
    payload = {
        'run_at': datetime.now().isoformat(timespec='seconds'),
        'target_date': str(target_date),
        'observations': [
            {'type': o.type.value, 'message': o.message, 'acknowledged': o.acknowledged}
            for o in observations
        ],
        'summary': summary,
    }
    write_json_atomic(daemon_state_path('last_inspection.json'), payload)


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
