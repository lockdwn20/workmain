"""
Standalone provider baseline: replay frozen WorkmAIn prompts against Gemini and
Claude, several samples each, and record raw output, production-formatted
output, tokens, timing and structure checks.

Imports nothing from workmain and never touches the database. Inputs are the
fixtures written by capture_baseline_prompts.py; the request payload each
provider receives mirrors WorkmAIn's providers as of the capture:

  Gemini  generate_content(model, contents=[user_prompt],
              config{max_output_tokens, system_instruction,
                     thinking_config, automatic_function_calling})   <- policy file
  Claude  messages.create(model, max_tokens, thinking, **sampling,   <- policy file
              system=[{type:text}], messages=[{role:user}])

"formatted" output is the raw output passed through a copy of
ReportGenerator._format_output() (Markdown branch) as of v1.42.2 — i.e. what
lands in staging/reports/, the email draft and Drive. Condensation output is
.strip()-ed, as condense_meeting does.

Requires: pip install google-genai anthropic   (both already in WorkmAIn's venv)
Keys:     GOOGLE_API_KEY / ANTHROPIC_API_KEY from the environment or --env-file.

Usage:
    python scripts/baseline/run_baseline.py --fixtures staging/baseline/fixtures/<id> --dry-run
    python scripts/baseline/run_baseline.py --fixtures staging/baseline/fixtures/<id> --samples 3
    python scripts/baseline/run_baseline.py ... --blind           # side-by-side with hidden labels
    python scripts/baseline/run_baseline.py ... --variant v.json  # replay with a prompt variant

Output holds real work content. Keep it under staging/baseline/ and never commit it.
"""

import argparse
import json
import os
import random
import re
import statistics
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

PROVIDERS = ('gemini', 'claude')
NORMAL_STOP = {'gemini': {'STOP', 'FinishReason.STOP'}, 'claude': {'end_turn'}}
NO_DATA_PHRASES = (
    'none at this time', 'continue current tasks', 'all requests and requirements are clear',
)


# --------------------------------------------------------------------------- env

def load_env_file(path: Path) -> None:
    """Minimal KEY=VALUE loader; never overrides variables already set."""
    if not path or not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip().removeprefix('export ').strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


# --------------------------------------------------------------------------- formatting (copy of production)

def format_output_v1422(content: str, fmt: Optional[dict], report_date: str) -> str:
    """Copy of ReportGenerator._format_output, MARKDOWN branch, as of v1.42.2."""
    if not fmt:
        return content.strip()
    subject_line = fmt.get('subject_line')
    if not content.startswith("#"):
        title = fmt.get('template_name') or "Report"
        header = f"# {title}\n"
        if subject_line:
            header += f"**Subject:** {subject_line}\n"
        d = datetime.fromisoformat(report_date)
        header += f"**Date:** {d.strftime('%B %d, %Y')}\n\n"
        return header + content
    if subject_line:
        lines = content.split('\n', 1)
        if len(lines) == 2:
            return f"{lines[0]}\n**Subject:** {subject_line}\n{lines[1]}"
        return f"{content}\n**Subject:** {subject_line}"
    return content


def format_output_proposed(content: str, fmt: Optional[dict], report_date: str,
                           expected: List[str]) -> str:
    """Candidate fix: the app owns the header. Drop a model-written title line
    (a first heading that is not a template section), then always prepend
    title, Subject and Date. Never inserts anything inside a section."""
    if not fmt:
        return content.strip()
    lines = content.strip().split('\n')
    if lines:
        m = HEADING_RE.match(lines[0])
        exp = [_norm(t) for t in expected]
        if m and not any(e and (e == _norm(m.group(2)) or e in _norm(m.group(2))) for e in exp):
            lines = lines[1:]
            while lines and not lines[0].strip():
                lines = lines[1:]
    header = f"# {fmt.get('template_name') or 'Report'}\n"
    if fmt.get('subject_line'):
        header += f"**Subject:** {fmt['subject_line']}\n"
    header += f"**Date:** {datetime.fromisoformat(report_date).strftime('%B %d, %Y')}\n\n"
    return header + '\n'.join(lines)


# --------------------------------------------------------------------------- structure checks

HEADING_RE = re.compile(r'^(#{1,6})\s+(.*?)\s*#*\s*$')


def _norm(title: str) -> str:
    t = re.sub(r'^\s*\d+[.)]\s*', '', title)          # leading "1. "
    t = re.sub(r'[*_`]', '', t)
    return re.sub(r'\s+', ' ', t).strip().lower().rstrip('?:')


def _headings(text: str) -> List[dict]:
    out = []
    for i, line in enumerate(text.splitlines()):
        m = HEADING_RE.match(line)
        if m:
            out.append({'line': i, 'level': len(m.group(1)), 'text': m.group(2)})
    return out


def check_report(raw: str, formatted: str, expected: List[str]) -> dict:
    exp_norm = [_norm(t) for t in expected]
    raw_heads = _headings(raw)

    def is_section(h):
        return any(e and (e == _norm(h['text']) or e in _norm(h['text'])) for e in exp_norm)

    section_heads = [h for h in raw_heads if is_section(h)]
    first_nonblank = next((l for l in raw.splitlines() if l.strip()), '')
    first_head = HEADING_RE.match(first_nonblank)
    model_title = bool(first_head) and not is_section({'text': first_head.group(2)})

    # where production put the Subject line
    f_lines = formatted.splitlines()
    subj_idx = next((i for i, l in enumerate(f_lines) if l.startswith('**Subject:**')), None)
    subject_placement = 'absent'
    if subj_idx is not None:
        prev = f_lines[subj_idx - 1] if subj_idx > 0 else ''
        m = HEADING_RE.match(prev)
        if m and is_section({'text': m.group(2)}):
            subject_placement = 'inside_section'
        elif m:
            subject_placement = 'under_title'
        else:
            subject_placement = 'other'

    found_order = []
    for h in section_heads:
        for idx, e in enumerate(exp_norm):
            if e and (e == _norm(h['text']) or e in _norm(h['text'])) and idx not in found_order:
                found_order.append(idx)
                break
    missing = [expected[i] for i in range(len(expected)) if i not in found_order]
    in_order = found_order == sorted(found_order)

    # section bodies -> "no data" boilerplate count, bullets
    lines = raw.splitlines()
    bounds = [h['line'] for h in section_heads] + [len(lines)]
    no_data_sections = []
    for n, h in enumerate(section_heads):
        body = ' '.join(l.strip() for l in lines[bounds[n] + 1:bounds[n + 1]] if l.strip()).lower()
        body = re.sub(r'^([-*]|[a-z][.)])\s*', '', body)
        if not body or any(p in body for p in NO_DATA_PHRASES) and len(body) < 80:
            no_data_sections.append(h['text'])

    return {
        'model_title_line': model_title,
        'subject_placement': subject_placement,
        'section_heading_levels': sorted({h['level'] for h in section_heads}),
        'sections_found': len(expected) - len(missing),
        'sections_expected': len(expected),
        'sections_missing': missing,
        'sections_in_order': in_order,
        'no_data_sections': no_data_sections,
        'bullets': sum(1 for l in lines if re.match(r'^\s*([-*]|[a-z][.)])\s+', l)),
        'words': len(raw.split()),
    }


def check_condensation(raw: str) -> dict:
    text = raw.strip()
    return {
        'chars': len(text),
        'within_200_chars': len(text) <= 200,
        'single_line': '\n' not in text,
        'type_prefix': bool(re.match(r'^[^:\n]{2,60}:\s+\S', text)),
        'has_markdown': bool(re.search(r'[*_`#]', text)),
        'words': len(text.split()),
    }


# --------------------------------------------------------------------------- providers

class GeminiCaller:
    def __init__(self, model: str, policy: dict, api_key_env: str):
        from google import genai
        from google.genai import types
        key = os.getenv(api_key_env or 'GOOGLE_API_KEY')
        if not key:
            raise SystemExit(f"{api_key_env or 'GOOGLE_API_KEY'} not set")
        self.types, self.model, self.policy = types, model, policy
        self.client = genai.Client(api_key=key)

    def call(self, system_prompt: str, user_prompt: str, max_tokens: int) -> dict:
        cfg = {
            'max_output_tokens': max_tokens,
            'thinking_config': self.policy['thinking_config'],
            'automatic_function_calling': self.policy['automatic_function_calling'],
        }
        if system_prompt:
            cfg['system_instruction'] = system_prompt
        r = self.client.models.generate_content(
            model=self.model, contents=[user_prompt],
            config=self.types.GenerateContentConfig(**cfg),
        )
        u = r.usage_metadata
        finish = None
        if r.candidates and getattr(r.candidates[0], 'finish_reason', None):
            finish = str(r.candidates[0].finish_reason)
        return {
            'content': r.text or '',
            'model': self.model,
            'prompt_tokens': u.prompt_token_count or 0,
            'completion_tokens': u.candidates_token_count or 0,
            'thinking_tokens': getattr(u, 'thoughts_token_count', None) or 0,
            'finish_reason': finish,
        }


class ClaudeCaller:
    def __init__(self, model: str, policy: dict, api_key_env: str):
        import anthropic
        key = os.getenv(api_key_env or 'ANTHROPIC_API_KEY')
        if not key:
            raise SystemExit(f"{api_key_env or 'ANTHROPIC_API_KEY'} not set")
        self.model, self.policy = model, policy
        self.client = anthropic.Anthropic(api_key=key)

    def call(self, system_prompt: str, user_prompt: str, max_tokens: int) -> dict:
        params = {'model': self.model, 'max_tokens': max_tokens, 'thinking': self.policy['thinking']}
        params.update(self.policy.get('sampling') or {})
        params['messages'] = [{'role': 'user', 'content': user_prompt}]
        if system_prompt:
            params['system'] = [{'type': 'text', 'text': system_prompt}]
        r = self.client.messages.create(**params)
        content = ''.join(b.text for b in r.content if b.type == 'text')
        return {
            'content': content,
            'model': self.model,
            'prompt_tokens': r.usage.input_tokens,
            'completion_tokens': r.usage.output_tokens,
            'thinking_tokens': 0,
            'finish_reason': r.stop_reason,
        }


# --------------------------------------------------------------------------- run

@dataclass
class Sample:
    fixture_id: str
    call_type: str
    label: str
    report_date: str
    provider: str
    sample: int
    variant: str
    model: Optional[str] = None
    raw: str = ''
    formatted: str = ''
    prompt_tokens: int = 0
    completion_tokens: int = 0
    thinking_tokens: int = 0
    finish_reason: Optional[str] = None
    latency_s: float = 0.0
    cost_usd: float = 0.0
    error: Optional[str] = None
    checks: Dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return (not self.error and bool(self.raw.strip())
                and str(self.finish_reason) in NORMAL_STOP[self.provider])


def apply_variant(fixture: dict, variant: Optional[dict]) -> dict:
    """Return system/user prompt (and format) with the variant applied, if it targets this call type."""
    system, user, fmt = fixture['system_prompt'], fixture['user_prompt'], fixture.get('format')
    if not variant:
        return {'system': system, 'user': user, 'format': fmt, 'format_mode': 'v1.42.2'}
    targets = variant.get('apply_to') or []
    if targets and fixture['call_type'] not in targets:
        return {'system': system, 'user': user, 'format': fmt, 'format_mode': 'v1.42.2'}
    per = (variant.get('per_call_type') or {}).get(fixture['call_type'], {})
    v = {**variant, **per}
    if 'system_prompt_replace' in v:
        system = v['system_prompt_replace']
    if v.get('system_prompt_append'):
        system = f"{system}\n\n{v['system_prompt_append']}"
    if v.get('user_prompt_append'):
        user = f"{user}\n\n{v['user_prompt_append']}"
    return {'system': system, 'user': user, 'format': fmt,
            'format_mode': v.get('format_output', 'v1.42.2')}


def with_retry(fn, attempts: int = 3, base_delay: float = 2.0):
    last = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:  # recorded on the sample if all attempts fail
            last = exc
            if i < attempts - 1:
                time.sleep(base_delay * (2 ** i))
    raise last


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.mean(xs), 1) if xs else 0


def write_summary(samples: List[Sample], fixtures: List[dict], manifest: dict,
                  out: Path, meta: dict) -> None:
    L = [f"# Provider baseline — {meta['run_id']}", "",
         "Contains real work content; never commit.", "",
         f"- Fixtures: `{meta['fixtures']}` (captured {manifest.get('captured_at')}, app {manifest.get('app_revision')})",
         f"- Variant: `{meta['variant']}`",
         f"- Gemini thinking level: `{meta.get('gemini_thinking_level')}`; report formatting: `{meta.get('format_output')}`",
         f"- Samples per provider per item: {meta['samples']}",
         f"- Models: " + ", ".join(f"{p} `{meta['models'][p]}`" for p in meta['providers']),
         f"- Calls: {len(samples)}, failed: {sum(1 for s in samples if not s.ok)}, "
         f"est. cost ${sum(s.cost_usd for s in samples):.2f}", ""]

    # per call type x provider
    L += ["## Totals by call type and provider", "",
          "| Call type | Provider | Runs ok | Avg prompt tok | Avg output tok | Avg thinking tok | Avg latency s | Avg words |",
          "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for ct in sorted({s.call_type for s in samples}):
        for p in meta['providers']:
            ss = [s for s in samples if s.call_type == ct and s.provider == p]
            if not ss:
                continue
            ok = [s for s in ss if s.ok]  # averages over successful runs only
            L.append(f"| {ct} | {p} | {len(ok)}/{len(ss)} | {_mean([s.prompt_tokens for s in ok])} "
                     f"| {_mean([s.completion_tokens for s in ok])} | {_mean([s.thinking_tokens for s in ok])} "
                     f"| {_mean([s.latency_s for s in ok])} | {_mean([s.checks.get('words') for s in ok])} |")
    L.append("")

    reports = [s for s in samples if s.checks and 'subject_placement' in s.checks]
    if reports:
        L += ["## Report structure (per sample)", "",
              "| Item | Provider | # | Model title | Subject placement | Section levels | Sections | In order | 'None' sections | Bullets | Finish |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for s in reports:
            c = s.checks
            L.append(f"| {s.fixture_id} | {s.provider} | {s.sample} | {'yes' if c['model_title_line'] else 'no'} "
                     f"| {c['subject_placement']} | {','.join(map(str, c['section_heading_levels'])) or '-'} "
                     f"| {c['sections_found']}/{c['sections_expected']} | {'yes' if c['sections_in_order'] else 'no'} "
                     f"| {len(c['no_data_sections'])} | {c['bullets']} | {s.finish_reason} |")
        L.append("")

    conds = [s for s in samples if s.checks and 'within_200_chars' in s.checks]
    if conds:
        L += ["## Condensation checks (per sample)", "",
              "| Item | Meeting | Provider | # | Chars | ≤200 | One line | Type prefix | Markdown | Finish |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for s in conds:
            c = s.checks
            L.append(f"| {s.fixture_id} | {s.label} | {s.provider} | {s.sample} | {c['chars']} "
                     f"| {'yes' if c['within_200_chars'] else 'NO'} | {'yes' if c['single_line'] else 'NO'} "
                     f"| {'yes' if c['type_prefix'] else 'no'} | {'YES' if c['has_markdown'] else 'no'} | {s.finish_reason} |")
        L.append("")

    errs = [s for s in samples if s.error]
    if errs:
        L += ["## Errors", ""] + [f"- {s.fixture_id} {s.provider} #{s.sample}: {s.error}" for s in errs] + [""]

    L += ["## Verdict (Ray)", "",
          "| Call type | Gemini comparable to Claude? | Why |", "| --- | --- | --- |",
          "| daily_internal | | |", "| weekly_client | | |", "| note_condensation | | |", ""]
    (out / 'summary.md').write_text("\n".join(L), encoding='utf-8')


def write_side_by_side(samples: List[Sample], fixtures: List[dict], out: Path,
                       blind: bool, seed: int) -> None:
    rng = random.Random(seed)
    key = {}
    L = ["# Side-by-side outputs", "",
         "Contains real work content; never commit.",
         "Shown: production-formatted output (what lands in staging/reports and the email draft)." , ""]
    if blind:
        L += ["Labels are hidden. Mapping is in `blind_key.json` — read it after you have judged.", ""]
    for fx in fixtures:
        ss = [s for s in samples if s.fixture_id == fx['id']]
        if not ss:
            continue
        L += [f"## {fx['id']} — {fx['label']}", ""]
        provs = sorted({s.provider for s in ss})
        labels = {p: p for p in provs}
        if blind:
            letters = ['A', 'B', 'C', 'D'][:len(provs)]
            rng.shuffle(letters)
            labels = {p: f"Output {letters[i]}" for i, p in enumerate(provs)}
            key[fx['id']] = {v: k for k, v in labels.items()}
        for p in sorted(provs, key=lambda x: labels[x]):
            for s in sorted([s for s in ss if s.provider == p], key=lambda x: x.sample):
                L.append(f"### {labels[p]} — sample {s.sample}")
                L.append("")
                if s.error:
                    L += [f"Error: {s.error}", ""]
                    continue
                L += ["~~~~", s.formatted, "~~~~", ""]
    (out / 'side_by_side.md').write_text("\n".join(L), encoding='utf-8')
    if blind:
        (out / 'blind_key.json').write_text(json.dumps(key, indent=2), encoding='utf-8')


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Standalone Gemini vs Claude baseline from frozen fixtures.")
    ap.add_argument('--fixtures', required=True, help='Directory written by capture_baseline_prompts.py')
    ap.add_argument('--out', default=None, help='Run directory (default: staging/baseline/runs/<timestamp>[_variant])')
    ap.add_argument('--samples', type=int, default=3)
    ap.add_argument('--providers', default='gemini,claude')
    ap.add_argument('--only', default=None, help='Comma-separated call types to run')
    ap.add_argument('--gemini-model', default=None, help='Override the captured Gemini model')
    ap.add_argument('--gemini-thinking-level', default=None,
                    help="Override the policy's thinking_config.thinking_level (e.g. low, high)")
    ap.add_argument('--format-output', default=None, choices=['v1.42.2', 'proposed', 'none'],
                    help='Override the formatting applied to report output (default: variant, else v1.42.2)')
    ap.add_argument('--tag', default=None, help='Suffix for the run folder name')
    ap.add_argument('--claude-model', default=None, help='Override the captured Claude model')
    ap.add_argument('--variant', default=None, help='Prompt variant JSON (see README)')
    ap.add_argument('--env-file', default='.env', help='KEY=VALUE file for API keys (default: .env)')
    ap.add_argument('--blind', action='store_true', help='Hide provider labels in side_by_side.md')
    ap.add_argument('--seed', type=int, default=181)
    ap.add_argument('--dry-run', action='store_true', help='Print the plan and call count; call nothing')
    args = ap.parse_args(argv)

    fx_dir = Path(args.fixtures)
    manifest = json.loads((fx_dir / 'manifest.json').read_text(encoding='utf-8'))
    fixtures = [json.loads((fx_dir / f"{fid}.json").read_text(encoding='utf-8')) for fid in manifest['fixtures']]
    if args.only:
        wanted = {t.strip() for t in args.only.split(',')}
        fixtures = [f for f in fixtures if f['call_type'] in wanted]
    providers = [p.strip() for p in args.providers.split(',') if p.strip() in PROVIDERS]
    variant = json.loads(Path(args.variant).read_text(encoding='utf-8')) if args.variant else None
    variant_name = (variant or {}).get('name', 'baseline')

    models = {
        'gemini': args.gemini_model or manifest['providers']['gemini']['model'],
        'claude': args.claude_model or manifest['providers']['claude']['model'],
    }
    total = len(fixtures) * len(providers) * args.samples
    print(f"{len(fixtures)} fixture(s) x {len(providers)} provider(s) x {args.samples} sample(s) = {total} call(s)")
    for f in fixtures:
        print(f"  {f['id']:<55} {f['label'][:40]}")
    print("Models: " + ", ".join(f"{p}={models[p]}" for p in providers) + f"; variant={variant_name}")
    if args.dry_run:
        return 0

    load_env_file(Path(args.env_file))
    callers = {}
    for p in providers:
        cfg = manifest['providers'][p]
        cls = GeminiCaller if p == 'gemini' else ClaudeCaller
        policy = json.loads(json.dumps(cfg['policy']))
        if p == 'gemini' and args.gemini_thinking_level:
            policy.setdefault('thinking_config', {})['thinking_level'] = args.gemini_thinking_level
        callers[p] = cls(models[p], policy, cfg.get('api_key_env'))

    run_id = (datetime.now().strftime('%Y%m%d_%H%M%S') + ('' if not variant else f"_{variant_name}")
              + (f"_think-{args.gemini_thinking_level}" if args.gemini_thinking_level else '')
              + (f"_{args.tag}" if args.tag else ''))
    out = Path(args.out) if args.out else Path('staging') / 'baseline' / 'runs' / run_id
    out.mkdir(parents=True, exist_ok=True)

    samples: List[Sample] = []
    n = 0
    with open(out / 'results.jsonl', 'w', encoding='utf-8') as jl:
        for fx in fixtures:
            req = apply_variant(fx, variant)
            for i in range(1, args.samples + 1):
                for p in providers:  # interleave providers so drift over time hits both
                    n += 1
                    s = Sample(fixture_id=fx['id'], call_type=fx['call_type'], label=fx['label'],
                               report_date=fx['report_date'], provider=p, sample=i,
                               variant=variant_name, model=models[p])
                    t0 = time.monotonic()
                    try:
                        r = with_retry(lambda: callers[p].call(req['system'], req['user'], fx['max_tokens']))
                        s.raw = r['content']
                        s.prompt_tokens, s.completion_tokens = r['prompt_tokens'], r['completion_tokens']
                        s.thinking_tokens, s.finish_reason = r['thinking_tokens'], r['finish_reason']
                    except Exception as exc:
                        s.error = f"{type(exc).__name__}: {exc}"
                    s.latency_s = round(time.monotonic() - t0, 2)

                    pc = manifest['providers'][p]
                    s.cost_usd = round(
                        (s.prompt_tokens / 1000) * (pc.get('cost_per_1k_prompt_tokens') or 0)
                        + ((s.completion_tokens + s.thinking_tokens) / 1000)
                        * (pc.get('cost_per_1k_completion_tokens') or 0), 5)

                    if fx['kind'] == 'report':
                        mode = args.format_output or req['format_mode']
                        if mode == 'v1.42.2':
                            s.formatted = format_output_v1422(s.raw, req['format'], fx['report_date'])
                        elif mode == 'proposed':
                            s.formatted = format_output_proposed(
                                s.raw, req['format'], fx['report_date'], fx.get('expected_sections', []))
                        else:
                            s.formatted = s.raw
                        if s.raw:
                            s.checks = check_report(s.raw, s.formatted, fx.get('expected_sections', []))
                    else:
                        s.formatted = s.raw.strip()
                        if s.raw:
                            s.checks = check_condensation(s.raw)

                    samples.append(s)
                    jl.write(json.dumps(asdict(s), ensure_ascii=False) + "\n")
                    jl.flush()
                    status = 'ok' if s.ok else f"FAIL {s.error or s.finish_reason}"
                    print(f"  [{n}/{total}] {fx['id']} {p} #{i}: {status} ({s.latency_s}s)")

    gem_policy = manifest['providers']['gemini']['policy'].get('thinking_config', {})
    meta = {'run_id': run_id, 'fixtures': str(fx_dir), 'variant': variant_name,
            'gemini_thinking_level': args.gemini_thinking_level or gem_policy.get('thinking_level'),
            'format_output': args.format_output or ((variant or {}).get('format_output') or 'v1.42.2'),
            'samples': args.samples, 'providers': providers, 'models': models}
    (out / 'run_meta.json').write_text(json.dumps({**meta, 'manifest': manifest}, indent=2), encoding='utf-8')
    write_summary(samples, fixtures, manifest, out, meta)
    write_side_by_side(samples, fixtures, out, args.blind, args.seed)

    failed = sum(1 for s in samples if not s.ok)
    print(f"\n{len(samples)} call(s), {failed} failed -> {out}")
    print(f"  {out / 'summary.md'}\n  {out / 'side_by_side.md'}")
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
