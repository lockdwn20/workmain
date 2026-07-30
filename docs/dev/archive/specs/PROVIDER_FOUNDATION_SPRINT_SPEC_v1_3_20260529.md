WorkmAIn
Provider Foundation Sprint Specification v1.3
20260529

---

**Version History:**
- v1.0 (20260529): Initial specification
- v1.1 (20260529): Claude Code review incorporated — 5 blocking issues, 5 design
  gaps, 4 minor items resolved
- v1.2 (20260529): Second Claude Code review — N1 (generate()/\_get\_provider() type
  mismatch), N2 (workmain/ai/\_\_init\_\_.py missing from Modified Files), ProviderConfig
  TODO/backlog observation resolved
- v1.3 (20260529): Third Claude Code review — 2 editorial items resolved:
  E1: Duplicate "Step 5" label in Gate 0 renumbered — steps now 1–8 sequentially
  E2: Explicit note added to Gate 1f — any except KeyError blocks guarding
      _get_provider() calls must be updated to catch ProviderUnavailableError;
      dead code path (check_provider_status/get_all_provider_statuses) noted with
      remove-if-dead instruction
  N1: generate() / _get_provider() type mismatch — generate() updated to call
      get_provider(primary.value); _get_provider() explicitly retired; Gate 0
      expanded to audit all internal callers; Gate 1f language corrected from
      "preserved unchanged" to "preserved in behavior, updated to string-keyed lookup"
  N2: workmain/ai/__init__.py added to Modified Files; Gate 0 audit step added for
      get_claude_client/get_gemini_client exports and codebase callers
  Observation: ProviderConfig TODO comment added to Gate 1a; FEATURE_BACKLOG item
      logged in Gate 5 for ProviderConfig dead code cleanup
  B1: ProviderUnavailableError added to base_provider.py (new subclass of ProviderError)
  B2: OllamaProvider stub corrected — all 5 abstract methods stubbed with correct
      signatures; generate() takes GenerationRequest, returns GenerationResponse
  B3: BaseProvider.__init__ updated to accept dict; ProviderConfig migration addressed
  B4: test_connection() added as default method to BaseProvider wrapping check_availability()
  B5: get_config_for_type() → get_report_config(); enum .value/.name handling for display
  D1: providers set default wired into providers_set group (@providers_set.command('default'))
  D2: providers config show uses providers_config subgroup consistently
  D3: ProviderType.OLLAMA added to enum; enum kept throughout
  D4: cost_structure added to all provider sections in ai_settings.json; providers list reads from config
  D5: "Changes take effect on next CLI invocation." added to set default output
  M1: Model fallback constant verified at Gate 0; future changes are config-only post-Item 35
  M2: providers set default write also updates last_updated field
  M3: click.Choice dropped for provider arguments — dynamic runtime validation against registry
  M4: Provider Assignments section kept in providers list; providers config show is full detail view
  base_provider.py added to Modified Files (was missing from v1.0)

---

## Context

Three related problems surfaced during the cost tracking sprint that must be resolved
before Phase 13 can introduce Ollama as a third provider:

1. `ProviderManager._load_config()` was a dead stub since Phase 4. Fixed in v1.17.0 —
   provider routing now works. But the rest of the provider layer was written assuming
   only Claude and Gemini ever exist, making adding a third provider require structural
   surgery rather than config.

2. `claude_client.py` and `gemini_client.py` are monolithic files with hardcoded model
   strings. `ai_settings.json` has a `model` field under each provider that is never
   read (Item 35). Model updates require Python file edits.

3. Display text, CLI help strings, and AI system prompts contain hardcoded "Claude"
   references. With Gemini now actively routing real traffic (confirmed by `notes costs`
   showing Gemini while UI says "Sending to Claude..."), this is a live accuracy bug,
   not future polish.

This sprint delivers: (a) `base_provider.py` extended with `ProviderUnavailableError`,
`ProviderType.OLLAMA`, dict-based `__init__`, and `test_connection()`; (b) an N-provider
extensible registry so adding a provider is one new file + one config section; (c) Ollama
stubbed as a disabled placeholder ready for Phase 13-1 activation; (d) config-driven
model selection closing Item 35; (e) full hardcoded reference sweep; (f) `providers set
default` finally implemented; and (g) dynamic provider validation replacing hardcoded
`click.Choice` lists.

**Branch:** `feature/provider-foundation` from `dev`
**Version bump:** v1.17.0 → v1.18.0
**Closes backlog items:** 10, 11, 35

---

## Pre-Implementation Reading (Claude Code)

Before writing any code, read in this order:

1. `CLAUDE.md` — session pattern, file versioning rules, commit format
2. `docs/CLI_STANDARDS.md` v2.5 — command naming, flag short-forms, violation register
3. `docs/TESTING_STANDARDS.md` — db_session fixture, sentinel dates, test file template
4. `docs/GIT_WORKFLOW_STANDARDS.md` — branch strategy, version bump rules, merge cadence
5. This spec — gate by gate

Do not begin Gate 0 until all five documents are read.

---

## Locked Architectural Decisions

| # | Decision |
|---|----------|
| 1 | `base_provider.py` lives at `workmain/ai/base_provider.py` permanently. It is the contract definition — not a provider implementation — and belongs at the layer that owns the abstraction, not inside the implementations subpackage. |
| 2 | Provider implementations live in `workmain/ai/providers/` — one file per provider. |
| 3 | `PROVIDER_REGISTRY` in `workmain/ai/providers/__init__.py` is the single registration point. Adding a provider = one registry entry + one `ai_settings.json` section. |
| 4 | `ProviderManager` instantiates providers from registry only. No hardcoded provider names inside `ProviderManager`. |
| 5 | Three provider status states: `disabled` (enabled=false in config — skip connectivity check entirely), `available` (enabled, connectivity passes), `unavailable` (enabled, connectivity fails). |
| 6 | `providers set default` uses read-modify-write. It reads `ai_settings.json`, updates only the targeted field(s) plus `last_updated`, and writes back. It never overwrites the entire file. |
| 7 | `ai_settings.json` remains directly user-editable. The CLI command is a convenience wrapper, not the gatekeeper. Both paths are equally valid. |
| 8 | `claude_client.py` and `gemini_client.py` are deleted. Content migrates to `providers/claude.py` and `providers/gemini.py`. No backwards-compat shims. |
| 9 | System prompt changes are minimal-scope: identity statements removed, role language substituted. No prompt quality improvements in this sprint. |
| 10 | `OllamaProvider` is a clean stub — ABC-compliant, all abstract methods present. `enabled: false` in config means ProviderManager never instantiates it. If invoked directly it raises `ProviderUnavailableError`. Phase 13-1 implements the body. |
| 11 | Provider arguments in CLI commands (`providers test`, `--provider` flags) use dynamic runtime validation against the registry. No `click.Choice` hardcoding — adding a provider to the registry makes it automatically valid in all commands. |
| 12 | `ProviderType` enum is retained and extended with `OLLAMA`. String-keyed registry maps to enum values internally via `ProviderType(name)`. |

---

## New Files

| File | Purpose |
|------|---------|
| `workmain/ai/providers/__init__.py` | Provider registry dict — single registration point |
| `workmain/ai/providers/claude.py` | Claude provider — config-driven, migrated from claude_client.py |
| `workmain/ai/providers/gemini.py` | Gemini provider — config-driven, migrated from gemini_client.py |
| `workmain/ai/providers/ollama.py` | Ollama stub — ABC-compliant placeholder for Phase 13-1 |
| `docs/ai_settings_guide.md` | Annotated schema documentation for `ai_settings.json` |
| `tests/test_provider_foundation.py` | Registry, config-driven model, status states, dynamic validation |

## Deleted Files

| File | Replaced By |
|------|-------------|
| `workmain/ai/claude_client.py` | `workmain/ai/providers/claude.py` |
| `workmain/ai/gemini_client.py` | `workmain/ai/providers/gemini.py` |

## Modified Files

| File | Change |
|------|--------|
| `workmain/ai/base_provider.py` | Add `ProviderUnavailableError`; add `ProviderType.OLLAMA`; `__init__` accepts dict; add `test_connection()` default method |
| `workmain/ai/__init__.py` | Remove `get_claude_client` / `get_gemini_client` exports; update re-exports to use `providers/` subpackage |
| `workmain/ai/provider_manager.py` | Registry-based factory; disabled tracking; N-provider support; `generate()` string-keyed lookup; `_get_provider()` removed |
| `workmain/ai/prompt_builder.py` | Identity language removed from system prompts |
| `workmain/ai/note_condenser.py` | Identity language removed; "Sending to..." display made dynamic |
| `workmain/ai/report_generator.py` | Any hardcoded provider references swept |
| `workmain/cli/commands/providers.py` | `set default` implemented; `config show` added; disabled status; model column; dynamic provider validation |
| `config/ai_settings.json` | Ollama section added; `cost_structure` in all provider sections |
| `tests/test_ai_foundation.py` | Updated for new import paths; extended for registry |
| `workmain/__version__.py` | v1.17.0 → v1.18.0 |
| `CHANGELOG.md` | New [1.18.0] entry |
| `docs/FEATURE_BACKLOG.md` | Items 10, 11, 35 marked COMPLETE |
| `docs/CLI_STANDARDS.md` | `providers set default`, `providers config show` registered; dynamic provider arg documented |

---

## Gate 0 — Audit and Branch Setup

### Objective

Establish the feature branch, record the test baseline, and complete the audit that
drives scope decisions for Gates 1–4. No implementation begins until audit findings
are documented.

### Steps

**1. Create feature branch:**
```bash
git checkout dev
git pull origin dev
git checkout -b feature/provider-foundation
```

**2. Verify test baseline:**
```bash
python -m pytest tests/ -v
```
Record the passing count. Expected: 443 passed, 0 failed.

**3. Audit `base_provider.py` — this drives Gate 1a entirely:**

Inspect `workmain/ai/base_provider.py`. Record:
- Exact `@abstractmethod` signatures for all five: `generate()`, `estimate_cost()`,
  `validate_config()`, `count_tokens()`, `check_availability()`
- `__init__` current signature and all attributes it initializes (`_status`,
  `_last_error`, `config`, and any others)
- `ProviderConfig` dataclass fields — what it currently holds
- `ProviderType` enum current values
- `ProviderStatus` enum values (needed for `check_availability()` return type)
- `ProviderError` class hierarchy — confirm it is the base exception class
- Whether `ProviderUnavailableError` already exists (expected: no)
- Whether `test_connection()` already exists (expected: no)

The OllamaProvider stub in Gate 1e must match the exact signatures found here.

**4. Audit `ProviderManager` and `providers.py`:**

Inspect `workmain/ai/provider_manager.py` v1.1 and
`workmain/cli/commands/providers.py`. Record:
- How Claude and Gemini are currently instantiated (direct import or via config key)
- Exact method name for report config lookup — confirm whether it is
  `get_report_config()` or something else; confirm return type
- `ReportTypeConfig` structure — whether `primary_provider` is `ProviderType` enum
  or string; this determines the `.value` vs `.name` call in Gate 3b
- Where `get_provider_manager()` singleton is defined and how it is cached
- Whether `CostTracker` (`cost_tracker.py`) is still actively called post-v1.17.0 or
  whether it is dead code. Do not remove it in this sprint — log a new
  FEATURE_BACKLOG item if dead.
- The connectivity check location: `providers.py` CLI or `ProviderManager`
- The exact group variable name for the `providers set` group (e.g. `providers_set`)
- Whether a `providers_config` group already exists or needs to be created
- Current `click.Choice` provider lists in `providers test` and `providers costs
  --provider` — confirm file/line numbers
- **`_get_provider()` internal callers:** find every call to `_get_provider()` inside
  `provider_manager.py` (expected: `generate()` and possibly fallback logic). Record
  all callers — Gate 1f must update every one. `_get_provider()` is removed in Gate 1f.
- **Current `_providers` dict key type:** confirm whether it is currently keyed by
  `ProviderType` enum or string. This determines the conversion pattern in Gate 1f.

**5. Audit `workmain/ai/__init__.py` exports:**

Inspect `workmain/ai/__init__.py`. Record:
- Whether `get_claude_client` and `get_gemini_client` are exported
- Every file in the codebase that imports from `workmain.ai` using these names:
  ```bash
  grep -rn "get_claude_client\|get_gemini_client\|from workmain.ai import" \
    workmain/ --include="*.py"
  ```
- Whether `note_condenser.py` v1.8 still uses these imports or routes exclusively
  through `ProviderManager`. If the imports are dead code post-v1.17.0, note this
  explicitly — Gate 1 will clean up proactively rather than reactively.
- Any other exports in `__init__.py` that reference `claude_client` or `gemini_client`
  by module path (will break when those files are deleted in Gate 1h)

**6. Verify `ai_settings.json` schema:**

Inspect `config/ai_settings.json`. Record:
- Exact top-level keys and structure
- All fields in each provider section (confirm `model` field exists)
- Whether `cost_structure` field exists in any provider section (expected: no)
- Whether `last_updated` field exists at top level (expected: yes — v1.1 will write to it)
- Current `report_types` section structure

**7. Hardcoded reference audit — four categories:**

```bash
# Category A — System prompts (AI instruction text sent to LLM)
grep -rn "Claude\|Anthropic\|claude-sonnet\|claude-haiku" \
  workmain/ai/prompt_builder.py workmain/ai/note_condenser.py \
  workmain/ai/report_generator.py

# Category B — CLI status messages shown to user
grep -rn "Sending to\|Using Claude\|Using Gemini" \
  workmain/cli/commands/ --include="*.py"

# Category C — Click help= strings
grep -rn 'help=.*[Cc]laude\|help=.*[Gg]emini' workmain/ --include="*.py"

# Category D — Rich output labels, panel headers, table headers
grep -rn '"Claude"\|"Gemini"\|Panel.*Claude\|Panel.*Gemini' \
  workmain/ --include="*.py"
```

For each hit: file, line number, category, severity (A=highest). The Gate 3 hit list
is derived directly from this output.

**8. Verify model fallback constants:**

In `claude_client.py`, find the hardcoded model string. This becomes the Gate 2
fallback constant for `ClaudeProvider`. Same for `gemini_client.py`. Record both —
these must exactly match what is currently hardcoded, not what the spec assumed.

### Gate 0 Verification
```
[ ] feature/provider-foundation branch created from dev
[ ] Test baseline recorded (443 passed, 0 failed — or actual if different)
[ ] base_provider.py audit complete — all 5 abstractmethod signatures recorded;
    __init__ attrs recorded; exception hierarchy confirmed; ProviderType enum recorded
[ ] provider_manager.py audit complete — instantiation path, method names, singleton,
    _get_provider() all callers recorded, _providers current key type confirmed
[ ] providers.py audit complete — group var names, click.Choice locations
[ ] workmain/ai/__init__.py audit complete — exports recorded; codebase callers of
    get_claude_client/get_gemini_client found; dead code status noted
[ ] ai_settings.json schema documented — all fields, last_updated presence confirmed
[ ] Hardcoded reference audit complete — all four categories, all hits listed by file/line
[ ] Model fallback constants recorded from claude_client.py and gemini_client.py
[ ] CostTracker usage confirmed (active or dead — note in summary)
```

```bash
git add -A
git commit -m "feat(provider-foundation): Gate 0 — audit complete, branch established"
```

---

## Gate 1 — base_provider.py + N-Provider Extensible Registry

### Objective

Update `base_provider.py` with the four targeted additions, create the `providers/`
subpackage, refactor `ProviderManager`, and delete the old client files.

`base_provider.py` must be updated before the subpackage is created — the new provider
files import from it.

### 1a. `workmain/ai/base_provider.py` — targeted updates (version bump)

Four additions based on Gate 0 audit findings. Make no other changes.

**Addition 1 — `ProviderType.OLLAMA`:**
Add to the `ProviderType` enum:
```python
OLLAMA = 'ollama'
```

**Addition 2 — `ProviderUnavailableError`:**
Add after existing exception classes:
```python
class ProviderUnavailableError(ProviderError):
    """Raised when a provider is disabled in config or not registered.
    Distinct from ProviderError (connectivity/API failures) — this indicates
    the provider has not been enabled, not that it failed."""
    pass
```

**Addition 3 — `BaseProvider.__init__` accepts dict:**
Update the signature to accept a plain dict rather than a `ProviderConfig` dataclass.
Preserve all existing attribute initialization exactly as found at Gate 0.

```python
def __init__(self, config: dict):
    """Initialize provider with config dict from ai_settings.json section.

    Accepts raw dict to support N-provider extensibility. Each provider reads
    its own required fields via config.get(). Previously accepted ProviderConfig
    dataclass — changed in v1.18.0 Provider Foundation Sprint.
    """
    self.config = config
    # Preserve all attrs the current __init__ sets — verify at Gate 0
    # e.g. self._status = None; self._last_error = None; etc.
```

**Addition 4 — `test_connection()` default method:**
Add after `check_availability()` abstract method:
```python
def test_connection(self) -> bool:
    """Check if provider is reachable. Default wraps check_availability().
    Subclasses may override for a simpler boolean check.
    Returns True if available, False otherwise."""
    try:
        return self.check_availability() == ProviderStatus.AVAILABLE
    except Exception:
        return False
```

**`ProviderConfig` TODO comment:**
`ProviderConfig` becomes dead code in this sprint — its only consumers were
`claude_client.py` and `gemini_client.py`, both of which are deleted. Do not remove
the class (out of scope — spec says "make no other changes"). Add this comment
directly above the `ProviderConfig` class definition:

```python
# TODO (v1.18.0 Provider Foundation Sprint): ProviderConfig is unused.
# claude_client.py and gemini_client.py (its only consumers) were deleted.
# Remove this class when base_provider.py is next modified.
# Tracked: FEATURE_BACKLOG Item <N> — see Gate 5.
```

The backlog item number will be filled in at Gate 5 when the item is logged.

### 1b. `workmain/ai/providers/__init__.py` (new)

```python
"""
WorkmAIn
AI Provider Registry v1.0
20260529

Single registration point for all AI provider implementations.
To add a new provider:
  1. Create workmain/ai/providers/<name>.py implementing BaseProvider
  2. Import and add one line to PROVIDER_REGISTRY below
  3. Add a section to config/ai_settings.json
  That is all. ProviderManager, providers list, and all CLI validation
  update automatically.
"""
from .claude import ClaudeProvider
from .gemini import GeminiProvider
from .ollama import OllamaProvider

PROVIDER_REGISTRY = {
    'claude': ClaudeProvider,
    'gemini': GeminiProvider,
    'ollama': OllamaProvider,
}
```

### 1c. `workmain/ai/providers/claude.py` (new — migrated from `claude_client.py`)

Migrate all content from `claude_client.py` into `ClaudeProvider`. Key requirements:
- `__init__(self, config: dict)` — calls `super().__init__(config)`; reads
  `self.model = config.get('model', <fallback from Gate 0>)`
- All existing methods preserved with identical signatures and logic
- All imports updated (no import of `claude_client` or `ProviderConfig`)
- Version: v2.0 (major — new location, config-driven interface)

File header:
```
Migrated from workmain/ai/claude_client.py v<N>.
Receives config dict from ProviderManager via PROVIDER_REGISTRY.
Do not instantiate directly — use get_provider_manager().get_provider('claude').
```

### 1d. `workmain/ai/providers/gemini.py` (new — migrated from `gemini_client.py`)

Same pattern as 1c. Migrated from `gemini_client.py`. Version: v2.0.
Fallback model constant from Gate 0 audit — use exact string found in `gemini_client.py`.

### 1e. `workmain/ai/providers/ollama.py` (new — ABC-compliant stub)

All five abstract methods implemented as stubs with exact signatures from Gate 0 audit.
`generate()` raises `ProviderUnavailableError`. Others return safe neutral values.

```python
"""
WorkmAIn
Ollama Provider — Phase 13-1 Stub v1.0
20260529

ABC-compliant placeholder. All abstract methods present; generate() raises
ProviderUnavailableError until Phase 13-1 implements the body.

Phase 13-1 activation checklist:
  1. Set enabled: true in config/ai_settings.json providers.ollama
  2. Set host/port to your Proxmox Ollama instance
  3. Implement generate() body — Ollama REST API: POST host:port/api/generate
  4. Implement check_availability() health check (GET host:port/api/tags)
  5. Extend ai_costs CHECK constraint: add 'intent_parse' to valid types
  6. Update ProviderType usage where intent_parse costs are written
"""
from workmain.ai.base_provider import (
    BaseProvider, ProviderUnavailableError, ProviderStatus,
    GenerationRequest, GenerationResponse  # exact names verified at Gate 0
)


class OllamaProvider(BaseProvider):
    """Ollama local inference provider. Phase 13-1 stub."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.model = config.get('model', 'mistral-7b')
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 11434)
        self._base_url = f"http://{self.host}:{self.port}"

    # --- Abstract method stubs (exact signatures from Gate 0 audit) ---

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Phase 13-1 implements this. Raises until then."""
        raise ProviderUnavailableError(
            "Ollama provider is not yet implemented. "
            "Full implementation arrives in Phase 13-1. "
            "See Phase 13-1 activation checklist in this file's docstring."
        )

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Ollama is local — no API cost."""
        return 0.0

    def validate_config(self) -> bool:
        """Returns True if host and port are configured."""
        return bool(self.host and self.port)

    def count_tokens(self, text: str) -> int:
        """Approximate token count until Phase 13-1 wires Ollama tokenizer."""
        return len(text.split())

    def check_availability(self) -> ProviderStatus:
        """Phase 13-1 implements GET host:port/api/tags health check."""
        return ProviderStatus.UNAVAILABLE

    def test_connection(self) -> bool:
        """Phase 13-1 implements real check. Returns False until then."""
        return False

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def display_name(self) -> str:
        return "Ollama"

    @property
    def cost_structure(self) -> str:
        return "Local — no API cost"
```

**Note:** Replace `GenerationRequest`, `GenerationResponse`, `ProviderStatus` with the
exact class/enum names confirmed at Gate 0. The stub method bodies are correct regardless
of class name variations.

### 1f. `workmain/ai/provider_manager.py` — Registry-based refactor

```python
from workmain.ai.providers import PROVIDER_REGISTRY
from workmain.ai.base_provider import ProviderUnavailableError

class ProviderManager:
    def __init__(self):
        self._providers: dict = {}      # name → instantiated provider
        self._disabled: set = set()     # names of disabled providers
        self._all_configs: dict = {}    # name → config dict (all, for providers list)
        self._settings: dict = {}       # full ai_settings.json
        self._load_config()

    def _load_config(self):
        # Read ai_settings.json — preserve existing read logic
        for name, config in self._settings.get('providers', {}).items():
            self._all_configs[name] = config
            if not config.get('enabled', True):
                self._disabled.add(name)
                continue
            cls = PROVIDER_REGISTRY.get(name)
            if cls:
                self._providers[name] = cls(config)

    def get_provider(self, name: str):
        if name in self._disabled:
            raise ProviderUnavailableError(
                f"Provider '{name}' is disabled. "
                f"Set 'enabled: true' in config/ai_settings.json to enable it."
            )
        if name not in self._providers:
            raise ProviderUnavailableError(
                f"Provider '{name}' is not registered. "
                f"Add it to PROVIDER_REGISTRY and config/ai_settings.json."
            )
        return self._providers[name]

    def get_all_provider_configs(self) -> dict:
        """Returns config dict for ALL providers including disabled.
        Used by providers list to display complete provider table."""
        return self._all_configs

    def get_registered_provider_names(self) -> list:
        """Returns list of all provider names in registry.
        Used for dynamic CLI validation."""
        return list(PROVIDER_REGISTRY.keys())

    def is_disabled(self, name: str) -> bool:
        return name in self._disabled
```

**`generate()` — preserved in behavior, updated to string-keyed lookup:**

`generate()` cannot be left fully unchanged because `_providers` is now string-keyed
(`'claude'`, `'gemini'`, `'ollama'`) while `ReportTypeConfig.primary_provider` is a
`ProviderType` enum. Every call that previously passed a `ProviderType` enum to
`_get_provider()` must be updated to pass `provider_type.value` to `get_provider()`.

Using all `_get_provider()` call sites recorded at Gate 0, apply this update:

```python
# Before (enum-keyed, _get_provider):
provider = self._get_provider(report_config.primary_provider)

# After (string-keyed, get_provider):
provider = self.get_provider(report_config.primary_provider.value)
```

Apply to every call site found at Gate 0 — primary provider lookup, fallback provider
lookup, and any other internal uses. The behavior is identical; only the lookup
mechanism changes.

**`_get_provider()` — retired:**

Remove `_get_provider()` entirely after updating all call sites. It is fully replaced
by the public `get_provider(name: str)` which adds disabled-check and better error
messages. Confirm no remaining references with:
```bash
grep -n "_get_provider" workmain/ai/provider_manager.py
# Must return empty
```

**Exception type update — `KeyError` → `ProviderUnavailableError`:**

Any existing `except KeyError` blocks that were guarding `_get_provider()` calls
(e.g. in `check_provider_status()`, `get_all_provider_statuses()`, or similar) must
be updated to catch `ProviderUnavailableError` instead. `get_provider()` raises
`ProviderUnavailableError`, not `KeyError`. The Gate 0 caller audit will surface
all affected sites — update every `except KeyError` found guarding a provider lookup.

Note: Gate 0 may confirm that `check_provider_status()` and `get_all_provider_statuses()`
are dead code post-v1.17.0 (providers list likely calls clients directly). If confirmed
dead, remove them along with `_get_provider()` rather than updating their catch blocks.
Record the finding in the Gate 0 summary and Gate 1 commit message.

**Existing public methods preserved in behavior:** `generate()`, `get_report_config()`,
`get_provider_manager()` singleton — signatures unchanged, internal lookup updated.

### 1g. `workmain/ai/__init__.py` — remove dead exports

Using the caller audit from Gate 0:
- Remove `get_claude_client` and `get_gemini_client` from exports (these imported
  from the now-deleted `claude_client.py` and `gemini_client.py`)
- If Gate 0 found any active callers of these exports outside `provider_manager.py`,
  update those callers to use `get_provider_manager().get_provider('claude')` /
  `get_provider_manager().get_provider('gemini')` before removing the exports
- If Gate 0 confirmed the imports are dead code (expected — `note_condenser.py` v1.8
  routes through `ProviderManager`), remove cleanly with no substitution needed
- Any other re-exports referencing `claude_client` or `gemini_client` module paths
  must also be removed or updated

### 1h. `config/ai_settings.json` — Ollama section + cost_structure

Using the exact schema verified at Gate 0, add:
1. `cost_structure` field to all existing provider sections:
   - `claude`: `"cost_structure": "$3/MTok prompt, $15/MTok completion"`
   - `gemini`: `"cost_structure": "$0.15/MTok prompt, $0.60/MTok completion"`
2. Complete `ollama` section:
```json
"ollama": {
    "enabled": false,
    "model": "mistral-7b",
    "host": "localhost",
    "port": 11434,
    "cost_structure": "Local — no API cost"
}
```

### 1i. Delete old client files

```bash
git rm workmain/ai/claude_client.py
git rm workmain/ai/gemini_client.py
```

Run full test suite immediately after deletion. All failures at this point are missed
imports — fix before proceeding to Gate 2.

```bash
python -m pytest tests/ -v
```

### Gate 1 Verification
```
[ ] base_provider.py — ProviderUnavailableError class present
[ ] base_provider.py — ProviderType.OLLAMA in enum
[ ] base_provider.py — __init__ accepts dict; all existing attrs preserved
[ ] base_provider.py — test_connection() default method present
[ ] base_provider.py — ProviderConfig has TODO comment with backlog item placeholder
[ ] providers/ directory: __init__.py, claude.py, gemini.py, ollama.py
[ ] PROVIDER_REGISTRY has three entries: claude, gemini, ollama
[ ] OllamaProvider — all 5 abstract methods present, no ABC TypeError on instantiation
[ ] python -c "from workmain.ai.providers.ollama import OllamaProvider; OllamaProvider({'model':'x','host':'localhost','port':11434})" — no error
[ ] ProviderManager instantiates from registry only
[ ] ProviderManager._disabled tracks disabled providers
[ ] ProviderManager.get_all_provider_configs() returns all three including ollama
[ ] _get_provider() removed — grep -n "_get_provider" workmain/ai/provider_manager.py returns empty
[ ] generate() uses get_provider(primary.value) — no remaining enum-keyed lookups
[ ] workmain/ai/__init__.py — dead exports removed; no references to deleted modules
[ ] config/ai_settings.json — ollama section; cost_structure in all provider sections
[ ] claude_client.py and gemini_client.py deleted
[ ] Full test suite passes after deletion — 0 failures, no missed imports (Gate 1i)
```

```bash
git add -A
git commit -m "feat(provider-foundation): Gate 1 — base_provider.py extended, \
providers/ subpackage, ProviderManager registry refactor (generate() string-keyed, \
_get_provider() retired), ai/__init__.py exports cleaned, ollama stub, \
old client files deleted"
```

---

## Gate 2 — Config-Driven Model Selection (Item 35)

### Objective

Confirm `ClaudeProvider` and `GeminiProvider` read their model strings from config
at instantiation. This should largely be done by Gate 1 since `__init__` reads from the
config dict — Gate 2 is verification and end-to-end confirmation.

### 2a. Confirm in `providers/claude.py`

```python
self.model = config.get('model', '<fallback from Gate 0>')
```

Confirm `generate()` uses `self.model` throughout — no hardcoded model string in the
method body. The fallback constant must match the string found in `claude_client.py`
at Gate 0 exactly.

### 2b. Confirm in `providers/gemini.py`

Same pattern. Fallback constant must match `gemini_client.py` Gate 0 finding.

### 2c. Verify end-to-end

Change `providers.claude.model` to `"test-model-gate2"` in `ai_settings.json`. Run:
```bash
workmain providers list
```
Claude row must show `test-model-gate2`. Revert after verification.

The user's current `ai_settings.json` model values (whatever they are post-Phase 4
updates) will be respected from this gate forward. Model changes are config-only.

### Gate 2 Verification
```
[ ] ClaudeProvider.model reads from config.get('model', fallback) — fallback matches Gate 0
[ ] GeminiProvider.model reads from config.get('model', fallback) — fallback matches Gate 0
[ ] generate() in both uses self.model — no hardcoded model string in method body
[ ] End-to-end test: providers list shows config value (manual verify + revert)
[ ] python -m pytest tests/ — 0 failures
```

```bash
git add -A
git commit -m "feat(provider-foundation): Gate 2 — config-driven model selection (Item 35)"
```

---

## Gate 3 — Hardcoded Reference Sweep

### Objective

Fix every hit from the Gate 0 audit. Work from the documented hit list — no
guesswork. Category A and B hits are mandatory. Category C/D hits that name a
specific provider where the active provider may differ are mandatory.

### 3a. System prompts — Category A (minimal-change rule)

**Scope:** Remove identity statements only. No restructuring, no quality improvements,
no content changes beyond the targeted substitution.

```
"You are Claude, an AI assistant made by Anthropic." →
"You are a professional work management assistant."

"As Claude, your role is..." →
"Your role is..."
```

Apply to every file in the Gate 0 Category A hit list. If a line references Claude
in a capability context ("As Claude, I can analyze...") change to role language
("As your work management assistant, I can analyze..."). Version-bump every modified
file.

### 3b. CLI status messages — Category B

**Primary confirmed bug** — "Sending to Claude..." in `note_condenser.py`:

Use the method name confirmed at Gate 0 (expected `get_report_config()`). The
`primary_provider` field type (enum or string) was verified at Gate 0 — use the
appropriate access pattern:

```python
# If primary_provider is a ProviderType enum:
report_config = self.provider_manager.get_report_config('note_condensation')
active_provider = report_config.primary_provider.value.capitalize()

# If primary_provider is already a string:
report_config = self.provider_manager.get_report_config('note_condensation')
active_provider = report_config.primary_provider.capitalize()

console.print(f"Sending to {active_provider}...")
```

Apply the same dynamic display pattern to every Category B hit in the audit list.
Provider display names must come from `ProviderManager` — never hardcoded in command
layer.

### 3c. Help strings and output labels — Category C/D

For each Category C/D hit: if the string names a specific provider where the active
provider may differ, replace with generic language ("AI provider", "configured
provider") or dynamic value. If the string describes a feature genuinely tied to a
specific provider, leave unchanged and document the reason in the gate summary.

Every Category C/D hit must be accounted for in the gate summary — fixed or
left-unchanged-with-reason.

### Gate 3 Verification
```
[ ] All Category A hits resolved — grep for "Anthropic" / "You are Claude" in
    system prompt text returns no hits
[ ] "Sending to..." bug fixed — manual: run meetings condense, verify display
    matches provider shown in notes costs
[ ] All mandatory Category B hits resolved
[ ] All mandatory Category C/D hits resolved
[ ] Gate 0 hit list fully accounted for — every hit documented in gate summary
[ ] python -m pytest tests/ — 0 failures
```

```bash
git add -A
git commit -m "feat(provider-foundation): Gate 3 — hardcoded reference sweep; \
system prompts, status messages, help strings"
```

---

## Gate 4 — providers list + set default + config show

### Objective

Deliver three provider CLI improvements. Use group variable names confirmed at Gate 0
for `providers_set` and `providers_config`.

### 4a. `providers list` — disabled status + model + cost_structure columns

**Dynamic provider iteration (N-provider-safe):**
```python
for name, config in provider_manager.get_all_provider_configs().items():
    model = config.get('model', '—')
    cost = config.get('cost_structure', '—')
    if provider_manager.is_disabled(name):
        status = "disabled"
        # No connectivity check — disabled check gates before any network call
    else:
        provider = provider_manager.get_provider(name)
        status = "available" if provider.test_connection() else "unavailable"
    # Add row to table
```

Both model and cost_structure read from config — no hardcoded strings in `providers.py`.

**Expected output:**
```
╭──────────────┬────────────────────────────┬──────────────┬──────────────────────────────────────────╮
│ Provider     │ Model                      │ Status       │ Cost Structure                           │
├──────────────┼────────────────────────────┼──────────────┼──────────────────────────────────────────┤
│ Claude       │ claude-sonnet-4-5-20250929 │ available    │ $3/MTok prompt, $15/MTok completion      │
│ Gemini       │ gemini-2.5-flash           │ available    │ $0.15/MTok prompt, $0.60/MTok completion │
│ Ollama       │ mistral-7b                 │ disabled     │ Local — no API cost                      │
╰──────────────┴────────────────────────────┴──────────────┴──────────────────────────────────────────╯
```

**Provider Assignments section** — keep as-is. It provides a quick routing summary
users expect. `providers config show` is the full detail view; they serve different
purposes.

### 4b. `providers test` — dynamic provider validation

Remove `click.Choice(['claude', 'gemini'])`. Use runtime validation:

```python
@providers.command('test')
@click.argument('provider')
def test_provider(provider):
    """Test connection to an AI provider."""
    pm = get_provider_manager()
    valid = pm.get_registered_provider_names()
    if provider not in valid:
        raise click.BadParameter(
            f"Unknown provider '{provider}'. "
            f"Valid providers: {', '.join(valid)}"
        )
    if pm.is_disabled(provider):
        console.print(f"[yellow]{provider} is disabled.[/yellow] "
                      f"Set 'enabled: true' in config/ai_settings.json to test.")
        return
    # ... existing test logic ...
```

### 4c. `providers costs --provider` — dynamic validation

Remove `click.Choice(['claude', 'gemini'])` from `--provider` option. Use the same
runtime validation pattern as 4b. Empty results for a valid-but-unused provider
(e.g. `--provider ollama`) is a valid state — display empty table, no error.

### 4d. `providers set default` — implemented

Wire into the `providers_set` group using the variable name confirmed at Gate 0:

```python
@providers_set.command('default')
@click.argument('report_type', metavar='REPORT_TYPE')
@click.argument('provider', metavar='PROVIDER')
@click.option('--fallback', '-f', default=None,
              help='Set fallback provider (optional)')
@click.option('--force', is_flag=True, default=False,
              help='Skip confirmation prompt')
def set_default(report_type, provider, fallback, force):
    """Set the default AI provider for a report type.

    REPORT_TYPE: e.g. daily_internal, weekly_client, note_condensation
    PROVIDER: e.g. claude, gemini
    """
```

**Validation:**
```python
pm = get_provider_manager()
valid_providers = pm.get_registered_provider_names()
valid_report_types = list(settings['report_types'].keys())

if report_type not in valid_report_types:
    raise click.BadParameter(
        f"Unknown report type '{report_type}'. "
        f"Valid: {', '.join(valid_report_types)}"
    )
if provider not in valid_providers:
    raise click.BadParameter(
        f"Unknown provider '{provider}'. "
        f"Valid: {', '.join(valid_providers)}"
    )
if fallback and fallback not in valid_providers:
    raise click.BadParameter(
        f"Unknown fallback provider '{fallback}'. "
        f"Valid: {', '.join(valid_providers)}"
    )
```

**Confirmation + write:**
```python
# Show diff and confirm
console.print("Provider assignment change:")
console.print(f"  {report_type}  primary_provider: "
              f"{current_primary} → {provider}")
if fallback:
    console.print(f"  {report_type}  fallback_provider: "
                  f"{current_fallback} → {fallback}")

if not force:
    click.confirm("Proceed?", abort=True)

# Read-modify-write
from datetime import date
with open(settings_path, 'r') as f:
    data = json.load(f)
data['report_types'][report_type]['primary_provider'] = provider
if fallback:
    data['report_types'][report_type]['fallback_provider'] = fallback
data['last_updated'] = date.today().strftime('%Y%m%d')
with open(settings_path, 'w') as f:
    json.dump(data, f, indent=2)

console.print(f"[green]✓ Updated ai_settings.json[/green]")
console.print(f"  {report_type} → {provider.capitalize()}"
              + (f" (fallback: {fallback.capitalize()})" if fallback else ""))
console.print("[dim]Changes take effect on next CLI invocation.[/dim]")
```

`--force` has no short form (CLI Standards §5.2). `-f` for `--fallback` must be
checked against §5.3 reserved table before assignment.

### 4e. `providers config show` — new subcommand

Create `providers_config` subgroup if it does not already exist (per Gate 0 finding).
Register `show` as its first command:

```python
@providers_config.command('show')
def config_show():
    """Display current ai_settings.json provider configuration."""
```

Renders two Rich panels:
1. **Providers** — for each provider: name, enabled/disabled, model, API key env var
   (name only — never value), cost_structure
2. **Report Type Assignments** — for each report type: primary provider, fallback

Does not expose API key values. `api_key_env` field name shown, not the key itself.

### 4f. `docs/ai_settings_guide.md` — schema documentation (Item 10)

New document. Contents:
- Full annotated description of every field in `ai_settings.json`
- `enabled` flag: false = disabled (shown in `providers list`, connectivity skipped)
- `model` field: read at instantiation; change here to update model — no code edits
  needed (Item 35 mechanism)
- `cost_structure` field: read by `providers list`; update here if pricing changes
- `api_key_env` field: env var name that holds the API key; never store the key itself
- `report_types` section: `primary_provider` / `fallback_provider` per type
- How to change provider assignments: direct edit or `workmain providers set default`
- Fallback behaviour: when primary fails, ProviderManager tries fallback automatically
- How to add a new provider: three-step process (file + registry + config)
- Phase 13-1 Ollama activation checklist (mirrors ollama.py docstring)

### Gate 4 Verification
```
[ ] providers list: 3 rows; Ollama shows "disabled"; model/cost_structure from config
[ ] providers list: no network call for Ollama (< 5s wall time with disabled ollama)
[ ] providers list: Provider Assignments section still present
[ ] providers test ollama — shows "disabled" message, no crash
[ ] providers test <unknown> — BadParameter with valid provider list
[ ] providers costs --provider ollama — empty table, no error
[ ] providers costs --provider <unknown> — BadParameter with valid provider list
[ ] providers set default daily_internal claude — confirmation shown; file updated;
    only targeted fields changed; last_updated updated
[ ] providers set default <unknown_type> — BadParameter
[ ] providers set default daily_internal <unknown_provider> — BadParameter
[ ] providers set default --force skips confirmation
[ ] "Changes take effect on next CLI invocation." in output
[ ] providers config show renders without error
[ ] docs/ai_settings_guide.md complete
[ ] python -m pytest tests/ — 0 failures
```

```bash
git add -A
git commit -m "feat(provider-foundation): Gate 4 — providers list N-provider dynamic, \
set default implemented, config show, ai_settings_guide.md (Item 10)"
```

---

## Gate 5 — Tests + Version Bump + Merge

### New test file: `tests/test_provider_foundation.py`

**Registry tests:**
- `PROVIDER_REGISTRY` has keys: claude, gemini, ollama
- Each value is a class (not an instance)
- Each class is a subclass of `BaseProvider`

**`base_provider.py` addition tests:**
- `ProviderUnavailableError` is a subclass of `ProviderError`
- `ProviderType.OLLAMA` value is `'ollama'`
- `BaseProvider.test_connection()` returns `False` when `check_availability()` raises

**OllamaProvider stub tests:**
- Instantiates without `TypeError` — ABC contract satisfied
- `generate()` raises `ProviderUnavailableError`
- `test_connection()` returns `False`
- `estimate_cost(100, 50)` returns `0.0`
- `validate_config()` returns `True` when host and port set
- `check_availability()` returns `ProviderStatus.UNAVAILABLE`

**Config-driven model tests:**
- `ClaudeProvider({'model': 'test-model'})` — `provider.model == 'test-model'`
- `ClaudeProvider({})` — `provider.model == <Gate 0 fallback constant>`
- `GeminiProvider({'model': 'test-model'})` — `provider.model == 'test-model'`
- `GeminiProvider({})` — `provider.model == <Gate 0 fallback constant>`

**ProviderManager N-provider tests:**
- Disabled provider not in `_providers`, present in `_disabled`
- `get_provider('ollama')` when disabled → `ProviderUnavailableError` with config hint
- `get_provider('unknown')` → `ProviderUnavailableError` with registry hint
- `get_all_provider_configs()` returns all three including ollama
- `get_registered_provider_names()` returns `['claude', 'gemini', 'ollama']`
- `is_disabled('ollama')` returns `True` when `enabled: false`
- `is_disabled('claude')` returns `False` when `enabled: true`

**Dynamic validation tests:**
- `providers test claude` → no BadParameter
- `providers test unknown_provider` → BadParameter with valid list in message
- `providers costs --provider gemini` → no BadParameter
- `providers costs --provider unknown` → BadParameter

**`providers set default` tests:**
- Read-modify-write preserves all fields not being changed
- `last_updated` field updated to today's date
- Unknown `report_type` → BadParameter
- Unknown `provider` → BadParameter
- `--force` skips confirmation
- "Changes take effect on next CLI invocation." in output

**Display accuracy test:**
- Status message matches active provider (mock `get_report_config()`)

**Update `tests/test_ai_foundation.py`:**
- Fix import paths: `claude_client` → `providers.claude`; `gemini_client` → `providers.gemini`
- Extend config structure test to include ollama section and cost_structure fields

### Version bump and documentation files

- `workmain/__version__.py` — v1.17.0 → v1.18.0
- `CHANGELOG.md` — new [1.18.0] entry
- `docs/FEATURE_BACKLOG.md` — Items 10, 11, 35 COMPLETE (v1.18.0); version bump;
  add new item: **`ProviderConfig` dead code cleanup** — `ProviderConfig` dataclass
  in `base_provider.py` has no remaining consumers post-v1.18.0 (only consumers were
  `claude_client.py` / `gemini_client.py`, both deleted). Remove when
  `base_provider.py` is next modified. Low priority, no functional impact.
  Update the TODO comment in `base_provider.py` with the assigned item number.
- `docs/CLI_STANDARDS.md` — register `providers set default`, `providers config show`;
  dynamic provider argument pattern documented; `-f/--fallback` scope added to §5.3

### Session handoff document

Create `SESSION_HANDOFF_PROVIDER_FOUNDATION_SPRINT_COMPLETE_<YYYYMMDD>.md`. Include:
- Sprint complete at v1.18.0
- Full test count (before and after)
- All new and deleted files with versions
- Gate 0 audit summary — category hits found and resolved by file/line
- Model fallback constants confirmed (from Gate 0)
- `CostTracker` finding (active or dead — backlog item number if logged)
- Any Category C/D hits left unchanged with documented reason
- Phase 13-1 Ollama activation checklist reference (docs/ai_settings_guide.md)
- Next phase: Phase 13-1 (Ollama Foundation)

### Merge flow

```bash
git add -A
git commit -m "feat(provider-foundation): Gate 5 — tests, v1.18.0 bump, CHANGELOG, \
backlog Items 10/11/35 complete"

# Step 1: push feature branch and open PR to dev
git push origin feature/provider-foundation
gh pr create --base dev --head feature/provider-foundation \
  --title "feat: Provider Foundation Sprint (v1.18.0)" \
  --body "N-provider extensible registry; providers/ subpackage; Ollama ABC-compliant stub; \
config-driven model selection (Item 35); hardcoded reference sweep; \
providers set default implemented; dynamic provider validation; Items 10, 11, 35 closed."
# Merge PR on GitHub, then:
git checkout dev
git pull origin dev
git branch -d feature/provider-foundation

# Step 2: verify full suite on dev before promoting
python -m pytest tests/

# Step 3: open PR dev → main
gh pr create --base main --head dev \
  --title "feat: Provider Foundation Sprint (v1.18.0)" \
  --body "Provider Foundation Sprint complete. N-provider extensible registry, \
Ollama ABC-compliant stub, config-driven model selection, hardcoded reference \
sweep, providers set default implemented, Items 10/11/35 closed."
# Merge PR on GitHub, then:
git checkout main
git pull origin main
git tag v1.18.0
git push --tags

# Step 4: publish GitHub release
gh release create v1.18.0 \
  --title "v1.18.0 — Provider Foundation Sprint" \
  --notes "N-provider extensible registry; Ollama disabled placeholder \
(Phase 13-1 activation); config-driven model selection (Item 35); \
hardcoded provider reference sweep; providers set default implemented; \
Items 10, 11, 35 closed."
```

### Gate 5 Verification
```
[ ] test_provider_foundation.py — all cases pass
[ ] test_ai_foundation.py — updated imports, 0 failures
[ ] python -m pytest tests/ on dev — 0 failures before PR to main
[ ] python -m pytest tests/ on main — 0 failures, new total recorded
[ ] __version__.py shows 1.18.0
[ ] CHANGELOG.md [1.18.0] entry present
[ ] FEATURE_BACKLOG.md Items 10, 11, 35 marked COMPLETE; ProviderConfig cleanup item added
[ ] base_provider.py TODO comment updated with assigned ProviderConfig backlog item number
[ ] CLI_STANDARDS.md updated for new commands and dynamic provider arg
[ ] SESSION_HANDOFF_PROVIDER_FOUNDATION_SPRINT_COMPLETE_*.md exists
[ ] GitHub PR feature/provider-foundation → dev merged
[ ] GitHub PR dev → main merged
[ ] git tag v1.18.0 exists and pushed
[ ] GitHub release v1.18.0 published
[ ] feature/provider-foundation branch deleted (local and remote)
[ ] claude_client.py and gemini_client.py no longer exist in repository
[ ] grep -n "_get_provider" workmain/ai/provider_manager.py — returns empty
```

---

## Constraints and Reminders

- Read all five Pre-Implementation documents before Gate 0. Do not skip.
- `base_provider.py` is a Modified File in this sprint. Update it in Gate 1a before
  creating the `providers/` subpackage — new provider files import from it.
- `base_provider.py` lives at `workmain/ai/base_provider.py` permanently.
  Do not move it into `providers/`.
- Gate 0 audit findings must be fully documented before any Gate 1 code is written.
  The audit hit list drives Gate 3 exactly — no guesswork in the sweep.
- `OllamaProvider` must satisfy the ABC contract — all five abstract methods present
  with correct signatures. Verify: `python -c "from workmain.ai.providers.ollama import
  OllamaProvider; OllamaProvider({'model':'x','host':'h','port':11434})"` must not raise.
- `claude_client.py` and `gemini_client.py` must be deleted with `git rm` — no shims.
  Run the full test suite immediately after deletion (Gate 1h).
- `workmain/ai/__init__.py` must be updated before the test suite run in Gate 1h —
  dead exports from deleted modules will cause import errors that obscure real misses.
- `_get_provider()` must be fully removed from `provider_manager.py`. Every call site
  recorded at Gate 0 must be updated to `get_provider(provider_type.value)` before
  removal. Verify with grep — zero remaining references required.
- `generate()` behavior is preserved; only the internal lookup mechanism changes
  (enum key → string key via `.value`). Do not alter `generate()` signatures or logic.
- System prompt changes are minimal-scope: identity statements only.
  No prompt restructuring, no quality improvements beyond the targeted substitution.
- `providers set default` must use read-modify-write. Never construct a new JSON
  object from scratch. Always update `last_updated`.
- `providers set default` output must include "Changes take effect on next CLI
  invocation." — users need to know the singleton caches the old config.
- Disabled providers must never trigger a network call. `is_disabled()` gates before
  any `test_connection()` or API attempt.
- `click.Choice` for provider arguments must be removed from `providers test` and
  `providers costs`. Replace with runtime validation against `get_registered_provider_names()`.
  An unknown provider must produce a helpful `BadParameter` listing valid options.
- `--force` has no short form (CLI Standards §5.2). `-f/--fallback` checked against
  §5.3 reserved table before assignment.
- Provider display names in all output come from `ProviderManager` or config — never
  hardcoded in the command layer.
- If `CostTracker` appears dead post-v1.17.0, log a new FEATURE_BACKLOG item and do
  not remove it in this sprint.
- Version bump is minor: v1.17.0 → v1.18.0. Do not deviate.

---

## Summary — Gate Completion Checklist

| Gate | Deliverable | Status |
|------|-------------|--------|
| 0 | Branch setup, test baseline, base_provider.py audit (abstract signatures, __init__, exceptions, enums), ProviderManager/providers.py audit, ai_settings.json schema, hardcoded reference audit (4 categories), model fallback constants | [ ] |
| 1 | base_provider.py extended (ProviderUnavailableError, OLLAMA, dict init, test_connection); providers/ subpackage; ProviderManager registry refactor; ai_settings.json Ollama + cost_structure; old client files deleted | [ ] |
| 2 | Config-driven model selection confirmed in claude.py and gemini.py (Item 35) | [ ] |
| 3 | Hardcoded reference sweep — system prompts, status messages, help strings (from Gate 0 hit list) | [ ] |
| 4 | providers list N-provider dynamic; providers test/costs dynamic validation; providers set default; providers config show; ai_settings_guide.md (Item 10) | [ ] |
| 5 | Tests, v1.18.0 bump, CHANGELOG, FEATURE_BACKLOG Items 10/11/35, PRs, tag, release | [ ] |

---

## Verification

```bash
# 1. Registry loads all three providers
python -c "from workmain.ai.providers import PROVIDER_REGISTRY; print(list(PROVIDER_REGISTRY.keys()))"
# Expected: ['claude', 'gemini', 'ollama']

# 2. OllamaProvider ABC-compliant — no TypeError
python -c "
from workmain.ai.providers.ollama import OllamaProvider
p = OllamaProvider({'model': 'mistral-7b', 'host': 'localhost', 'port': 11434})
print('Instantiated OK')
try:
    p.generate(None)
except Exception as e:
    print(type(e).__name__, '—', str(e)[:60])
"
# Expected: Instantiated OK / ProviderUnavailableError — Ollama provider is not yet...

# 3. Old client files gone
ls workmain/ai/claude_client.py 2>&1   # No such file or directory
ls workmain/ai/gemini_client.py 2>&1   # No such file or directory

# 4. providers list shows all three with correct status
workmain providers list
# Claude: available, Gemini: available, Ollama: disabled
# Model column reads from ai_settings.json

# 5. Model column is config-driven
# Edit config/ai_settings.json: providers.claude.model → "test-model-gate2"
workmain providers list   # Claude row shows test-model-gate2
# Revert

# 6. Sending to... matches actual provider
# Confirm ai_settings.json: note_condensation primary_provider: gemini
workmain notes log -m <meeting_id>
# Must show "Sending to Gemini...", not "Sending to Claude..."
workmain notes costs   # Provider column shows Gemini — matches display

# 7. Dynamic provider validation
workmain providers test unknown_provider   # BadParameter with valid list
workmain providers test ollama            # Disabled message, no crash

# 8. providers set default
workmain providers set default daily_internal claude
# Confirmation shown; ai_settings.json updated; only targeted fields changed
# last_updated updated; "Changes take effect on next CLI invocation." shown
workmain providers set default daily_internal gemini   # revert

# 9. providers config show
workmain providers config show   # renders, no crash

# 10. Full test suite
python -m pytest tests/
```

---

END OF SPEC
WorkmAIn PROVIDER_FOUNDATION_SPRINT_SPEC — v1.1 — 20260529
