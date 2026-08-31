"""Self-invocation of the ``workmain`` entry point as a subprocess.

The EOD workflow and ``reports resend`` shell out to the ``workmain`` binary
rather than call internal APIs. Under systemd the venv is not activated, so
the bare name does not resolve, and a child that hangs on the network or an
AI provider blocks the daemon thread with no bound. This module owns the one
hardened way to make that call: an absolute binary path, a required per-call
timeout, optional output capture, and a result object that reports a timeout
or a non-zero exit without raising.

It is not a general subprocess facility. ``$EDITOR`` and ``wsl-notify-send``
callers stay where they are — a timeout on ``$EDITOR`` would be a defect,
not a fix — and a later caller wanting to run some other binary does not
extend this module.

Timeout constants live here, not with a caller, because the runner has more
than one caller. Each bound is per call, not per step: a step issuing N
calls is bounded at N times its value. See
``docs/dev/specs/EOD_SUBPROCESS_HARDENING_SPEC.md`` §3–§4.
"""

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

TIMEOUT_LOCAL = 120
"""Local database read and render; nothing here touches the network."""

TIMEOUT_NETWORK = 300
"""One integration round trip — Clockify, Drive, Slack, email staging."""

TIMEOUT_AI = 1800
"""A chosen ceiling, not a derived one. ``config/ai_settings.json`` carries a
``timeout_seconds`` key but nothing reads it, and the Claude/Gemini clients
are constructed with no per-call timeout, so there is no real number to size
against. This bounds the daemon thread and nothing more; it drops once a
provider honours a per-call timeout."""

TIMEOUT_INTERACTIVE = 1800
"""Bounds an abandoned terminal, not a human's thinking time."""


def resolve_workmain_bin() -> str:
    """Return the absolute path to the ``workmain`` entry-point script.

    When the daemon runs as a systemd service the venv is not activated, so
    ``workmain`` is not on ``PATH``. ``sys.executable`` is the venv Python,
    so the script lives in the same ``bin/`` directory. Falls back to the
    bare name when that file is not present (e.g. an editable install run a
    different way).
    """
    candidate = Path(sys.executable).parent / "workmain"
    return str(candidate) if candidate.is_file() else "workmain"


@dataclass
class WorkmainRun:
    """Outcome of a :func:`run_workmain` call.

    ``returncode`` is ``None`` only when ``timed_out`` is ``True``.
    ``stdout`` / ``stderr`` are ``''`` unless the call captured output.
    """

    returncode: Optional[int]
    stdout: str = ''
    stderr: str = ''
    timed_out: bool = False
    timeout: Optional[float] = None

    @property
    def ok(self) -> bool:
        """True when the child exited zero and did not time out."""
        return not self.timed_out and self.returncode == 0

    def failure_message(self, label: str) -> str:
        """One-line ``FAILED`` message for ``label``, naming the cause.

        Owns the wording so a step's failure message reads the same wherever
        it came from (spec DR8).
        """
        if self.timed_out:
            return f"{label} timed out after {self.timeout:g}s"
        detail = self.stderr.strip()
        if detail:
            return f"{label} failed (exit code {self.returncode}): {detail}"
        return f"{label} failed (exit code {self.returncode})"


def _as_text(value) -> str:
    """Coerce a captured stream to ``str`` — ``TimeoutExpired`` may carry bytes."""
    if value is None:
        return ''
    if isinstance(value, bytes):
        return value.decode(errors='replace')
    return value


def run_workmain(args: Sequence[str], *, timeout: float, capture: bool = True) -> WorkmainRun:
    """Invoke ``workmain <args>`` as a subprocess.

    Args:
        args: Arguments after the binary, e.g. ``['clockify', 'sync', 'push']``.
        timeout: Per-call timeout in seconds. Keyword-only and required —
            there is no default (spec DR3).
        capture: When ``True`` (default), capture stdout/stderr as text.
            When ``False``, the child inherits the parent's stdio so a
            prompt reaches the operator.

    Returns:
        A :class:`WorkmainRun`. A timeout sets ``timed_out=True`` and
        ``returncode=None``; a non-zero exit is reported on ``returncode``.
        Neither raises (spec DR2). Anything else — a missing binary, an
        ``OSError`` — propagates unchanged.
    """
    cmd = [resolve_workmain_bin(), *args]
    kwargs = {'capture_output': True, 'text': True} if capture else {}
    try:
        result = subprocess.run(cmd, timeout=timeout, **kwargs)
    except subprocess.TimeoutExpired as e:
        return WorkmainRun(
            returncode=None,
            stdout=_as_text(e.stdout),
            stderr=_as_text(e.stderr),
            timed_out=True,
            timeout=timeout,
        )
    return WorkmainRun(
        returncode=result.returncode,
        stdout=_as_text(result.stdout) if capture else '',
        stderr=_as_text(result.stderr) if capture else '',
    )
