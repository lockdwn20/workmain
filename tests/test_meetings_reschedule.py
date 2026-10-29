"""
CLI-level coverage for 'workmain meetings reschedule': the new start time and
each linked time entry the user approved are committed before the next
prompt, so cancelling a later prompt keeps what was already done
(docs/standards/4-database.md §4.1, the owner commits before it waits).
"""

from datetime import date, datetime, time
from unittest.mock import patch

import click
from click.testing import CliRunner

from workmain.cli.commands.meetings import meetings
from workmain.database.models import Meeting, TimeEntry
from workmain.services import notes_service, time_entry_service


def test_reschedule_keeps_the_approved_updates_when_a_later_prompt_is_cancelled(db_session):
    meeting = Meeting(
        title="Sentinel Reschedule 2099-96",
        start_time=datetime(2099, 6, 1, 9, 0),
        end_time=datetime(2099, 6, 1, 11, 0),
        is_recurring=False,
    )
    db_session.add(meeting)
    db_session.commit()
    entry_ids = []
    for index in range(2):
        note = notes_service.create_note(
            db_session,
            content=f"Sentinel reschedule entry {index} 2099-96",
            tags=['internal-only'],
            source='meeting',
            meeting_id=meeting.id,
        )
        entry = time_entry_service.create_paired_time_entry(
            db_session,
            note,
            duration_hours=0.5,
            entry_date=date(2099, 6, 1),
            entry_time=time(9, 0),
        )
        entry_ids.append(entry.id)
    db_session.commit()
    meeting_id = meeting.id

    # The first linked entry is updated; Ctrl-C at the second prompt raises Abort
    with patch('click.confirm', side_effect=[True, click.Abort()]):
        result = CliRunner().invoke(
            meetings, ["reschedule", str(meeting_id), "--start", "10:00"]
        )

    # The command reports the abort and exits 0; its scope has rolled back
    assert "✗ Error" in result.output
    db_session.expire_all()
    assert db_session.get(Meeting, meeting_id).start_time.time() == time(10, 0)
    times = [db_session.get(TimeEntry, eid).entry_time for eid in entry_ids]
    assert sorted(times) == [time(9, 0), time(10, 0)]
