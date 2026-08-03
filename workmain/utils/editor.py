"""
Shared $EDITOR helper for report correction UX — extracted from
reports.py:_edit_in_editor and eod_workflow.py:_eod_edit_in_editor (Item #61
Gate 2, Design Rule 3). slack.py's own copy is retired in Gate 4 once
slack_post() is rewritten onto the shared review runner.

Failure/output rendering is preserved per caller via the report_fn
callback, since callers differ in their console primitives — reports.py
uses Rich console.print with markup, eod_workflow.py uses plain print()
(it deliberately does not import click/rich).
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Optional


def edit_in_editor(seed_text: str, report_fn: Callable[[str], None]) -> Optional[str]:
    """Open $EDITOR pre-populated with seed_text; return the edited text.

    Args:
        seed_text: Text to pre-populate in the editor.
        report_fn: Callback invoked with a human-readable message when
            $EDITOR is unset or the editor process fails. Callers own how
            the message is rendered (Rich markup, plain print, etc.) —
            this function passes the bare message with no icon/color.

    Returns:
        Edited string, or None if $EDITOR is unset or the editor call failed.
    """
    editor = os.environ.get('EDITOR', '').strip()
    if not editor:
        report_fn("$EDITOR is not set. Export EDITOR=vim (or nano, etc.) and retry.")
        return None

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            tmp_path = f.name
            f.write(seed_text)
        subprocess.run([editor, tmp_path], check=True)
        return Path(tmp_path).read_text()
    except Exception as e:
        report_fn(f"Editor error: {e}")
        return None
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)
