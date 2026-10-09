"""
Read-only side-by-side comparison of two AI providers for one date.

Sends each provider the same production-built request for every call type
routed to the candidate provider, and writes the responses to a Markdown file
for a person to read. The script writes nothing to the database: it never
generates or saves a report, never condenses a meeting, never commits, and
rolls its session back before closing it.

The output holds real work content and can name the client. Write it only
under staging/reports/ (gitignored) and never commit or quote it.

Usage:
    python scripts/compare_providers.py --date 2026-10-08 \
        --out staging/reports/provider_comparison_20261008.md

Exit status is 0 when every run returned non-empty content and stopped on its
provider's normal stop reason, 1 otherwise.
"""

import argparse
import sys
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

from workmain.ai.base_provider import GenerationRequest, GenerationResponse, ProviderType
from workmain.ai.note_condenser import NoteCondenser
from workmain.ai.provider_manager import ProviderManager, get_provider_manager
from workmain.ai.report_generator import ReportGenerator
from workmain.cli.commands.reports import get_client_filter
from workmain.database.connection import get_db
from workmain.database.repositories.meetings_repo import MeetingsRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.templates_engine import get_template_loader

CONDENSATION_TYPE = 'note_condensation'
SUCCESS_REASONS = {'FinishReason.STOP', 'end_turn'}


@dataclass
class Run:
    """One request sent to one provider, or one call type that was skipped."""

    call_type: str
    label: str
    provider: str
    response: Optional[GenerationResponse] = None
    error: Optional[str] = None
    skipped: Optional[str] = None

    @property
    def reason(self) -> Optional[str]:
        """The provider's finish or stop reason, or None when absent."""
        if self.response is None:
            return None
        metadata = self.response.metadata or {}
        key = 'finish_reason' if self.response.provider == ProviderType.GEMINI else 'stop_reason'
        value = metadata.get(key)
        return str(value) if value else None

    @property
    def passed(self) -> bool:
        """True only for non-empty content with a normal stop reason (DR6)."""
        if self.error or self.skipped or self.response is None:
            return False
        return bool(self.response.content.strip()) and self.reason in SUCCESS_REASONS


def exit_status(runs: List[Run]) -> int:
    """Return 0 when every run passed, 1 otherwise (including no runs)."""
    return 0 if runs and all(run.passed for run in runs) else 1


def _default_types(provider_manager: ProviderManager, candidate: ProviderType) -> List[str]:
    """Call types whose primary provider is the candidate, per live routing."""
    return [
        name for name in provider_manager.get_report_type_names()
        if provider_manager.get_report_config(name).primary_provider == candidate
    ]


def _report_request(
    session, provider_manager: ProviderManager, call_type: str, report_date: date,
) -> Optional[GenerationRequest]:
    """Build a report type's request as generate_report would; None if no client is active."""
    template = get_template_loader().load(call_type)
    recipient_type = template.get('recipient_type', 'internal_management')
    active_client_id = SystemStateRepository(session).get_int('active_client_id')
    filter_client, client_id = get_client_filter(recipient_type, active_client_id)
    if filter_client and client_id is None:
        return None
    generator = ReportGenerator(session, provider_manager=provider_manager)
    preview = generator.preview_report(
        template_name=call_type,
        report_date=report_date,
        filter_client=filter_client,
        client_id=client_id,
    )
    return GenerationRequest(
        prompt=preview['user_prompt'],
        system_prompt=preview['system_prompt'],
        max_tokens=provider_manager.get_max_tokens(call_type),
    )


def _send(
    provider_manager: ProviderManager,
    request: GenerationRequest,
    call_type: str,
    label: str,
    providers: List[ProviderType],
) -> List[Run]:
    """Send one request to each provider in order; record exceptions per run."""
    runs = []
    for provider in providers:
        run = Run(call_type=call_type, label=label, provider=provider.value)
        try:
            run.response, _ = provider_manager.generate(
                request, report_type=call_type, provider_override=provider,
            )
        except Exception as exc:  # recorded against the run; the script continues
            run.error = f"{type(exc).__name__}: {exc}"
        runs.append(run)
    return runs


def compare(
    session,
    report_date: date,
    candidate,
    baseline,
    types: Optional[List[str]],
    provider_manager: ProviderManager,
) -> List[Run]:
    """
    Send each call type's production request to the candidate, then the baseline.

    Args:
        session: Database session, used for reads only
        report_date: Date whose data the requests are built from
        candidate: Provider under test (ProviderType or its value)
        baseline: Provider compared against (ProviderType or its value)
        types: Call types to compare, or None for those routed to the candidate
        provider_manager: The manager every builder and every send uses

    Returns:
        One Run per provider per request, plus one skipped Run per skipped call type
    """
    candidate, baseline = ProviderType(candidate), ProviderType(baseline)
    call_types = types if types else _default_types(provider_manager, candidate)
    providers = [candidate, baseline]
    runs: List[Run] = []

    for call_type in call_types:
        try:
            if call_type == CONDENSATION_TYPE:
                condenser = NoteCondenser(session)
                condenser.provider_manager = provider_manager
                meetings = MeetingsRepository(session).get_by_date(report_date)
                for meeting in meetings:
                    notes = condenser.select_condensation_notes(meeting)
                    if not notes:
                        continue
                    request = condenser.build_condensation_request(meeting, notes)
                    runs.extend(_send(
                        provider_manager, request, call_type, meeting.title, providers,
                    ))
            else:
                request = _report_request(session, provider_manager, call_type, report_date)
                if request is None:
                    runs.append(Run(
                        call_type=call_type, label=call_type, provider='-',
                        skipped='client required and none active',
                    ))
                    continue
                runs.extend(_send(provider_manager, request, call_type, call_type, providers))
        except Exception as exc:  # request could not be built: a failed run, not a crash
            runs.append(Run(
                call_type=call_type, label=call_type, provider='-',
                error=f"{type(exc).__name__}: {exc}",
            ))
    return runs


def _thinking_tokens(response: GenerationResponse) -> int:
    return response.tokens_used - response.prompt_tokens - response.completion_tokens


def _summary_rows(runs: List[Run]) -> List[str]:
    rows = ["| Call type | Request | Provider | Model | Reason | Result |", "| --- | --- | --- | --- | --- | --- |"]
    for run in runs:
        model = run.response.model if run.response else '-'
        if run.skipped:
            result = f"SKIPPED: {run.skipped}"
        elif run.error:
            result = "FAIL (error)"
        else:
            result = "pass" if run.passed else "FAIL"
        rows.append(
            f"| {run.call_type} | {run.label} | {run.provider} | {model} "
            f"| {run.reason or '-'} | {result} |"
        )
    return rows


def render(runs: List[Run], report_date: date, candidate: str, baseline: str) -> str:
    """Render the runs as the Markdown comparison document."""
    lines = [
        f"# Provider comparison: {candidate} vs {baseline}, data of {report_date}",
        "",
        f"Generated {datetime.now():%Y-%m-%d %H:%M}. Contains real work content; never commit.",
        "",
    ]
    seen = None
    for run in runs:
        section = (run.call_type, run.label)
        if section != seen:
            lines += [f"## {run.call_type}: {run.label}", ""]
            seen = section
        lines.append(f"### {run.provider}")
        lines.append("")
        if run.skipped:
            lines += [f"Skipped: {run.skipped}", ""]
        elif run.error:
            lines += [f"Error: {run.error}", ""]
        else:
            r = run.response
            lines += [
                f"- Model: {r.model}",
                f"- Prompt tokens: {r.prompt_tokens}",
                f"- Completion tokens: {r.completion_tokens}",
                f"- Thinking tokens: {_thinking_tokens(r)}",
                f"- Finish/stop reason: {run.reason or 'none'}",
                "",
                "~~~~",
                r.content,
                "~~~~",
                "",
            ]
    lines += ["## Summary", ""] + _summary_rows(runs) + [""]
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    """Parse arguments, run the comparison read-only, write the file, return the exit status."""
    parser = argparse.ArgumentParser(description="Read-only provider comparison for one date.")
    parser.add_argument('--date', required=True, help='YYYY-MM-DD')
    parser.add_argument('--out', required=True, help='Output path (under staging/reports/)')
    parser.add_argument('--candidate', default='gemini')
    parser.add_argument('--baseline', default='claude')
    parser.add_argument('--types', help='Comma-separated call types (default: routed to the candidate)')
    args = parser.parse_args(argv)

    report_date = date.fromisoformat(args.date)
    types = [t.strip() for t in args.types.split(',') if t.strip()] if args.types else None

    session = get_db().get_session()
    try:
        runs = compare(
            session, report_date, args.candidate, args.baseline, types, get_provider_manager(),
        )
    finally:
        session.rollback()
        session.close()

    document = render(runs, report_date, args.candidate, args.baseline)
    with open(args.out, 'w', encoding='utf-8') as handle:
        handle.write(document)
    print("\n".join(_summary_rows(runs)))
    print(f"\nOutput: {args.out}")
    return exit_status(runs)


if __name__ == '__main__':
    sys.exit(main())
