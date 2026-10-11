"""
Capture the exact prompts WorkmAIn would send for a set of report dates, and
freeze them to JSON fixtures that run_baseline.py replays outside the app.

This is the ONLY baseline step that touches WorkmAIn or the database, and it
does so read-only:

  * The session's transaction is declared READ ONLY before any query, so
    PostgreSQL itself rejects any INSERT/UPDATE/DELETE that could slip through.
  * The session is rolled back and closed at the end, whatever happens.
  * No report is generated or saved, no meeting is condensed, no provider is
    called. Prompts are built with the same builders production uses:
      - reports:      PromptBuilder.build_prompt()   (as generate_report does)
      - condensation: NoteCondenser.select_condensation_notes() +
                      NoteCondenser.build_condensation_request()

Output holds real work content and can name the client. Keep it under
staging/baseline/ (gitignored). Never commit or paste it.

Run from the repository root, in the WorkmAIn virtualenv:

    python scripts/baseline/capture_baseline_prompts.py \
        --daily 2026-10-07,2026-10-08,2026-10-09 \
        --weekly 2026-09-25,2026-10-02,2026-10-09

Condensation fixtures default to the meetings on the --daily dates
(override with --condense, or pass --condense none to skip).
"""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import text

from workmain.ai.note_condenser import NoteCondenser
from workmain.ai.prompt_builder import PromptBuilder
from workmain.ai.report_generator import ReportGenerator
from workmain.cli.commands.reports import get_client_filter
from workmain.database.connection import get_db
from workmain.database.repositories.meetings_repo import MeetingsRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.templates_engine import get_template_loader

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_VERSION = 1


def _dates(value: Optional[str]) -> List[date]:
    if not value or value.strip().lower() == 'none':
        return []
    return [date.fromisoformat(v.strip()) for v in value.split(',') if v.strip()]


def _sha(text_: str) -> str:
    return hashlib.sha256(text_.encode('utf-8')).hexdigest()[:16]


def _read_json(path: Path) -> dict:
    with open(path, encoding='utf-8') as handle:
        return json.load(handle)


def _git_head() -> Optional[str]:
    try:
        out = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'], cwd=REPO_ROOT,
            capture_output=True, text=True, timeout=5,
        )
        branch = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=REPO_ROOT,
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0:
            return f"{branch.stdout.strip()}@{out.stdout.strip()}"
    except Exception:
        pass
    return None


def _user_full_name() -> str:
    # _get_user_full_name never touches self; call it the way production resolves it.
    try:
        return ReportGenerator._get_user_full_name(None)
    except Exception:
        return "User Name"


def _subject_line(template: dict, report_date: date, user_full_name: str) -> Optional[str]:
    """Render the template's subject line exactly as _format_output does."""
    if not template.get('subject_line'):
        return None
    variables = get_template_loader().build_variables(
        report_date=report_date, user_full_name=user_full_name,
    )
    subject = template['subject_line']
    for name, value in variables.items():
        subject = subject.replace(f"{{{name}}}", str(value))
    return subject


def _report_fixture(session, settings: dict, call_type: str, report_date: date,
                    user_full_name: str) -> dict:
    template = get_template_loader().load(call_type)
    recipient_type = template.get('recipient_type', 'internal_management')
    active_client_id = SystemStateRepository(session).get_int('active_client_id')
    filter_client, client_id = get_client_filter(recipient_type, active_client_id)
    if filter_client and client_id is None:
        raise RuntimeError(f"{call_type}: client required and no active client set")

    system_prompt, user_prompt = PromptBuilder(session).build_prompt(
        template_name=call_type,
        report_date=report_date,
        filter_client=filter_client,
        client_id=client_id,
    )
    return {
        'id': f"{call_type}_{report_date.isoformat()}",
        'call_type': call_type,
        'kind': 'report',
        'report_date': report_date.isoformat(),
        'label': call_type,
        'system_prompt': system_prompt,
        'user_prompt': user_prompt,
        'system_prompt_sha': _sha(system_prompt),
        'user_prompt_sha': _sha(user_prompt),
        'max_tokens': settings['report_types'][call_type]['max_tokens'],
        'format': {
            'template_name': template.get('name', 'Report'),
            'subject_line': _subject_line(template, report_date, user_full_name),
        },
        'expected_sections': [s.get('title', '') for s in template.get('sections', [])],
        'filter_client': filter_client,
        'client_id': client_id,
    }


def _condensation_fixtures(session, settings: dict, meeting_date: date) -> List[dict]:
    condenser = NoteCondenser(session)
    fixtures = []
    for meeting in MeetingsRepository(session).get_by_date(meeting_date):
        notes = condenser.select_condensation_notes(meeting)
        if not notes:
            continue
        request = condenser.build_condensation_request(meeting, notes)
        fixtures.append({
            'id': f"note_condensation_{meeting_date.isoformat()}_m{meeting.id}",
            'call_type': 'note_condensation',
            'kind': 'condensation',
            'report_date': meeting_date.isoformat(),
            'label': meeting.title,
            'system_prompt': request.system_prompt or '',
            'user_prompt': request.prompt,
            'system_prompt_sha': _sha(request.system_prompt or ''),
            'user_prompt_sha': _sha(request.prompt),
            'max_tokens': settings['report_types']['note_condensation']['max_tokens'],
            'format': None,
            'expected_sections': [],
        })
    return fixtures


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Freeze production prompts to fixtures (read-only).")
    parser.add_argument('--daily', default='', help='Comma-separated YYYY-MM-DD for daily_internal')
    parser.add_argument('--weekly', default='', help='Comma-separated YYYY-MM-DD for weekly_client')
    parser.add_argument('--condense', default=None,
                        help="Comma-separated dates for note_condensation (default: --daily dates; 'none' to skip)")
    parser.add_argument('--out', default=None,
                        help='Fixture directory (default: staging/baseline/fixtures/<timestamp>)')
    args = parser.parse_args(argv)

    daily, weekly = _dates(args.daily), _dates(args.weekly)
    condense = daily if args.condense is None else _dates(args.condense)
    if not (daily or weekly or condense):
        parser.error('nothing to capture: pass --daily and/or --weekly')

    out = Path(args.out) if args.out else (
        REPO_ROOT / 'staging' / 'baseline' / 'fixtures' / datetime.now().strftime('%Y%m%d_%H%M%S'))
    out.mkdir(parents=True, exist_ok=True)

    settings = _read_json(REPO_ROOT / 'config' / 'ai_settings.json')
    policies = {
        name: _read_json(REPO_ROOT / 'config' / 'providers' / name / 'settings.json')
        for name in ('gemini', 'claude')
    }
    user_full_name = _user_full_name()

    plan = ([('daily_internal', d) for d in daily]
            + [('weekly_client', d) for d in weekly])

    fixtures: List[dict] = []
    failures: List[str] = []

    session = get_db().get_session()

    def _refuse_commit(*_a, **_k):
        raise RuntimeError("capture is read-only: session.commit() was called and refused")

    session.commit = _refuse_commit  # guard 1: nothing in this process can commit

    def _assert_read_only():
        # guard 2: the transaction is still the READ ONLY one we opened
        if session.execute(text("SHOW transaction_read_only")).scalar() != 'on':
            raise RuntimeError("transaction is no longer READ ONLY; aborting capture")

    try:
        # First statement of the transaction: the database refuses any write after this.
        session.execute(text("SET TRANSACTION READ ONLY"))
        _assert_read_only()

        for call_type, report_date in plan:
            try:
                fixtures.append(_report_fixture(session, settings, call_type, report_date, user_full_name))
                print(f"  captured {call_type} {report_date}")
            except Exception as exc:
                failures.append(f"{call_type} {report_date}: {type(exc).__name__}: {exc}")
                print(f"  FAILED   {call_type} {report_date}: {exc}")
            _assert_read_only()

        for meeting_date in condense:
            try:
                found = _condensation_fixtures(session, settings, meeting_date)
                fixtures.extend(found)
                print(f"  captured note_condensation {meeting_date}: {len(found)} meeting(s)")
            except Exception as exc:
                failures.append(f"note_condensation {meeting_date}: {type(exc).__name__}: {exc}")
                print(f"  FAILED   note_condensation {meeting_date}: {exc}")
            _assert_read_only()
    finally:
        session.rollback()
        session.close()

    for fixture in fixtures:
        with open(out / f"{fixture['id']}.json", 'w', encoding='utf-8') as handle:
            json.dump(fixture, handle, indent=2, ensure_ascii=False)

    manifest = {
        'fixture_version': FIXTURE_VERSION,
        'captured_at': datetime.now().isoformat(timespec='seconds'),
        'app_revision': _git_head(),
        'providers': {
            name: {
                'model': settings['providers'][name]['model'],
                'cost_per_1k_prompt_tokens': settings['providers'][name].get('cost_per_1k_prompt_tokens'),
                'cost_per_1k_completion_tokens': settings['providers'][name].get('cost_per_1k_completion_tokens'),
                'api_key_env': settings['providers'][name].get('api_key_env'),
                'policy': {k: v for k, v in policies[name].items() if k != 'description'},
            }
            for name in ('gemini', 'claude')
        },
        'routing': {
            k: {'primary': v.get('primary_provider'), 'fallback': v.get('fallback_provider')}
            for k, v in settings['report_types'].items()
        },
        'fixtures': [f['id'] for f in fixtures],
        'failures': failures,
    }
    with open(out / 'manifest.json', 'w', encoding='utf-8') as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)

    print(f"\n{len(fixtures)} fixture(s), {len(failures)} failure(s) -> {out}")
    return 1 if failures or not fixtures else 0


if __name__ == '__main__':
    sys.exit(main())
