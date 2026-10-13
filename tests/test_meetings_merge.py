"""
CLI-level coverage for 'workmain meetings merge': the notes the merge moved
are committed before the "Delete old meeting?" prompt, so cancelling that
prompt keeps the merge (DEVELOPMENT_STANDARDS §4.1, the owner commits before
it waits).
"""

from datetime import datetime
from unittest.mock import patch

import click
from click.testing import CliRunner

from workmain.cli.commands.meetings import meetings
from workmain.database.models import Meeting, Note
from workmain.services import notes_service


def _meeting(session, title: str) -> Meeting:
    meeting = Meeting(
        title=title,
        start_time=datetime(2099, 6, 1, 9, 0),
        end_time=datetime(2099, 6, 1, 9, 30),
        is_recurring=False,
    )
    session.add(meeting)
    session.commit()
    session.refresh(meeting)
    return meeting


def test_merge_keeps_moved_notes_when_the_delete_prompt_is_cancelled(db_session):
    old = _meeting(db_session, "Sentinel Merge Old 2099-96")
    new = _meeting(db_session, "Sentinel Merge New 2099-96")
    note = notes_service.create_note(
        db_session,
        content="Sentinel merge note 2099-96",
        tags=['internal-only'],
        source='meeting',
        meeting_id=old.id,
    )
    db_session.commit()
    note_id, old_id, new_id = note.id, old.id, new.id

    # Continue? is answered yes; Ctrl-C at "Delete old meeting?" raises Abort
    with patch('click.confirm', side_effect=[True, click.Abort()]):
        result = CliRunner().invoke(meetings, ["merge", str(old_id), str(new_id)])

    assert result.exit_code != 0
    db_session.expire_all()
    assert db_session.get(Note, note_id).meeting_id == new_id
