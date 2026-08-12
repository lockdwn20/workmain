WorkmAIn
Feature Spec: Cost Tracking Persistence + Costs Commands Redesign v1.4
20260528

---

**Version History:**
- v1.0 (20260528): Initial spec
- v1.1 (20260528): Four pre-flight corrections: migration split (017_ai_costs.sql +
  backfill script); datetime.utcnow sweep (Item 13); CHECK constraint on
  interaction_type; --type no-op filter on notes/meetings costs
- v1.2 (20260528): Date filtering added to all four costs commands. New flags:
  --date/-d (single day), --start/-b (range start), --end/-e (range end).
  New Gate 0 (list_reports() pre-flight). New Gate 1f (date_utils.py).
  Precedence rules defined. reports costs filtering on report_date.
  CLI_STANDARDS.md §5.3 scope expansions for -b, -e, -M.
- v1.3 (20260528): Added standard development scaffolding missing from v1.2:
  Pre-Implementation Reading section; branch setup + test baseline in Gate 0;
  git commit commands at each gate; merge flow block in Gate 5; session
  handoff instruction; gate completion checklist; Constraints and Reminders
  section; END OF SPEC footer.
- v1.4 (20260528): Gate 2 expanded to include provider wiring fix. Root cause
  identified during Gate 0/1 review: provider_manager._load_config() is a stub
  (body: pass), ai_settings.json is never read, Claude is hardcoded everywhere.
  Added Gate 2c (implement _load_config()), Gate 2d (fix note_condenser —
  hardcoded self.claude), Gate 2e (fix report_generator — template-metadata
  provider override bypasses config), Gate 2f (fix providers list display).
  Added audit findings to Critical Files Summary and Scope Items. Added test
  cases in Gate 5 for provider wiring. Updated Constraints and Reminders.

---

## Context

Two problems prompted this work:
1. `providers costs` and `reports costs` are named-backwards — `providers costs` is
   currently a per-report list while `reports costs` is the aggregate-by-provider view.
2. Neither command reflects non-report AI interactions. Meeting/note condensations make
   real Claude API calls whose costs are tracked in-memory via `CostTracker` but silently
   discarded on process exit — they never hit the database.

This spec covers: (a) adding a dedicated `ai_costs` table to persist ALL AI API
interactions, (b) injecting persistence into `note_condenser.py` and
`report_generator.py`, (c) swapping the display roles of `providers costs` and
`reports costs` to match their names, (d) adding `workmain notes costs` and
`workmain meetings costs` subcommands, (e) sweeping all `datetime.utcnow()`
deprecations (Item 13, FEATURE_BACKLOG.md), (f) adding granular date filtering
(-d/-b/-e) to all four costs commands, and (g) fixing the provider wiring gap
where `provider_manager._load_config()` was a stub causing `ai_settings.json` to
be ignored and Claude hardcoded throughout the pipeline.

**Branch:** `feature/cost-tracking-persistence` from `dev`
**Version bump:** v1.16.1 → v1.17.0

---

## Pre-Implementation Reading (Claude Code)

Before writing any code, read in this order:

1. `CLAUDE.md` — session pattern, file versioning rules, commit format
2. `docs/CLI_STANDARDS.md` v2.4 — command naming, flag short-forms, violation register
3. `docs/TESTING_STANDARDS.md` — db_session fixture, sentinel dates, test file template
4. `docs/GIT_WORKFLOW_STANDARDS.md` — branch strategy, version bump rules, merge cadence
5. This spec — gate by gate

Do not begin Gate 0 until all five documents are read.

---

## Architecture: New `ai_costs` Table

A single table that stores every AI API call, regardless of context:

```
ai_costs
─────────────────────────────────────────────────────────
id                SERIAL PK
interaction_type  VARCHAR(50) NOT NULL   -- CHECK IN ('report', 'condensation')
                                         -- Phase 13-1 extends: adds 'intent_parse'
provider          VARCHAR(50) NOT NULL   -- 'claude' | 'gemini'
model             VARCHAR(100)
prompt_tokens     INTEGER NOT NULL DEFAULT 0
completion_tokens INTEGER NOT NULL DEFAULT 0
total_tokens      INTEGER NOT NULL DEFAULT 0
cost_usd          NUMERIC(12,8) NOT NULL DEFAULT 0
generation_time_s FLOAT
report_id         INTEGER → reports.id ON DELETE SET NULL (nullable)
meeting_id        INTEGER → meetings.id ON DELETE SET NULL (nullable)
context_label     VARCHAR(255)           -- report type name or meeting title
created_at        TIMESTAMP NOT NULL DEFAULT NOW()
```

Only one FK is populated per row: `report_id` for report generation, `meeting_id` for
condensation.

**Dual-write approach:** `report_generator.py` continues writing cost data to
`reports.report_metadata` (backward compat) AND also writes a row to `ai_costs`. This
lets `reports costs` keep reading the `reports` table directly (preserving `report_date`
and full report context) while `providers costs` reads `ai_costs` for the complete
cross-type picture.

---

## Gate 0 — Pre-flight

### Objective

Establish the feature branch, verify the test baseline, confirm migration numbering,
and audit `list_reports()` before any code is written.

### Steps

**1. Create feature branch:**
```bash
git checkout dev
git pull origin dev
git checkout -b feature/cost-tracking-persistence
```

**2. Verify test baseline:**
```bash
python -m pytest tests/ -v
```
Record the passing count. All subsequent gates must maintain 0 failures against this
baseline before adding new tests. Expected: 413 passed, 0 failed.

**3. Confirm migration numbering:**
```bash
ls workmain/database/migrations/
```
Verify that `016_reports_status_columns.sql` is the highest numbered file. The new
migration will be `017_ai_costs.sql`. Do not assume — record in gate summary.

**4. Audit `ReportsRepository.list_reports()` signature:**

Inspect `workmain/database/repositories/reports_repo.py`. Check whether `list_reports()`
accepts `start_date` and `end_date` parameters that filter on `reports.report_date`.

- **If present and filtering on `report_date`:** no change needed. Proceed.
- **If absent:** add them before Gate 3b is implemented. Required addition:

```python
def list_reports(
    self,
    status: Optional[str] = None,
    report_type: Optional[str] = None,
    start_date: Optional[date] = None,   # filters on report_date
    end_date: Optional[date] = None,     # filters on report_date
) -> List[Report]: ...
```

Filter logic:
```python
if start_date:
    query = query.filter(Report.report_date >= start_date)
if end_date:
    query = query.filter(Report.report_date <= end_date)
```

**5. Audit for any additional `datetime.utcnow()` instances:**
```bash
grep -rn "datetime.utcnow" workmain/ --include="*.py"
```
Record all hits. These are fixed at Gate 1e. Known instance:
`workmain/database/repositories/gdrive_repository.py`

### Gate 0 Verification
```
[ ] feature/cost-tracking-persistence branch created from dev
[ ] test baseline recorded (413 passed, 0 failed — or actual count if different)
[ ] migration 016 confirmed as highest; 017 slot confirmed available
[ ] list_reports() audit complete — result documented (params present / added)
[ ] datetime.utcnow audit complete — all hits recorded
```

---

## Gate 1 — DB Layer

### 1a. `workmain/database/models.py`

Add `AiCost` model (after `Report` model):
- `CheckConstraint` in `__table_args__` enforces valid `interaction_type` values
- `created_at` default uses `datetime.now(timezone.utc)` — no `datetime.utcnow`
- Ensure `from datetime import datetime, timezone` is present in imports
- Ensure `from sqlalchemy import CheckConstraint` is present in imports

```python
class AiCost(Base):
    __tablename__ = 'ai_costs'
    __table_args__ = (
        CheckConstraint(
            "interaction_type IN ('report', 'condensation')",
            name='ai_costs_interaction_type_check'
        ),
    )

    id = Column(Integer, primary_key=True)
    interaction_type = Column(String(50), nullable=False)
    provider = Column(String(50), nullable=False)
    model = Column(String(100))
    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    cost_usd = Column(Numeric(12, 8), nullable=False, default=0)
    generation_time_s = Column(Float)
    report_id = Column(Integer, ForeignKey('reports.id', ondelete='SET NULL'), nullable=True)
    meeting_id = Column(Integer, ForeignKey('meetings.id', ondelete='SET NULL'), nullable=True)
    context_label = Column(String(255))
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    report = relationship("Report", backref="ai_costs", passive_deletes=True)
    meeting = relationship("Meeting", backref="ai_costs", passive_deletes=True)
```

### 1b. `workmain/database/migrations/017_ai_costs.sql` (new migration file)

Schema-only migration following the established numbered convention.

```sql
-- WorkmAIn
-- Migration 017: AI cost tracking table
-- 20260528

CREATE TABLE IF NOT EXISTS ai_costs (
    id                SERIAL PRIMARY KEY,
    interaction_type  VARCHAR(50) NOT NULL,
    provider          VARCHAR(50) NOT NULL,
    model             VARCHAR(100),
    prompt_tokens     INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens      INTEGER NOT NULL DEFAULT 0,
    cost_usd          NUMERIC(12,8) NOT NULL DEFAULT 0,
    generation_time_s FLOAT,
    report_id         INTEGER REFERENCES reports(id) ON DELETE SET NULL,
    meeting_id        INTEGER REFERENCES meetings(id) ON DELETE SET NULL,
    context_label     VARCHAR(255),
    created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ai_costs_interaction_type_check
        CHECK (interaction_type IN ('report', 'condensation'))
);

CREATE INDEX IF NOT EXISTS idx_ai_costs_interaction_type ON ai_costs(interaction_type);
CREATE INDEX IF NOT EXISTS idx_ai_costs_provider         ON ai_costs(provider);
CREATE INDEX IF NOT EXISTS idx_ai_costs_created_at       ON ai_costs(created_at);
CREATE INDEX IF NOT EXISTS idx_ai_costs_report_id        ON ai_costs(report_id);
CREATE INDEX IF NOT EXISTS idx_ai_costs_meeting_id       ON ai_costs(meeting_id);
```

**Note for Phase 13-1:** Extend the constraint when `intent_parse` is added:
```sql
ALTER TABLE ai_costs DROP CONSTRAINT ai_costs_interaction_type_check;
ALTER TABLE ai_costs ADD CONSTRAINT ai_costs_interaction_type_check
    CHECK (interaction_type IN ('report', 'condensation', 'intent_parse'));
```
Update `__table_args__` CHECK in `models.py` in the same gate.

### 1c. `workmain/database/repositories/ai_costs_repo.py` (new file)

Public interface:

```python
class AiCostRepository:
    def create(self, interaction_type, provider, model,
               prompt_tokens, completion_tokens, cost_usd,
               generation_time_s=None, report_id=None,
               meeting_id=None, context_label=None) -> AiCost

    def get_filtered(self, interaction_type=None, provider=None,
                     start_date=None, end_date=None,
                     limit=50) -> List[AiCost]
    # Filters on ai_costs.created_at

    def get_summary(self, interaction_type=None,
                    start_date=None, end_date=None) -> dict
    # Filters on ai_costs.created_at
    # Returns: {total_cost, total_tokens, total_calls,
    #           by_provider: {name: {calls, cost, tokens}},
    #           by_type: {name: {calls, cost, tokens}}}

def get_ai_cost_repository(session) -> AiCostRepository: ...
```

### 1d. `scripts/migrate_backfill_ai_costs.py` (new script — backfill only)

Backfill-only. Schema creation handled by `017_ai_costs.sql`; run after migration.

1. Check `ai_costs` table exists — raise clear error if migration not yet applied
2. Read all `reports` rows where `metadata` column contains non-null cost data
3. Insert corresponding `ai_costs` rows:
   - `interaction_type='report'`, `report_id=report.id`,
     `context_label=report.report_type`
   - Extract `provider`, `model`, token counts, `cost_usd`, `generation_time_s`
     from `metadata` JSON
   - Note: ORM attribute is `report_metadata`; DB column is `metadata`
4. Idempotent: skip reports where a matching `ai_costs` row already exists
   (`report_id=report.id`, `interaction_type='report'`)
5. Print summary: rows inserted, rows skipped

### 1e. `datetime.utcnow()` Deprecation Sweep — Item 13

Replace all `datetime.utcnow()` calls with `datetime.now(timezone.utc)` across the
codebase using the hit list recorded at Gate 0.

**Procedure:**
1. For each file in the audit hit list:
   - Replace `datetime.utcnow()` → `datetime.now(timezone.utc)`
   - Ensure `from datetime import timezone` is present in imports
   - Bump file version header (minor increment)
2. Verify: `grep -rn "datetime.utcnow" workmain/ --include="*.py"` — must return empty

Known instance: `workmain/database/repositories/gdrive_repository.py`

### 1f. `workmain/utils/date_utils.py` (new utility file)

Shared date-window resolution used by all four costs commands. Two functions:

**`resolve_date_window()`:**

```python
from __future__ import annotations
import calendar
from datetime import date
from typing import Optional, Tuple
import click


def resolve_date_window(
    date_str: Optional[str],
    start_str: Optional[str],
    end_str: Optional[str],
    month_str: Optional[str],
    show_all: bool,
) -> Tuple[Optional[date], Optional[date]]:
    """
    Resolve mutually exclusive date filter CLI flags into (start_date, end_date).

    Precedence (highest → lowest):
      --all              → (None, None)       full history, no filter
      --date             → (date, date)       single day
      --start [--end]    → (start, end|today) explicit range
      --month            → (first, last)      calendar month
      (default)          → current month

    Mutual exclusions — raises click.UsageError:
      --date  with  --start or --end
      --date  with  --month
      --start/--end  with  --month
      --end  without  --start
    """
    if date_str and start_str:
        raise click.UsageError("--date and --start are mutually exclusive.")
    if date_str and month_str:
        raise click.UsageError("--date and --month are mutually exclusive.")
    if (start_str or end_str) and month_str:
        raise click.UsageError("--start/--end and --month are mutually exclusive.")
    if end_str and not start_str:
        raise click.UsageError("--end requires --start.")

    if show_all:
        return None, None
    if date_str:
        d = date.fromisoformat(date_str)
        return d, d
    if start_str:
        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str) if end_str else date.today()
        return start, end
    if month_str:
        year, mon = int(month_str[:4]), int(month_str[5:7])
        last_day = calendar.monthrange(year, mon)[1]
        return date(year, mon, 1), date(year, mon, last_day)

    today = date.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    return date(today.year, today.month, 1), date(today.year, today.month, last_day)
```

**`format_date_window_label()`:**

```python
def format_date_window_label(
    start_date: Optional[date],
    end_date: Optional[date],
) -> str:
    """
    Format the active date window as a human-readable label.

    Returns:
      None/None     → "All Time"
      same day      → "2026-05-15"
      full month    → "May 2026"
      custom range  → "2026-05-01 to 2026-05-15"
    """
    if start_date is None:
        return "All Time"
    if start_date == end_date:
        return start_date.isoformat()
    last_of_month = calendar.monthrange(start_date.year, start_date.month)[1]
    if (start_date.day == 1
            and end_date.day == last_of_month
            and start_date.year == end_date.year
            and start_date.month == end_date.month):
        return start_date.strftime("%B %Y")
    return f"{start_date.isoformat()} to {end_date.isoformat()}"
```

All four costs commands import both functions from `workmain.utils.date_utils`.

### Gate 1 Verification
```
[ ] 017_ai_costs.sql applies cleanly — table and indexes created
[ ] AiCost model in models.py — CheckConstraint present, datetime.now(timezone.utc) used
[ ] ai_costs_repo.py — create(), get_filtered(), get_summary() implemented
[ ] migrate_backfill_ai_costs.py — runs, prints inserted/skipped summary
[ ] datetime.utcnow audit hits all resolved — grep returns empty
[ ] date_utils.py — both functions present with full docstrings
[ ] python -m pytest tests/ — baseline count, 0 failures
```

```bash
git add -A
git commit -m "feat(cost-tracking): Gate 1 — 017 migration, AiCost model, \
ai_costs_repo, backfill script, datetime sweep (Item 13), date_utils"
```

---

## Gate 2 — Persistence Injection + Provider Wiring Fix

**Background (v1.4 addition):**
During Gate 0/1 review a systemic provider wiring gap was identified:
`ProviderManager._load_config()` has been a stub since Phase 4 — its body is `pass`.
`ai_settings.json` is never read. Claude is hardcoded as the default throughout the
pipeline regardless of config. This gate fixes the full chain: the config loader, the
report generator's per-report provider override, the note condenser's direct Claude
dependency, and the `providers list` display text.

The daemon narration path (`workmain/daemon/narration.py`) correctly passes
`report_type='daily_internal'` to `provider_manager.generate()` and will benefit
automatically once `_load_config()` is implemented. No changes needed there.

### 2a. `workmain/ai/note_condenser.py` (v1.7 → v1.8)

**Two changes in this file:**

**Persistence injection** — after `self.session.commit()` (~line 159):

```python
from workmain.database.repositories.ai_costs_repo import AiCostRepository
AiCostRepository(self.session).create(
    interaction_type='condensation',
    provider=response.provider.value,
    model=response.model,
    prompt_tokens=response.prompt_tokens,
    completion_tokens=response.completion_tokens,
    cost_usd=response.cost,
    meeting_id=db_meeting.id,
    context_label=db_meeting.title,
)
```

**Provider wiring fix** — replace the hardcoded `self.claude` with the provider manager.

Remove:
```python
from workmain.ai.claude_client import get_claude_client
# and in __init__:
self.claude = get_claude_client()
```

Add to imports:
```python
from workmain.ai.provider_manager import get_provider_manager
from workmain.ai import get_claude_client, get_gemini_client
```

Add to `__init__`:
```python
self.provider_manager = get_provider_manager()
self.provider_manager.register_provider(ProviderType.CLAUDE, get_claude_client())
self.provider_manager.register_provider(ProviderType.GEMINI, get_gemini_client())
```

Replace the generation call (`self.claude.generate(request)`) with:
```python
provider_override = provider if provider else None
response, _ = self.provider_manager.generate(
    request,
    report_type='note_condensation',
    provider_override=provider_override,
)
```

This honours the `provider` parameter already present in `condense_meeting()` signature
and uses `note_condensation` config from `ai_settings.json` when no override is given.

### 2b. `workmain/ai/report_generator.py` (v1.10 → v1.11)

**Two changes in this file:**

**Persistence injection** — immediately after `db_report = self.reports_repo.create(...)`
(~line 255):

```python
from workmain.database.repositories.ai_costs_repo import AiCostRepository
AiCostRepository(self.session).create(
    interaction_type='report',
    provider=response.provider.value,
    model=response.model,
    prompt_tokens=response.prompt_tokens,
    completion_tokens=response.completion_tokens,
    cost_usd=response.cost,
    generation_time_s=generation_time,
    report_id=db_report.id,
    context_label=template_name,
)
```

**Provider wiring fix** — remove the template-metadata provider resolution block in
`generate_report()` (and the equivalent in `generate_section()` if present):

Remove:
```python
if provider is None:
    # Get from template metadata
    metadata = template.get("metadata", {})
    provider_name = metadata.get("ai_provider", "claude")
    provider = ProviderType.CLAUDE if provider_name == "claude" else ProviderType.GEMINI
```

When `provider` is None (no CLI `--provider` flag), `provider_override=None` flows
through to `provider_manager.generate()`, which then looks up the `report_type` config
loaded from `ai_settings.json`. When a CLI override is passed, it still works as before.

The `provider_override=provider` call at `self.provider_manager.generate(...)` is
unchanged — it correctly passes None or the explicit type.

### 2c. `workmain/ai/provider_manager.py` (v1.0 → v1.1)

**Implement `_load_config()`** and fix the `__init__` guard that prevented it from being
called without an explicit `config_path`.

**Fix `__init__`** — change:
```python
if config_path:
    self._load_config()
```
to:
```python
self._load_config()
```
`_load_config()` handles the missing-file case gracefully (returns early if file not found).

**Implement `_load_config()`:**
```python
def _load_config(self):
    """Load provider and report-type configuration from ai_settings.json."""
    import json
    from pathlib import Path

    config_file = self.config_path or str(
        Path(__file__).parent.parent.parent / 'config' / 'ai_settings.json'
    )

    if not Path(config_file).exists():
        return

    with open(config_file, 'r') as f:
        config = json.load(f)

    provider_map = {
        'claude': ProviderType.CLAUDE,
        'gemini': ProviderType.GEMINI,
    }
    fallback_mode_map = {
        'auto':   FallbackMode.AUTO,
        'manual': FallbackMode.MANUAL,
    }

    for report_type, cfg in config.get('report_types', {}).items():
        primary   = provider_map.get(cfg.get('primary_provider',  'claude'), ProviderType.CLAUDE)
        fallback  = provider_map.get(cfg.get('fallback_provider', 'gemini'), ProviderType.GEMINI)
        fb_mode   = fallback_mode_map.get(cfg.get('fallback_mode', 'auto'), FallbackMode.AUTO)
        max_cost  = cfg.get('max_cost_per_report', 1.0)

        self.configure_report_type(
            report_type=report_type,
            primary_provider=primary,
            fallback_provider=fallback,
            fallback_mode=fb_mode,
            max_cost=max_cost,
        )
```

The singleton `_provider_manager_instance` is reset to None on process start, so each
process reads the config once at first `get_provider_manager()` call. Config changes
require a process restart (acceptable for a CLI tool).

### 2d. `workmain/cli/commands/providers.py` (v1.10 → v1.11)

Fix the `providers list` command's hardcoded display text. Replace:

```python
console.print("  Daily Internal Report  → Claude")
console.print("  Weekly Client Report   → Gemini")
console.print("  Note Condensation      → Claude")
```

With a dynamic lookup from the provider manager config:

```python
from workmain.ai.provider_manager import get_provider_manager

pm = get_provider_manager()
report_types = [
    ('Daily Internal Report', 'daily_internal'),
    ('Weekly Client Report',  'weekly_client'),
    ('Note Condensation',     'note_condensation'),
]
console.print("[bold]Provider Assignments (from ai_settings.json):[/bold]")
for label, rt in report_types:
    cfg = pm.get_report_config(rt)
    if cfg:
        primary = cfg.primary_provider.value.title()
        fallback = cfg.fallback_provider.value.title() if cfg.fallback_provider else "none"
        console.print(f"  {label:<26} → {primary} (fallback: {fallback})")
    else:
        console.print(f"  {label:<26} → [dim]not configured[/dim]")
```

The providers must be registered before `get_provider_manager()` is called in the list
command, or the report configs will be loaded but providers will be absent from the
`_providers` dict. Register both at the top of the list command function:

```python
from workmain.ai import get_claude_client, get_gemini_client
from workmain.ai.base_provider import ProviderType

pm = get_provider_manager()
pm.register_provider(ProviderType.CLAUDE, get_claude_client())
pm.register_provider(ProviderType.GEMINI, get_gemini_client())
```

Note: `get_report_config()` does not require registered providers — it reads
`_report_configs` only. The provider registration is only needed if `providers list`
also shows availability status (which it does via the table above).

### Gate 2 Verification
```
[ ] note_condenser.py — ai_costs row created after condensation; version bumped to v1.8
[ ] note_condenser.py — condensation uses provider_manager.generate('note_condensation')
[ ] report_generator.py — ai_costs row created after report save; version bumped to v1.11
[ ] report_generator.py — template-metadata provider block removed; provider=None flows through
[ ] provider_manager.py — _load_config() implemented; version bumped to v1.1
[ ] provider_manager.py — __init__ guard removed; config loaded on every instantiation
[ ] providers.py — list command shows dynamic provider assignments; version bumped to v1.11
[ ] Manual: edit ai_settings.json daily_internal primary_provider → gemini
            run workmain reports save daily_internal
            verify ai_costs row shows provider='gemini'
            revert ai_settings.json
[ ] Manual: run workmain meetings condense <meeting>
            verify ai_costs row shows correct provider from config
[ ] Manual: workmain providers list — shows config-driven assignments, not hardcoded text
[ ] python -m pytest tests/ — baseline count, 0 failures
```

```bash
git add -A
git commit -m "feat(cost-tracking): Gate 2 — persistence injection in \
note_condenser and report_generator; fix provider wiring (_load_config, \
note_condenser hardcode, report_generator metadata override, providers list display)"
```

---

## Gate 3 — Display Swap

### Date filter flags (all costs commands)

All four costs commands share the same date filter options and precedence rules.
Use `resolve_date_window()` from `date_utils.py`; use `format_date_window_label()`
in the output header.

**Click option block (apply to every costs command):**

```python
@click.option('--date', '-d', default=None, metavar='YYYY-MM-DD',
              help='Show costs for a single date.')
@click.option('--start', '-b', default=None, metavar='YYYY-MM-DD',
              help='Range start date.')
@click.option('--end', '-e', default=None, metavar='YYYY-MM-DD',
              help='Range end date (requires --start; defaults to today if omitted).')
@click.option('--month', '-M', default=None, metavar='YYYY-MM',
              help='Calendar month window (default: current month).')
@click.option('--all', 'show_all', is_flag=True, default=False,
              help='All-time; overrides all date filters.')
```

**Resolution call (same in every costs command body):**

```python
from workmain.utils.date_utils import resolve_date_window, format_date_window_label

start_date, end_date = resolve_date_window(date, start, end, month, show_all)
window_label = format_date_window_label(start_date, end_date)
```

### 3a. Redesign `workmain providers costs` (`workmain/cli/commands/providers.py`)

**New role:** Provider-level aggregate — "how much am I spending across all AI operations?"

Source: `AiCostRepository.get_summary(start_date=start_date, end_date=end_date)`

Output (header reflects active window):
```
AI Cost Summary — May 2026

  Total API Calls:  42
  Total Cost:       $0.004218
  Total Tokens:     38,412

By Provider:
  Provider  | Calls | Cost       | Tokens  | Avg/Call
  Claude    |    35 | $0.003891  |  33,205 | $0.000111
  Gemini    |     7 | $0.000327  |   5,207 | $0.000047

By Interaction Type:
  Type          | Calls | Cost       | Tokens
  report        |    12 | $0.002841  |  26,100
  condensation  |    30 | $0.001377  |  12,312
```

Full filter set:
- `--date/-d`, `--start/-b`, `--end/-e`, `--month/-M`, `--all` (date filters — see above)
- `--provider/-P claude|gemini` — filter by provider

### 3b. Redesign `workmain reports costs` (`workmain/cli/commands/reports.py`)

**New role:** Per-report detail — "what does each individual report cost?"

Source: `ReportsRepository.list_reports(start_date=start_date, end_date=end_date, ...)`

**Important:** date filtering operates on `report_date` (the workday summarised), not
`created_at`. Gate 0 must confirm `list_reports()` supports this before Gate 3b proceeds.

Output:
```
Report Costs — May 2026  (15 reports, $0.002841 total)

  Date        | Type              | Provider | Tokens  | Cost
  2026-05-28  | daily_internal    | Claude   |  2,841  | $0.000312
  2026-05-27  | daily_internal    | Claude   |  2,719  | $0.000298
  ...
```

Full filter set:
- `--date/-d`, `--start/-b`, `--end/-e`, `--month/-M`, `--all` (date filters — see above)
- `--provider/-P claude|gemini`
- `--type/-t` — filter by report type (e.g. `daily_internal`, `weekly_client`)
- `--limit/-n` — cap rows shown

### Gate 3 Verification
```
[ ] providers costs — new aggregate layout renders; header shows window label
[ ] providers costs --all — full history shown
[ ] reports costs — per-report layout renders; header shows window label
[ ] reports costs --date 2026-05-28 — filters on report_date, not created_at
[ ] providers.py version bumped
[ ] reports.py version bumped
[ ] python -m pytest tests/ — baseline count, 0 failures
```

```bash
git add -A
git commit -m "feat(cost-tracking): Gate 3 — providers costs and reports costs redesign \
with date filters"
```

---

## Gate 4 — New Costs Subcommands

### 4a. `workmain notes costs` (`workmain/cli/commands/notes.py`)

Add `@notes.command('costs')`:

Source: `AiCostRepository.get_filtered(interaction_type=filter_type,
start_date=start_date, end_date=end_date, limit=limit)`

`filter_type` defaults to `'condensation'` when `--type` is not supplied.

**Note on scope:** Condensation is meeting-scoped; `notes costs` and `meetings costs`
show the same underlying data currently. `notes costs` will be the natural home for
per-note Ollama intent parsing costs in Phase 13.

Output:
```
Note / Condensation Costs — May 2026

  Total: 30 calls  $0.001377  12,312 tokens

  Date        | Mtg ID | Meeting                        | Provider | Tokens | Cost
  2026-05-27  |    142 | Security Weekly                | Claude   |    412 | $0.000045
  ...
```

Full filter set:
- `--date/-d`, `--start/-b`, `--end/-e`, `--month/-M`, `--all` (date filters — see above)
- `--limit/-n`
- `--type` (no short form) — interaction type filter; default `condensation`; accepts
  `condensation` or `intent_parse` (Phase 13). Short form assigned in CLI_STANDARDS.md
  §5.3 in Phase 13 when the flag becomes functional.

### 4b. `workmain meetings costs` (`workmain/cli/commands/meetings.py`)

Add `@meetings.command('costs')`:

Same data source, date filters, and `--type` behavior as 4a.

Output:
```
Meeting Condensation Costs — May 2026

  Total: 30 calls  $0.001377  12,312 tokens

  Date        | Mtg ID | Meeting                        | Provider | Tokens | Cost
  2026-05-27  |    142 | Security Weekly                | Claude   |    412 | $0.000045
  ...
```

Full filter set: identical to `notes costs` (4a above).

### Gate 4 Verification
```
[ ] notes costs renders; header shows window label
[ ] meetings costs renders; header shows window label
[ ] notes costs --type intent_parse — empty table, no error
[ ] notes.py version bumped
[ ] meetings.py version bumped
[ ] python -m pytest tests/ — baseline count, 0 failures
```

```bash
git add -A
git commit -m "feat(cost-tracking): Gate 4 — notes costs and meetings costs \
subcommands with date filters"
```

---

## Gate 5 — Tests + Version Bump + Merge

### New test file: `tests/test_ai_costs.py`

**Repository tests:**
- `AiCostRepository.create()` — round-trip with sentinel dates
- `AiCostRepository.create()` — rejects invalid `interaction_type` (CHECK constraint)
- `AiCostRepository.get_filtered()` — interaction_type, provider, date range filters
- `AiCostRepository.get_filtered(interaction_type='intent_parse')` — returns empty list
- `AiCostRepository.get_summary()` — by_provider / by_type aggregations

**Persistence tests:**
- Condensation: mock `condense_meeting()`, assert `ai_costs` row with correct `meeting_id`
- Report: mock `generate_report()`, assert `ai_costs` row with correct `report_id`
- Backfill: seed test reports with metadata, run backfill, verify row count

**Provider wiring tests (v1.4 addition):**
- `ProviderManager()` with no config_path loads `ai_settings.json` automatically
- `ProviderManager()` with missing config file does not raise — falls back to Claude
- After loading config, `get_provider_for_report('daily_internal')` returns the value
  from `ai_settings.json` (not hardcoded Claude)
- After loading config, `get_provider_for_report('note_condensation')` returns the
  value from `ai_settings.json`
- `NoteCondenser.condense_meeting()` calls `provider_manager.generate()`, not
  `claude_client.generate()` directly (mock/spy verification)

**date_utils tests:**
- `resolve_date_window(show_all=True)` → `(None, None)`
- `resolve_date_window(date_str='2026-05-15')` → `(date(2026,5,15), date(2026,5,15))`
- `resolve_date_window(start_str='2026-05-01')` → `(date(2026,5,1), date.today())`
- `resolve_date_window(start_str='2026-05-01', end_str='2026-05-15')`
  → `(date(2026,5,1), date(2026,5,15))`
- `resolve_date_window(month_str='2026-05')`
  → `(date(2026,5,1), date(2026,5,31))`
- Mutual exclusion: `--date` + `--start` → `UsageError`
- Mutual exclusion: `--date` + `--month` → `UsageError`
- Mutual exclusion: `--start` + `--month` → `UsageError`
- `--end` without `--start` → `UsageError`
- `format_date_window_label(None, None)` → `"All Time"`
- `format_date_window_label(date(2026,5,15), date(2026,5,15))` → `"2026-05-15"`
- `format_date_window_label(date(2026,5,1), date(2026,5,31))` → `"May 2026"`
- `format_date_window_label(date(2026,5,1), date(2026,5,15))`
  → `"2026-05-01 to 2026-05-15"`

**Deprecation test:**
- No `DeprecationWarning` on import of `models.py` and `gdrive_repository.py`

### Version bump and documentation files

- `workmain/__version__.py` — v1.16.1 → v1.17.0
- `CHANGELOG.md` — new [1.17.0] entry
- `docs/FEATURE_BACKLOG.md` — mark Item 13 COMPLETE (v1.17.0); version bump to v6.0
- `docs/CLI_STANDARDS.md` — v2.4 → v2.5; three §5.3 scope expansions:

| Short | Current scope | Updated scope |
|-------|--------------|---------------|
| `-b` | `time add`, `meetings create`, `clockify sync pull` | add: all costs commands |
| `-e` | `time add`, `meetings create` | add: all costs commands |
| `-M` | `providers costs` | expand to: all costs commands |

### Session handoff document

Create `SESSION_HANDOFF_COST_TRACKING_SPRINT_COMPLETE_<YYYYMMDD>.md` following the
established handoff format. Include:
- Sprint complete at v1.17.0
- Full test count (before and after)
- All new and modified files with versions
- Migration file name confirmed (017_ai_costs.sql)
- datetime.utcnow audit result — files fixed, Item 13 closed
- list_reports() audit result — params present / added
- Provider wiring fix summary: _load_config() implemented; note_condenser rerouted;
  report_generator template-metadata override removed; providers list display dynamic
- Next phase: Phase 13-1 (Ollama Foundation)
- Open items: Feature Backlog Items 32, 33, 34 (Phase 13 targets)

### Merge flow

```bash
git add -A
git commit -m "feat(cost-tracking): Gate 5 — tests, v1.17.0 bump, CHANGELOG, \
CLI_STANDARDS v2.5, FEATURE_BACKLOG Item 13 closed"

# Merge feature branch into dev
git checkout dev
git merge --no-ff feature/cost-tracking-persistence
git branch -d feature/cost-tracking-persistence

# Verify full suite on dev
python -m pytest tests/

# dev → main MUST go through a GitHub PR (per GIT_WORKFLOW_STANDARDS)
git push origin dev
gh pr create --base main --head dev --title "feat: Cost tracking persistence + provider wiring fix (v1.17.0)" --body "..."
# Merge on GitHub, then:
git checkout main
git pull origin main
git tag v1.17.0
git push --tags
```

### Gate 5 Verification
```
[ ] test_ai_costs.py — all cases pass
[ ] python -m pytest tests/ on main — 0 failures, new total recorded
[ ] __version__.py shows 1.17.0
[ ] CHANGELOG.md [1.17.0] entry present
[ ] FEATURE_BACKLOG.md Item 13 marked COMPLETE; version v6.0
[ ] CLI_STANDARDS.md v2.5; -b, -e, -M scope expansions confirmed
[ ] SESSION_HANDOFF_COST_TRACKING_SPRINT_COMPLETE_*.md exists
[ ] git tag v1.17.0 exists and pushed
[ ] feature/cost-tracking-persistence branch deleted
```

---

## Critical Files Summary

| File | Change |
|------|--------|
| `workmain/database/migrations/017_ai_costs.sql` | New — `CREATE TABLE ai_costs` with CHECK constraint and indexes |
| `workmain/database/models.py` | Add `AiCost` model with `CheckConstraint` + `datetime.now(timezone.utc)` |
| `workmain/database/repositories/ai_costs_repo.py` | New — `AiCostRepository` |
| `scripts/migrate_backfill_ai_costs.py` | New — backfill from `reports.metadata` (run after 017) |
| `workmain/database/repositories/gdrive_repository.py` | `datetime.utcnow` → `datetime.now(timezone.utc)` (Item 13) |
| `workmain/utils/date_utils.py` | New — `resolve_date_window()` + `format_date_window_label()` |
| `workmain/ai/provider_manager.py` | v1.0 → v1.1 — implement `_load_config()`; remove `if config_path:` guard |
| `workmain/ai/note_condenser.py` | v1.7 → v1.8 — inject persistence; replace `self.claude` with `provider_manager.generate('note_condensation')` |
| `workmain/ai/report_generator.py` | v1.10 → v1.11 — inject persistence; remove template-metadata provider override block |
| `workmain/cli/commands/providers.py` | v1.10 → v1.11 — redesign `providers costs`; fix `providers list` display; add date filters |
| `workmain/cli/commands/reports.py` | Redesign `reports costs`; add date filters |
| `workmain/cli/commands/notes.py` | Add `notes costs` with date filters + `--type` placeholder |
| `workmain/cli/commands/meetings.py` | Add `meetings costs` with date filters + `--type` placeholder |
| `tests/test_ai_costs.py` | New test file |
| `tests/test_ai_foundation.py` | v1.1 → v1.2 — fix brittle hard-coded provider assertions in test_config_structure |
| `workmain/__version__.py` | v1.16.1 → v1.17.0 |
| `CHANGELOG.md` | New [1.17.0] entry |
| `docs/FEATURE_BACKLOG.md` | Item 13 COMPLETE; version v6.0 |
| `docs/CLI_STANDARDS.md` | v2.4 → v2.5; §5.3 scope expansions for -b, -e, -M |

---

## Scope Items NOT in This Plan

1. **`config_manager/loader.py` dead code** — `get_default_provider_for_report()` method
   exists but is never called anywhere in the codebase. Not changed in this sprint;
   flagged for removal in the code quality phase (Phase 15 — CLI cleanup/refactor).

2. **Monthly trend table in `providers costs`** — a "last 3 months" row-per-month
   breakdown. Useful but adds complexity; follow-on sprint.

3. **`workmain eod costs`** — all AI costs for a specific EOD run. Requires a
   session/run context not currently tracked.

4. **`providers set default` CLI command** — remains a stub until Phase 14 (Setup
   Wizard). The underlying config is now respected via `_load_config()`; the CLI command
   is the UI to modify the config without hand-editing JSON.

---

## Constraints and Reminders

- Read all five Pre-Implementation documents before Gate 0. Do not skip.
- All CLI flags must be checked against `CLI_STANDARDS.md` §5.3 before assignment.
  The table is authoritative — do not assign a short form already listed for a different
  purpose.
- `--all`, `--force`, `--dry-run`, and `--status` have no short form. Do not add one.
- `datetime.utcnow` must not appear anywhere in new or modified code. Use
  `datetime.now(timezone.utc)`. The Gate 0 audit list is the minimum — fix every
  instance found, not just known ones.
- `lazy='dynamic'` is not permitted in SQLAlchemy relationships. Use `lazy='select'`
  or omit `lazy=` entirely.
- The dual-write approach in `report_generator.py` is intentional. `report_metadata`
  must not be removed — it is the source for `reports costs` and backward compat.
  Do not consolidate to `ai_costs` only.
- `resolve_date_window()` is the single source of truth for date filter resolution.
  Do not implement independent date logic in any individual costs command.
- Date filtering on `reports costs` operates on `report_date` (the workday covered),
  not `created_at`. Date filtering on all other costs commands operates on `created_at`.
  This is intentional — do not normalise.
- Gate 0 findings (list_reports() audit, datetime audit) must be reported before any
  Gates 1+ code is written.
- Version bumps follow minor increment rules (feature = minor bump). This sprint is
  v1.16.1 → v1.17.0. Do not deviate without explicit justification.
- Delete the feature branch after merging to dev. Branches are scaffolding; tags are
  the permanent record.
- `provider_manager._load_config()` reads config at instantiation time. The singleton
  pattern means config is read once per process. Config changes take effect on next
  CLI invocation (acceptable for a CLI tool — no daemon restart needed).
- The `providers set default` CLI stub remains unchanged — it is a Phase 14 deliverable.
  Do not implement it here.

---

## Summary — Gate Completion Checklist

| Gate | Deliverable | Status |
|------|-------------|--------|
| 0 | Branch setup, test baseline, migration number, list_reports() audit, utcnow audit | ✓ COMPLETE |
| 1 | 017_ai_costs.sql, AiCost model, ai_costs_repo, backfill script, datetime sweep, date_utils | ✓ COMPLETE |
| 2 | Persistence injection + provider wiring fix (_load_config, note_condenser, report_generator, providers list) | [ ] |
| 3 | providers costs and reports costs redesigned with date filters | [ ] |
| 4 | notes costs and meetings costs subcommands with date filters | [ ] |
| 5 | Tests, v1.17.0 bump, CHANGELOG, CLI_STANDARDS v2.5, FEATURE_BACKLOG, merge | [ ] |

---

## Verification

```bash
# 1. Run schema migration
psql -U workmain_user -d workmain -f workmain/database/migrations/017_ai_costs.sql

# 2. Run backfill script
python scripts/migrate_backfill_ai_costs.py

# 3. Verify backfill populated ai_costs from existing reports
workmain providers costs --all

# 4. Confirm no datetime.utcnow deprecation warnings
python -W error::DeprecationWarning -c "from workmain.integrations.gdrive import gdrive_repository"
python -W error::DeprecationWarning -c "from workmain.database import models"

# 5. Provider wiring smoke test — edit ai_settings.json to set daily_internal primary = gemini,
#    generate a report, verify ai_costs shows gemini, then revert
workmain reports save daily_internal
workmain providers costs

# 6. Run a condensation — should persist to ai_costs using config provider
workmain meetings condense <meeting>
workmain meetings costs

# 7. Verify providers list shows config-driven assignments
workmain providers list

# 8. Generate a report — should double-write
workmain reports save daily_internal
workmain providers costs
workmain reports costs

# 9. Date filter smoke tests (all four commands)
workmain providers costs --date 2026-05-28
workmain providers costs --start 2026-05-01 --end 2026-05-28
workmain providers costs --start 2026-05-01
workmain providers costs --month 2026-05
workmain providers costs --all
workmain reports costs --date 2026-05-28
workmain reports costs --start 2026-05-01 --end 2026-05-28
workmain notes costs --date 2026-05-28
workmain meetings costs --start 2026-05-01

# 10. Mutual exclusion error cases — each must print UsageError, not a traceback
workmain providers costs --date 2026-05-28 --start 2026-05-01
workmain providers costs --date 2026-05-28 --month 2026-05
workmain providers costs --start 2026-05-01 --month 2026-05
workmain providers costs --end 2026-05-28

# 11. --type smoke tests
workmain notes costs --type condensation
workmain notes costs --type intent_parse
workmain meetings costs --type intent_parse

# 12. Full test suite on main
python -m pytest tests/
```

---

END OF SPEC
WorkmAIn FEATURE_SPEC_COST_TRACKING_PERSISTENCE — v1.4 — 20260528
