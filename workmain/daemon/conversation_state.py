"""
Single owner of Slack DM conversational state: pending confirmation
actions (PendingAction) and in-progress T5 EOD sessions (SlackEodSession).

ConversationStore holds both record types in memory under one lock —
memory is authoritative because a session's threading.Event/Thread cannot
be serialized and _abort_session() depends on their identity — and mirrors
the whole state to one JSON file on every mutation. The file is read once,
at daemon start.
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from workmain.daemon.state_io import daemon_state_path, write_json_atomic

logger = logging.getLogger(__name__)

# How long a conversational offer stays meaningful. A module constant, not a
# tunable: above ~30 min an affirmative no longer plausibly refers to the
# offer; below ~5 min it expires while you make coffee. Same category as the
# 24 h session window and the 60 s socket-dedupe window.
PENDING_ACTION_TTL = timedelta(minutes=15)
# Session staleness — the inline 24 h literal from slack_eod.py, named.
EOD_SESSION_TTL = timedelta(hours=24)

_STATE_FILENAME = 'conversation_state.json'
_LEGACY_SESSION_FILENAME = 'eod_session.json'


# ---------------------------------------------------------------------------
# Pending confirmation action
# ---------------------------------------------------------------------------

@dataclass
class PendingAction:
    """A confirmation offer awaiting a yes/no. Correlated to its Block Kit
    button click by action_id (a uuid), never by comparing payloads."""

    user_id: str
    action: dict
    action_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            'user_id': self.user_id,
            'action': self.action,
            'action_id': self.action_id,
            'created_at': self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PendingAction':
        return cls(
            user_id=data['user_id'],
            action=data['action'],
            action_id=data['action_id'],
            created_at=datetime.fromisoformat(data['created_at']),
        )


# ---------------------------------------------------------------------------
# T5 EOD session state (moved from slack_eod.py — behaviour unchanged)
# ---------------------------------------------------------------------------

@dataclass
class SlackEodSession:
    """In-memory state for a single T5 EOD session.

    One session per user_id. Persisted by ConversationStore after every
    mutation so daemon restarts can offer resume. Sessions older than
    EOD_SESSION_TTL are dropped on load.
    """
    user_id: str
    channel_id: str
    target_date: date
    steps: list
    current_step_idx: int
    paused: bool
    completed: list
    skipped: list
    skip_targets: list = field(default_factory=list)  # original --skip
        # argument value, captured at construction. Always [] from the Slack
        # surface today — kept so the round-trip is correct if that changes.
    pending_action: Optional[dict] = None
    started_at: datetime = field(default_factory=datetime.now)

    # Runtime-only — not persisted, not compared/repr'd. Set by
    # SlackEodManager when a long-running step is dispatched to a thread.
    _step_thread: Optional[threading.Thread] = field(default=None, repr=False, compare=False)
    _cancel_event: Optional[threading.Event] = field(default=None, repr=False, compare=False)

    def to_dict(self) -> dict:
        return {
            'user_id': self.user_id,
            'channel_id': self.channel_id,
            'target_date': str(self.target_date),
            'current_step_idx': self.current_step_idx,
            'completed': self.completed,
            'skipped': self.skipped,
            'started_at': self.started_at.isoformat(),
            'paused': self.paused,
            'pending_action': self.pending_action,
            'skip_targets': self.skip_targets,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SlackEodSession':
        """Rebuild a session from its persisted dict. steps is rebuilt from
        get_step_sequence() — its entries hold live runner callables and are
        never serialized. The import is deferred so workmain/daemon/ gains no
        module-level edge on workmain/workflows/."""
        from workmain.workflows.eod_workflow import get_step_sequence

        target_date = date.fromisoformat(data['target_date'])
        skip_targets = data.get('skip_targets', [])
        return cls(
            user_id=data['user_id'],
            channel_id=data['channel_id'],
            target_date=target_date,
            steps=get_step_sequence(weekday=target_date.weekday(), skip=skip_targets),
            current_step_idx=data['current_step_idx'],
            paused=data.get('paused', False),
            completed=list(data['completed']),
            skipped=list(data['skipped']),
            skip_targets=skip_targets,
            pending_action=data.get('pending_action'),
            started_at=datetime.fromisoformat(data['started_at']),
        )


# ---------------------------------------------------------------------------
# The store
# ---------------------------------------------------------------------------

class ConversationStore:
    """Owns every pending action and EOD session, in memory and on disk.

    Every mutating method holds one RLock for the whole operation and writes
    the file through before returning. The lock is held across a store
    method and nothing else — never across an Ollama call, a Slack post or
    an EOD step.
    """

    def __init__(self, path=None) -> None:
        self._path = Path(path) if path is not None else daemon_state_path(_STATE_FILENAME)
        self._lock = threading.RLock()
        self._pending: dict = {}          # user_id -> PendingAction
        self._sessions: dict = {}         # user_id -> SlackEodSession
        self._restored: list = []         # sessions brought back by load()

    # -- lifecycle ------------------------------------------------------

    def load(self) -> None:
        """Read the file once. Prune both TTLs, write the pruned state back,
        and remember which sessions were restored. A corrupt or absent file
        loads as empty state. A legacy eod_session.json is unlinked."""
        with self._lock:
            legacy = self._path.parent / _LEGACY_SESSION_FILENAME
            if legacy.exists():
                legacy.unlink()
                logger.info("Removed legacy %s", _LEGACY_SESSION_FILENAME)

            if not self._path.exists():
                return
            try:
                data = json.loads(self._path.read_text())
            except (json.JSONDecodeError, OSError, ValueError):
                logger.warning("%s unreadable — starting with empty conversation state", self._path)
                return

            now = datetime.now()
            for raw in data.get('pending', []):
                try:
                    pa = PendingAction.from_dict(raw)
                except (KeyError, ValueError, TypeError):
                    continue
                if now - pa.created_at <= PENDING_ACTION_TTL:
                    self._pending[pa.user_id] = pa

            for raw in data.get('sessions', []):
                try:
                    s = SlackEodSession.from_dict(raw)
                except (KeyError, ValueError, TypeError, json.JSONDecodeError):
                    continue
                if now - s.started_at <= EOD_SESSION_TTL:
                    self._sessions[s.user_id] = s

            self._restored = list(self._sessions.values())
            self._write()

    def restored_sessions(self) -> list:
        """Sessions load() brought back from disk — the only way the resume
        path can find a session whose user_id it does not yet know."""
        with self._lock:
            return list(self._restored)

    # -- pending actions ----------------------------------------------

    def put_pending(self, user_id: str, action: dict) -> PendingAction:
        """Record a new confirmation offer for user_id, replacing any prior
        one. Returns the record so the caller can put its action_id in the
        Block Kit button."""
        with self._lock:
            pa = PendingAction(user_id=user_id, action=action)
            self._pending[user_id] = pa
            self._write()
            return pa

    def take_pending(self, user_id: str, action_id: Optional[str] = None) -> Optional[dict]:
        """Return the user's pending action dict once, or None.

        Returned only if it exists, has not outlived PENDING_ACTION_TTL, and
        (when action_id is given) its id matches. A mismatched id leaves the
        record in place. An expired record is dropped and None returned.
        """
        with self._lock:
            pa = self._pending.get(user_id)
            if pa is None:
                return None
            if datetime.now() - pa.created_at > PENDING_ACTION_TTL:
                del self._pending[user_id]
                self._write()
                return None
            if action_id is not None and action_id != pa.action_id:
                return None
            del self._pending[user_id]
            self._write()
            return pa.action

    # -- EOD sessions -----------------------------------------------

    def get_session(self, user_id: str) -> Optional[SlackEodSession]:
        with self._lock:
            return self._sessions.get(user_id)

    def has_session(self, user_id: str) -> bool:
        with self._lock:
            return user_id in self._sessions

    def has_any_session(self) -> bool:
        with self._lock:
            return bool(self._sessions)

    def save_session(self, session: SlackEodSession) -> None:
        """Upsert: register a session the store has not seen, persist one it
        has. Registering and persisting are the same call."""
        with self._lock:
            self._sessions[session.user_id] = session
            self._write()

    def set_session_pending(self, user_id: str, action: dict) -> None:
        """Set session.pending_action through the store so it is persisted."""
        with self._lock:
            session = self._sessions.get(user_id)
            if session is None:
                return
            session.pending_action = action
            self._write()

    def take_session_pending(self, user_id: str) -> Optional[dict]:
        """Read-and-clear session.pending_action atomically, persisting the
        clear. Returns the action to the winning caller only."""
        with self._lock:
            session = self._sessions.get(user_id)
            if session is None or session.pending_action is None:
                return None
            action = session.pending_action
            session.pending_action = None
            self._write()
            return action

    def discard_session(self, user_id: str) -> None:
        """Remove an EOD session from memory and the file together."""
        with self._lock:
            if self._sessions.pop(user_id, None) is not None:
                self._write()

    # -- persistence ------------------------------------------------

    def _write(self) -> None:
        """Mirror the whole state to the file. Caller holds the lock."""
        payload = {
            'pending': [pa.to_dict() for pa in self._pending.values()],
            'sessions': [s.to_dict() for s in self._sessions.values()],
        }
        write_json_atomic(self._path, payload)
