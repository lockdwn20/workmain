WorkmAIn
PHASE13_SPRINT1_OLLAMA_PROVIDER_SPEC_v1_8
20260605

Version History:
- v1.0: Initial spec — Phase 13 Sprint 1 (Ollama Provider Activation)
- v1.1: Infrastructure confirmed live — updated Gate 0b expected output, Gate 1c
        ai_settings.json values, and Locked Decisions with confirmed host/model
- v1.2: Claude Code review (12 issues) — fixed 6 critical bugs: GenerationResponse/
        GenerationRequest/AiCostRepository field names, ProviderType enum usage,
        generate() kwarg + tuple unpack, DB session import path; fixed workflow
        violation (dev->main via GitHub PR); minor fixes: dates, commit format,
        CLAUDE.md path, double round-trip note
- v1.3: Claude Code review (5 issues) — fixed ProviderType missing import in
        intent_parser.py; cost_usd vs cost field name (GenerationResponse.cost vs
        AiCostRepository.cost_usd are different objects); super().__init__(config)
        omitted from OllamaProvider constructor; stale test assertions updated to
        ProviderStatus enum and correct field names; cosmetic footer/SQL date fixes
- v1.4: Claude Code review (3 issues) — fixed test_parse_raises_provider_unavailable
        mock target (ProviderManager.generate() not OllamaProvider.check_availability);
        CHANGELOG test count 11->10; removed unused Optional import in intent_parser.py
- v1.5: Gate 2 benchmark tuning — 7/10 baseline; three prompt/config fixes: (1) added
        explicit "note:" prefix rule; (2) clarified duration_minutes no-conversion rule;
        (3) expanded carry-forward tag inference; (4) timeout 30s → 60s in ai_settings.json
- v1.6: Gate 2 second benchmark tuning — (1) timeout 60s → 120s; (2) temperature 0.1 → 0.4;
        (3) generation_options block added (top_p, top_k, repeat_penalty); (4) system prompt
        extracted to config/intent_parse_system_prompt.txt — JSON holds params only;
        (5) note: example moved earlier in schema; (6) OllamaProvider passes generation_options
        to API payload; (7) Modelfile approach added to FEATURE_BACKLOG as new item
- v1.7: Modelfile pulled forward from Phase 14 backlog into Sprint 1 Gate 2;
        ai_settings.json model updated to workmain-intent:latest; Gate 0b and Gate 1c
        updated to reflect model name change; Gate 2 benchmark now runs against
        workmain-intent not mistral:latest; Locked Decisions updated
- v1.8: Claude Code Q1-Q4 resolved — system_prompt=None at runtime (Modelfile owns
        system); generation_options removed from per-request path (Modelfile owns params,
        JSON is editable reference); GenerationRequest.generation_options field confirmed;
        Modelfile PARAMETER blocks confirmed as runtime source of truth; config file
        headers added to intent_parse_prompt.json and intent_parse_system_prompt.txt
        with version, dates, Ollama model name, and host reference

---

# Phase 13 Sprint 1 — Ollama Provider Activation

**Version target:** v1.19.0
**Branch:** `feature/phase-13-sprint1-ollama-provider` from `dev`
**Baseline:** v1.18.3, 479 tests passing, `main` clean
**Closes backlog items:** 36 (ProviderConfig dead code — on first `base_provider.py` touch)
**Partially addresses:** Item 19 (Ollama GPU offloading — CPU path only; GPU deferred)

---

## Goals

Activate the OllamaProvider stub introduced in v1.18.0, implement intent parsing
against Mistral 7B running on Proxmox, and validate prompt quality through a hard
benchmark gate before any Slack or orchestration work begins.

This sprint deliberately has no Slack dependencies. Everything delivered here
(provider activation, intent parsing, cost tracking extension) is foundational
infrastructure that Sprints 2 and 3 build on.

---

## Locked Architectural Decisions

| # | Decision |
|---|----------|
| 1 | Intent prompt stored at `config/intent_parse_prompt.json` — editable without code changes |
| 2 | `templates/style/` reserved for voice/style artifacts only; intent prompt is config |
| 3 | OllamaProvider lives in existing `workmain/ai/providers/ollama.py` stub — no new file |
| 9 | Ollama host: `workmain-ollama.lab.haloschaos.com:11434`; model: `mistral:latest` (confirmed 20260605) |
| 4 | Migration 018 extends `ai_costs` CHECK constraint for `'intent_parse'` interaction type |
| 5 | Benchmark gate is a hard stop — Claude Code presents results, waits for user approval |
| 6 | Gate 0 includes `note_condenser.py` v2.1 writing style fix (broken style path → StyleAdapter) |
| 7 | No Slack polling, no orchestration, no T1–T6 triggers — those are Sprint 2 and 3 |
| 10 | Modelfile pulled forward from Phase 14 — workmain-intent:latest is the benchmark target |
| 11 | intent_parse_system_prompt.txt is source of truth; Modelfile SYSTEM block must stay in sync |
| 12 | system_prompt=None at runtime — Modelfile owns system prompt; txt file is not a runtime artifact |
| 13 | Modelfile PARAMETER blocks own temperature/top_p/top_k/repeat_penalty; generation_options in
       JSON is the human-readable reference for rebuild; only max_tokens is per-request variable |
| 14 | GenerationRequest.generation_options: Optional[Dict[str, Any]] = None added to base_provider.py;
       optional/None default — existing Claude/Gemini call sites unaffected |
| 8 | Item 36 (ProviderConfig dead code) resolved on first `base_provider.py` touch in Gate 1 |

---

## Pre-Flight Reading (Claude Code must complete before Gate 0)

Claude Code must read all five documents before starting work:

1. `CLAUDE.md` (repo root)
2. `docs/GIT_WORKFLOW_STANDARDS.md`
3. `docs/CLI_STANDARDS.md`
4. `docs/TESTING_STANDARDS.md`
5. This spec — gate by gate

---

## Gate 0 — Environment Verification + Writing Style Fix

**Purpose:** Confirm the live codebase and Ollama infrastructure are ready before
any implementation begins. Resolve the known note_condenser writing style bug as
a mandatory prerequisite.

### 0a — Codebase Baseline

```bash
# Confirm version
python -c "from workmain.__version__ import __version__; print(__version__)"
# Expected: 1.18.3

# Confirm test suite
python -m pytest tests/ -q
# Expected: 479 passed, 0 failed

# Confirm branch
git branch --show-current
# Expected: dev (feature branch will be cut in Gate 0 after verification)

# Confirm OllamaProvider stub exists
grep -n "class OllamaProvider" workmain/ai/providers/ollama.py
# Expected: line found

# Confirm ollama section in ai_settings.json
python -c "import json; s=json.load(open('config/ai_settings.json')); print(json.dumps(s.get('providers',{}).get('ollama',{}), indent=2))"
# Expected: enabled, host, port, model fields present
```

**STOP:** Report baseline results before proceeding. If test count is not 479 or
version is not 1.18.3, stop and report the discrepancy.

### 0b — Ollama Infrastructure Verification

Verify Mistral 7B is reachable on the Proxmox server. The host and port values
are read from `config/ai_settings.json` (`providers.ollama.host` and
`providers.ollama.port`). Do not hardcode network addresses.

```bash
# Read host/port from config and test connectivity
python -c "
import json, urllib.request
cfg = json.load(open('config/ai_settings.json'))
ollama = cfg['providers']['ollama']
host, port = ollama['host'], ollama['port']
url = f'http://{host}:{port}/api/tags'
try:
    resp = urllib.request.urlopen(url, timeout=10)
    data = json.loads(resp.read())
    models = [m['name'] for m in data.get('models', [])]
    print(f'Ollama reachable at {host}:{port}')
    print(f'Available models: {models}')
except Exception as e:
    print(f'FAIL: {e}')
"
```

**Expected output (infrastructure pre-confirmed 20260605):**
```
Ollama reachable at workmain-ollama.lab.haloschaos.com:11434
Available models: ["mistral:latest"]
```

The Ollama LXC is already live and verified. If this check fails, the container
has gone down or the DNS name is not resolving — stop and report.

Confirmed infrastructure values (use these exactly — do not re-derive):
- Host: `workmain-ollama.lab.haloschaos.com`
- Port: `11434`
- Base model: `mistral:latest` (pulled in LXC provisioning)
- Intent model: `workmain-intent:latest` (built via build_workmain_intent.sh)
- Quantization: Q4_K_M (7.2B parameters, 32K context)

**Gate 0b also verifies workmain-intent is built:**
```bash
curl -s http://workmain-ollama.lab.haloschaos.com:11434/api/tags | \
  python3 -c "import sys,json; models=[m['name'] for m in json.load(sys.stdin)['models']]; print(models)"
# Expected: list includes both 'mistral:latest' AND 'workmain-intent:latest'
```
If `workmain-intent:latest` is absent, run `build_workmain_intent.sh` on the LXC
before proceeding. See OLLAMA_PROXMOX_LXC_SPEC for instructions.

### 0c — Writing Style Fix (note_condenser.py v2.1)

**Context:** `NoteCondenser._format_writing_style_context()` loads `writing_style.json`
independently and queries three non-existent keys (`voice_characteristics`, top-level
`tone`, `example_phrases`). It always returns a bare header with no content. Fix this
before any new AI work builds on top of the broken path.

**Changes to `workmain/ai/note_condenser.py`:**

1. Add import at top of file:
   ```python
   from workmain.templates_engine import get_style_adapter
   ```

2. In `__init__`: remove `self.writing_style = self._load_writing_style()`.
   Add: `self.style_adapter = get_style_adapter()`

3. Delete `_load_writing_style()` method entirely.

4. Delete `_format_writing_style_context()` method entirely.

5. In `_build_condensation_prompt()`, replace the `if self.writing_style:` block
   that calls `_format_writing_style_context()` with:
   ```python
   style_context = self.style_adapter.get_style_prompt("internal")
   if style_context:
       prompt = f"WRITING STYLE CONTEXT:\n{style_context}\n\n{prompt}"
   ```

6. Remove the trailing `if self.writing_style:` check that appends requirement #7.
   Make requirement #7 unconditional — style is always available via StyleAdapter.

7. Version bump: `v2.0 → v2.1`, date `20260603 → 20260605`.
   Version history entry:
   ```
   - v2.1: Gate 0 Phase 13 Sprint 1 (20260605) — replace broken _format_writing_style_context
           with StyleAdapter.get_style_prompt("internal") for consistent voice
           across condensation and reports
   ```

**Verification after fix:**
```bash
python -m pytest tests/ -q
# Expected: 479 passed, 0 failed (no regressions)
```

Then manually confirm:
```bash
workmain meetings condense <any meeting id with notes>
```
Inspect the condensed output — it should use action verbs, active voice, and
outcome-first framing consistent with report lines.

### 0d — Cut Feature Branch

```bash
git checkout dev
git pull origin dev
git checkout -b feature/phase-13-sprint1-ollama-provider
```

Commit Gate 0c fix:
```bash
git add workmain/ai/note_condenser.py
git commit -m "fix(phase13-sprint1): note_condenser writing style path — StyleAdapter replaces broken _format_writing_style_context (v2.1)"
```

**STOP:** Report Gate 0 results:
- Baseline confirmed (version, test count)
- Ollama reachable (host, port, exact model name from tags response)
- Writing style fix applied and verified (479 passed, manual condense output reviewed)
- Feature branch cut

Do not proceed to Gate 1 until all three checks are confirmed.

---

## Gate 1 — OllamaProvider Implementation

**Purpose:** Implement `generate()` and `check_availability()` in the existing
stub, making OllamaProvider a fully functional BaseProvider.

### 1a — Item 36: ProviderConfig Dead Code Cleanup

This is the first touch to `base_provider.py` since v1.18.0. Item 36 requires
removing the `ProviderConfig` dataclass on this touch.

**In `workmain/ai/base_provider.py`:**

**Change 1 — Remove ProviderConfig dead code (Item 36):**
- Remove the `ProviderConfig` dataclass (it has no consumers post-v1.18.0;
  a TODO comment was added at v1.18.0 marking it for removal)

**Change 2 — Add `generation_options` field to `GenerationRequest`:**
- Add `generation_options: Optional[Dict[str, Any]] = None` to the
  `GenerationRequest` dataclass
- Add required imports if not already present:
  `from typing import Optional, Dict, Any`
- This field is optional with a `None` default — every existing call site
  (Claude, Gemini, all reports, condensation) is unaffected. Only
  `OllamaProvider.generate()` reads it, and only when explicitly set.

```python
@dataclass
class GenerationRequest:
    # ... existing fields ...
    generation_options: Optional[Dict[str, Any]] = None
    # Passed through to OllamaProvider options dict when set.
    # Claude/Gemini providers ignore this field.
    # For workmain-intent:latest, leave None — Modelfile owns all generation params.
    # Only set if you need to override a specific parameter per-request.
```

- Version bump to v1.2
- Version history entry:
  ```
  - v1.2: Gate 1 Phase 13 Sprint 1 — remove ProviderConfig dead code (Item 36);
           add generation_options: Optional[Dict[str, Any]] = None to GenerationRequest
  ```

Verify no remaining imports of `ProviderConfig` anywhere in the codebase:
```bash
grep -r "ProviderConfig" workmain/ --include="*.py"
# Expected: 0 results (only the class definition, which is being deleted)
```

### 1b — OllamaProvider Implementation

**File:** `workmain/ai/providers/ollama.py`

The stub at v1.0 satisfies the BaseProvider ABC but raises `NotImplementedError`
on all methods. Replace with a real implementation.

#### `check_availability() -> ProviderStatus`

The ABC declares `check_availability() -> ProviderStatus`. Return
`ProviderStatus.AVAILABLE` if the model is reachable, `ProviderStatus.UNAVAILABLE`
otherwise. Never return a plain bool — `BaseProvider.test_connection()` compares
against `ProviderStatus.AVAILABLE`, and `True == ProviderStatus.AVAILABLE` evaluates
to `False`, causing `providers test ollama` to always report unavailable even when
Ollama is fully up.

```python
def check_availability(self) -> ProviderStatus:
    try:
        url = f"http://{self._host}:{self._port}/api/tags"
        resp = urllib.request.urlopen(url, timeout=self._timeout)
        data = json.loads(resp.read())
        available = [m["name"] for m in data.get("models", [])]
        # Match on prefix: "mistral" matches "mistral:latest", "mistral:7b", etc.
        model_base = self._model.split(":")[0]
        if any(m.split(":")[0] == model_base for m in available):
            return ProviderStatus.AVAILABLE
        return ProviderStatus.UNAVAILABLE
    except Exception:
        return ProviderStatus.UNAVAILABLE
```

#### `generate(request: GenerationRequest) -> GenerationResponse`

Call `POST http://<host>:<port>/api/generate` with streaming disabled
(`"stream": false`). The request body uses Ollama's generate API format.

```python
def generate(self, request: GenerationRequest) -> GenerationResponse:
    # Note: check_availability() makes a GET /api/tags round-trip before every
    # generate call. For a LAN Ollama instance this adds ~5-20ms — acceptable
    # for intent parsing. This is a deliberate safety gate: avoids sending a
    # POST /api/generate to a host that is down.
    if self.check_availability() != ProviderStatus.AVAILABLE:
        raise ProviderUnavailableError(
            f"Ollama ({self._model}) unreachable at {self._host}:{self._port}"
        )

    # The workmain-intent Modelfile owns temperature, top_p, top_k, repeat_penalty.
    # Only num_predict (max_tokens) is sent per-request since it can legitimately
    # vary by call type. Do not re-send temperature or other params — let the
    # Modelfile defaults govern generation quality.
    #
    # generation_options on the request is reserved for future cases where a
    # specific per-request override is needed. Merge it last so it can override
    # the num_predict default if required.
    options = {"num_predict": request.max_tokens or 512}
    if request.generation_options:
        options.update(request.generation_options)

    payload = {
        "model": self._model,
        "prompt": self._build_prompt(request),
        "stream": False,
        "options": options,
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"http://{self._host}:{self._port}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=self._timeout)
        result = json.loads(resp.read())
        response_text = result.get("response", "").strip()
        prompt_tokens = result.get("prompt_eval_count", 0)
        completion_tokens = result.get("eval_count", 0)

        return GenerationResponse(
            content=response_text,
            provider=ProviderType.OLLAMA,
            model=self._model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            tokens_used=prompt_tokens + completion_tokens,
            cost=0.0,  # Local model — no API cost
        )
    except urllib.error.URLError as e:
        raise ProviderUnavailableError(
            f"Ollama request failed: {e}"
        ) from e
```

#### `_build_prompt(request: GenerationRequest) -> str`

Concatenate system prompt (if present) and user message in Mistral's expected
instruction format:

```python
def _build_prompt(self, request: GenerationRequest) -> str:
    # GenerationRequest uses request.prompt (not user_message)
    if request.system_prompt:
        return f"[INST] {request.system_prompt}\n\n{request.prompt} [/INST]"
    return f"[INST] {request.prompt} [/INST]"
```

#### Constructor and config loading

Read `host`, `port`, `model`, and `timeout` from the config dict passed by
ProviderManager (same pattern as ClaudeProvider and GeminiProvider).

**Important:** `super().__init__(config)` must be called first. The existing stub
calls it and the replacement must too — without it, `BaseProvider.__init__` never
runs, leaving `self.config`, `self._status`, and `self._last_error` unset.
`_set_status()` and the `status` property will raise `AttributeError` on first use.

**Attribute visibility check:** The existing stub uses public attributes
(`self.model`, `self.host`, `self.port`). This spec switches to private
(`self._model`, `self._host`, `self._port`). Before implementing, Claude Code must
check whether `test_provider_foundation.py` accesses `provider.model`,
`provider.host`, or `provider.port` directly. If it does, either keep the public
names or add public properties — do not silently break existing tests.

```python
def __init__(self, config: dict):
    super().__init__(config)          # Required — sets self.config, self._status, self._last_error
    self._host = config.get("host", "localhost")
    self._port = config.get("port", 11434)
    self._model = config.get("model", "mistral")
    self._timeout = config.get("timeout", 120)
```

#### Version bump

`v1.0 → v1.1`. Version history entry:
```
- v1.1: Gate 1 Phase 13 Sprint 1 — implement generate(), check_availability(),
        _build_prompt(); real HTTP calls replacing NotImplementedError stubs
```

### 1c — ai_settings.json: Enable Ollama

Update `config/ai_settings.json` to activate the Ollama provider:
- Set `providers.ollama.enabled` to `true`
- Set `providers.ollama.host` to `"workmain-ollama.lab.haloschaos.com"`
- Set `providers.ollama.port` to `11434`
- Set `providers.ollama.model` to `"workmain-intent:latest"` — this is the Modelfile-compiled
  variant, not the base mistral:latest. Must be built via build_workmain_intent.sh first.
- Set `providers.ollama.timeout` to `120` (cold-start model load on Proxmox CPU takes ~55s;
  120s provides headroom. Sprint 2 warm-up ping eliminates cold-start in normal operation.)

**Do not change any other provider settings.** Claude and Gemini remain primary
for report generation and condensation. Ollama is only used when explicitly
requested (intent parsing). The `enabled` flag controls whether ProviderManager
registers the provider — it does not affect report routing.

### 1d — Migration 018: Extend ai_costs CHECK Constraint

**File:** `workmain/database/migrations/018_extend_ai_costs_interaction_type.sql`

The `ai_costs` table was created in v1.17.0 with:
```sql
CHECK (interaction_type IN ('report', 'condensation'))
```

Intent parsing calls must be cost-tracked. Extend the constraint to include
`'intent_parse'`:

```sql
-- WorkmAIn Migration 018
-- Extend ai_costs interaction_type CHECK constraint for intent_parse
-- 20260605

ALTER TABLE ai_costs DROP CONSTRAINT IF EXISTS ai_costs_interaction_type_check;

ALTER TABLE ai_costs
    ADD CONSTRAINT ai_costs_interaction_type_check
    CHECK (interaction_type IN ('report', 'condensation', 'intent_parse'));
```

**Verify migration:**
```bash
psql -U workmain_user -d workmain -c "\d ai_costs" | grep -A5 "interaction_type"
# Confirm CHECK constraint includes 'intent_parse'
```

Also update `workmain/database/models.py`: add `'intent_parse'` to the
`interaction_type` CHECK constraint in the `AiCost` model definition to keep
model and schema in sync. Version bump models.py accordingly.

### 1e — `providers test ollama` Verification

The `providers test <name>` command was implemented in v1.18.0 and calls
`provider.check_availability()`. With the real implementation in place, it should
work for Ollama without code changes. Verify:

```bash
workmain providers test ollama
```

Expected output: confirmation that Ollama is reachable and `workmain-intent:latest`
is available. The check_availability() prefix match confirms `workmain-intent`
matches `workmain-intent:latest` in the /api/tags response.

If the command fails or produces an unexpected error, diagnose and fix before
proceeding.

### 1f — Gate 1 Tests

**File:** `tests/test_ollama_provider.py` (new, v1.0)

Write unit tests covering:

```
test_check_availability_success
    Mock urllib response returning model list that includes configured model.
    Assert check_availability() returns ProviderStatus.AVAILABLE.

test_check_availability_model_absent
    Mock urllib response returning model list that does NOT include configured model.
    Assert check_availability() returns ProviderStatus.UNAVAILABLE.

test_check_availability_connection_refused
    Mock urllib raising URLError (connection refused).
    Assert check_availability() returns ProviderStatus.UNAVAILABLE (never raises).

test_check_availability_timeout
    Mock urllib raising socket.timeout.
    Assert check_availability() returns ProviderStatus.UNAVAILABLE (never raises).

test_generate_success
    Mock urllib POST response returning valid Ollama generate response JSON.
    Assert GenerationResponse.content is populated.
    Assert GenerationResponse.provider == ProviderType.OLLAMA.
    Assert GenerationResponse.cost == 0.0.
    Assert prompt_tokens and completion_tokens populated from prompt_eval_count/eval_count.
    Assert tokens_used == prompt_tokens + completion_tokens.

test_generate_provider_unavailable
    check_availability mocked to return ProviderStatus.UNAVAILABLE.
    Assert generate() raises ProviderUnavailableError.

test_generate_network_error
    Mock urllib raising URLError during POST.
    Assert generate() raises ProviderUnavailableError.

test_build_prompt_with_system
    Assert [INST] format includes system prompt and request.prompt correctly.

test_build_prompt_without_system
    Assert [INST] format with request.prompt only (no system prompt wrapper).

test_model_prefix_matching
    Config model = "mistral", tags response includes "mistral:latest".
    Assert check_availability() returns ProviderStatus.AVAILABLE (prefix match).
```

Run full suite:
```bash
python -m pytest tests/ -q
# Expected: 479 + new tests passed, 0 failed
```

### Gate 1 Commit

```bash
git add workmain/ai/base_provider.py \
        workmain/ai/providers/ollama.py \
        config/ai_settings.json \
        workmain/database/migrations/018_extend_ai_costs_interaction_type.sql \
        workmain/database/models.py \
        tests/test_ollama_provider.py
git commit -m "feat(phase13-sprint1): OllamaProvider generate/check_availability/ProviderStatus; migration 018 intent_parse; Item 36 ProviderConfig removed"
```

**STOP:** Report Gate 1 results:
- `providers test ollama` output
- Test count (479 + N passed, 0 failed)
- Migration 018 applied and verified

Do not proceed to Gate 2 until all checks pass.

---

## Gate 2 — Intent Parse Prompt + Benchmark (HARD STOP)

**Purpose:** Build the intent-parsing prompt, run it against a defined benchmark
set of sample inputs on the live Mistral instance, and produce a structured
results report for user review and approval.

**This gate does not complete until the user explicitly approves the results.**

### 2a — Intent Parser Module

**File:** `workmain/ai/intent_parser.py` (new, v1.0)

This module is the single entry point for all intent parsing. It loads the prompt
template, constructs the request, calls OllamaProvider, parses the JSON response,
and handles malformed output gracefully.

```python
"""
WorkmAIn Intent Parser
workmain/ai/intent_parser.py
v1.0
20260605

Parses natural language input (Slack DM messages) into structured action JSON
using Mistral 7B via OllamaProvider.
"""

import json
import logging
from pathlib import Path
from workmain.ai.provider_manager import get_provider_manager
from workmain.ai.base_provider import GenerationRequest, ProviderUnavailableError, ProviderType

logger = logging.getLogger(__name__)

PROMPT_CONFIG_PATH = Path("config/intent_parse_prompt.json")


class IntentParseError(Exception):
    """Raised when Mistral returns output that cannot be parsed as valid JSON."""
    pass


class IntentParser:
    """
    Parses natural language user input into structured action dicts.

    All parsed actions are returned as dicts conforming to the action schema
    defined in config/intent_parse_system_prompt.txt. Generation parameters
    (temperature, max_tokens, generation_options) are in intent_parse_prompt.json.
    Callers are responsible for presenting actions to the user for confirmation
    before any database write.
    """

    def __init__(self):
        self._prompt_config = self._load_prompt_config()
        self._system_prompt = self._load_system_prompt()
        self._provider_manager = get_provider_manager()

    def _load_prompt_config(self) -> dict:
        if not PROMPT_CONFIG_PATH.exists():
            raise FileNotFoundError(
                f"Intent parse prompt config not found: {PROMPT_CONFIG_PATH}"
            )
        with open(PROMPT_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_system_prompt(self) -> str:
        system_prompt_path = Path(
            self._prompt_config.get("system_prompt_file",
                                    "config/intent_parse_system_prompt.txt")
        )
        if not system_prompt_path.exists():
            raise FileNotFoundError(
                f"Intent parse system prompt not found: {system_prompt_path}"
            )
        with open(system_prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()

    def parse(self, user_message: str) -> dict:
        """
        Parse a natural language message into a structured action dict.

        Returns a dict with at minimum an "action" key. If the action is
        "unknown", a "follow_up" key contains a clarifying question for the user.

        Raises IntentParseError if Mistral returns non-JSON output.
        Raises ProviderUnavailableError if Ollama is unreachable.
        """
        # system_prompt=None: the workmain-intent Modelfile owns the system prompt.
        # Injecting it here would double the instruction surface and defeat the
        # purpose of the Modelfile (keeping the context window clean).
        # The txt file is the human-readable source of truth for the Modelfile
        # SYSTEM block — it is NOT a runtime artifact.
        #
        # generation_options not set: Modelfile PARAMETER blocks own
        # temperature/top_p/top_k/repeat_penalty. Only max_tokens is per-request.
        request = GenerationRequest(
            system_prompt=None,
            prompt=user_message,
            max_tokens=self._prompt_config.get("max_tokens", 256),
        )

        # provider_manager.generate() signature:
        #   generate(request, provider_override: Optional[ProviderType]) -> Tuple[GenerationResponse, bool]
        # - kwarg is provider_override, not provider_name
        # - takes ProviderType enum, not a plain string
        # - returns a tuple; unpack the bool (fallback_used) and discard it
        response, _fallback_used = self._provider_manager.generate(
            request, provider_override=ProviderType.OLLAMA
        )
        raw = response.content.strip()

        # Strip markdown code fences if Mistral wraps output despite instructions
        if raw.startswith("```"):
            lines = raw.splitlines()
            raw = "\n".join(
                l for l in lines
                if not l.strip().startswith("```")
            ).strip()

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.warning("Intent parse failed — raw output: %s", raw)
            raise IntentParseError(
                f"Mistral returned non-JSON output: {raw[:200]}"
            ) from e

        if "action" not in result:
            raise IntentParseError(
                f"Parsed JSON missing 'action' key: {result}"
            )

        return result
```

### 2b — Intent Parse Config Files

The system prompt is extracted from the JSON config into its own text file.
This separation has three benefits:
- The prompt is human-readable and editable without touching JSON syntax
- Both this planning Claude and the user can read and iterate on it directly
- Generation parameters (temperature, tokens, options) stay in JSON where they belong

**File 1: `config/intent_parse_prompt.json`** (new — generation parameters only)

```json
{
  "_doc": {
    "name": "WorkmAIn Intent Parse — Generation Config",
    "description": "Generation parameters for Mistral 7B intent parsing via Ollama. Controls max_tokens only at runtime — temperature/top_p/top_k/repeat_penalty are baked into the Modelfile and are listed here as the editable reference for rebuilds.",
    "system_prompt_source": "config/intent_parse_system_prompt.txt",
    "ollama_model": "workmain-intent:latest",
    "ollama_host": "workmain-ollama.lab.haloschaos.com:11434",
    "config_version": "1.1",
    "config_updated": "20260605",
    "model_built": "",
    "notes": "After editing generation_options, update Modelfile PARAMETER blocks to match, rebuild model via build_workmain_intent.sh, then set model_built to today\'s date."
  },
  "system_prompt_file": "config/intent_parse_system_prompt.txt",
  "max_tokens": 256,
  "temperature": 0.4,
  "generation_options": {
    "_comment": "Reference only — runtime source of truth is Modelfile PARAMETER blocks. Edit here first, then sync to Modelfile and rebuild.",
    "top_p": 0.9,
    "top_k": 40,
    "repeat_penalty": 1.1
  }
}
```

**File 2: `config/intent_parse_system_prompt.txt`** (new — full system prompt, human-readable)

The file opens with a header comment block so both humans and tooling can identify
which version is in the repo versus what was last compiled into Ollama.

```
# ============================================================
# WorkmAIn Intent Parse — System Prompt
# ============================================================
# config_version:    1.0
# config_updated:    20260605
# ollama_model:      workmain-intent-1
# ollama_host:       workmain-ollama.lab.haloschaos.com:11434
# model_built:       (set this when build_workmain_intent.sh is run)
#
# Description:
#   System prompt for Mistral 7B intent parsing. Defines 7 action types
#   with examples and inference rules. This file is the source of truth —
#   the Modelfile SYSTEM block must match this content exactly.
#
# Versioning:
#   Increment config_version on any content change.
#   Increment ollama_model suffix (workmain-intent-1, workmain-intent-2)
#   when rebuilding the Ollama model so you can track which prompt version
#   is compiled on the host. Update model_built date after each rebuild.
#   Update ollama_model in ai_settings.json to match the new model name.
#
# Tuning workflow:
#   1. Edit this file
#   2. Sync SYSTEM block to ollama-lxc/models/workmain-intent/Modelfile
#   3. Run build_workmain_intent.sh on Proxmox LXC
#   4. Update model_built date above and ollama_model if version incremented
#   5. Update ai_settings.json model field if model name changed
# ============================================================

You are a work management assistant for a cybersecurity engineer. The user sends
short messages describing what they are working on or what they want to do. Your
job is to identify the action they want to take and return ONLY a valid JSON
object — no explanation, no markdown, no preamble.

IMPORTANT: If the user's message begins with "note:" or "Note:", always use the
create_note action. This takes priority over all other rules.

Valid actions and their required fields:

1. create_note
   Required: content (string)
   Optional: tags (array of strings from: internal-only, client-report,
             info-only, carry-forward, blocker)
   Example input: "note: PR automation pipeline throwing 404 on merge trigger"
   Example output: {"action": "create_note", "content": "PR automation pipeline
                    throwing 404 on merge trigger"}
   Example input: "note: XSOAR migration blocked waiting on dev environment access"
   Example output: {"action": "create_note", "content": "XSOAR migration blocked
                    waiting on dev environment access", "tags": ["carry-forward", "blocker"]}

2. create_time_entry
   Required: duration_minutes (integer), description (string)
   Optional: project (string)
   IMPORTANT: duration_minutes is in minutes. Do NOT convert minutes to anything
   else. Only convert hours to minutes (2 hours = 120, 90 min = 90, 30 min = 30).
   Example input: "spent 2 hours on the XSOAR migration"
   Example output: {"action": "create_time_entry", "duration_minutes": 120,
                    "description": "XSOAR migration"}
   Example input: "logged 30 min for email triage"
   Example output: {"action": "create_time_entry", "duration_minutes": 30,
                    "description": "email triage"}

3. update_task
   Required: task_description (string), status (one of: completed, dismissed, deferred)
   Example input: "finished the Splunk normalization review"
   Example output: {"action": "update_task", "task_description": "Splunk normalization
                    review", "status": "completed"}

4. confirm_report
   Required: report_type (one of: daily_internal, weekly_client)
   Example input: "daily report looks good, confirm it"
   Example output: {"action": "confirm_report", "report_type": "daily_internal"}

5. correct_report
   Required: report_type (one of: daily_internal, weekly_client), correction (string)
   Example input: "fix the daily — I spent 2 hours on XSOAR not 90 minutes"
   Example output: {"action": "correct_report", "report_type": "daily_internal",
                    "correction": "XSOAR time should be 120 minutes not 90"}

6. defer_task
   Required: task_description (string)
   Example input: "push the PR review to tomorrow"
   Example output: {"action": "defer_task", "task_description": "PR review"}

7. unknown
   Use when the input does not match any action or is too ambiguous to parse.
   Required: follow_up (string — a short clarifying question)
   Example input: "hey what's the weather like"
   Example output: {"action": "unknown", "follow_up": "What would you like to do?
                    I can log time, add a note, update a task, or confirm/correct
                    a report."}

Rules:
- Return ONLY the JSON object. No other text.
- If the input begins with "note:" or "Note:", always use create_note.
- If duration is given in hours, convert to minutes. duration_minutes is already
  in minutes — do NOT convert further.
- If the input mentions being blocked or waiting on something external, infer
  the blocker tag.
- If the input mentions "still waiting", "ongoing", "need to follow up", or an
  unresolved item carrying into tomorrow, infer the carry-forward tag.
- When in doubt between two actions, return unknown with a clarifying question.
- Never invent fields not listed in the schema above.
```

**Notes on generation_options:**

These values are the **Modelfile source of truth** — edit them here, then sync
to the Modelfile PARAMETER blocks and rebuild. They are NOT sent per-request
at runtime (the Modelfile owns them). Only `max_tokens` is per-request.

- `temperature: 0.4` — natural language input is varied; 0.1 was too rigid.
  0.4 balances flexibility with JSON structure reliability.
- `top_p: 0.9` — nucleus sampling; limits token selection to 90% probability
  mass. Reduces low-probability hallucinations.
- `top_k: 40` — limits token selection to top 40 candidates. Works with top_p.
- `repeat_penalty: 1.1` — mild penalty for repeating tokens; reduces output loops.

**To change any of these:** edit the JSON, update the Modelfile PARAMETER blocks
to match, run `build_workmain_intent.sh`, increment `ollama_model` version suffix
in the txt file header, update `model_built` date, update `ai_settings.json`
model field to the new model name.

### 2c — Benchmark Sample Set

Claude Code must run the following 10 inputs through `IntentParser.parse()` on
the live `workmain-intent:latest` model (NOT mistral:latest directly). Confirm
`ai_settings.json` has `model: "workmain-intent:latest"` before running.
This ensures the benchmark tests the Modelfile-compiled behavior, not the
base model with context-window prompt injection.

**Do not modify or filter the outputs.** Present them exactly as returned
(after JSON parsing) in the benchmark report.

```python
BENCHMARK_INPUTS = [
    # Clean inputs — unambiguous
    "spent 90 minutes on the TIE team XSOAR migration",
    "finished the Splunk normalization doc review",
    "note: PR automation pipeline throwing 404 on merge trigger",

    # Tag inference
    "still waiting on dev environment access from the TIE team, blocking XSOAR work",
    "need to follow up with Matt on the normalization schema tomorrow",

    # Report actions
    "daily report looks good, confirm it",
    "fix the daily — I spent 2 hours on XSOAR not 90 minutes",

    # Ambiguous / multi-intent
    "done with standup, also logged 30 min for email triage",
    "working on the Splunk alert fidelity metrics for Emily",

    # Out of scope
    "hey what's the weather like",
]
```

### 2d — Benchmark Report Format

Claude Code must present results in this exact format for each input:

```
--- Sample 1 ---
Input:    "spent 90 minutes on the TIE team XSOAR migration"
Output:   {"action": "create_time_entry", "duration_minutes": 90, "description": "TIE team XSOAR migration"}
Latency:  X.Xs
Pass/Fail: PASS — action correct, fields complete
```

For each result, Claude Code must assess:
- **Action** — is the action type correct for this input?
- **Fields** — are all required fields present and correctly populated?
- **Tag inference** — for inputs 4 and 5, are the correct tags inferred?
- **Ambiguity handling** — for inputs 8 and 9, is the output reasonable?
- **Unknown handling** — for input 10, does it return `unknown` with a `follow_up`?

After all 10 results, provide a summary:
```
Benchmark Summary
-----------------
Passed:   X/10
Failed:   X/10
Latency:  avg Xs, max Xs

Issues identified:
- [list any incorrect actions, missing fields, wrong tag inferences]
```

**HARD STOP:** Claude Code presents the benchmark report and waits.
Do not proceed to Gate 3 until the user reviews the report and explicitly
approves it or requests prompt tuning.

**If prompt tuning is needed:** The user and planning Claude will update
`config/intent_parse_prompt.json` together in this session, then re-hand off
to Claude Code to re-run the benchmark. Repeat until approved.

### Gate 2 Commit (after user approval only)

```bash
git add workmain/ai/intent_parser.py \
        config/intent_parse_prompt.json
git commit -m "feat(phase13-sprint1): IntentParser + intent_parse_prompt.json; benchmark approved"
```

---

## Gate 3 — Intent Parser Tests + Cost Tracking

**Purpose:** Unit tests for IntentParser, and wire intent parse calls through
the cost tracking path.

### 3a — IntentParser Tests

**File:** `tests/test_intent_parser.py` (new, v1.0)

```
test_parse_create_time_entry
    Mock OllamaProvider returning valid JSON for a time entry input.
    Assert returned dict has action='create_time_entry', duration_minutes, description.

test_parse_update_task
    Mock returning valid JSON for a task completion input.
    Assert returned dict has action='update_task', task_description, status='completed'.

test_parse_create_note_with_tags
    Mock returning valid JSON with tags array.
    Assert tags field is a list; known tag values present.

test_parse_confirm_report
    Mock returning valid JSON for confirm_report.
    Assert report_type field present.

test_parse_unknown
    Mock returning {"action": "unknown", "follow_up": "What would you like to do?"}.
    Assert action='unknown', follow_up key present.

test_parse_strips_markdown_fences
    Mock returning output wrapped in ```json ... ``` fences.
    Assert IntentParser strips fences and parses correctly.

test_parse_raises_intent_parse_error_on_bad_json
    Mock returning plain English text (not JSON).
    Assert IntentParseError raised.

test_parse_raises_intent_parse_error_on_missing_action_key
    Mock returning {"result": "something"} — valid JSON but no action key.
    Assert IntentParseError raised.

test_parse_raises_provider_unavailable
    self._provider_manager.generate() mocked to raise ProviderUnavailableError directly.
    Note: do NOT mock OllamaProvider.check_availability — it never raises, it returns
    ProviderStatus. Do NOT mock OllamaProvider.generate() — ProviderManager.generate()
    catches ProviderError/RateLimitError and re-wraps before it exits the manager,
    so the exception never reaches parse(). Mock at the ProviderManager level instead,
    bypassing the manager's catch/re-wrap logic entirely.
    Assert ProviderUnavailableError propagates from parse().

test_prompt_config_loads
    Assert IntentParser() initialises without error when both config JSON and
    system prompt text file exist.

test_prompt_config_missing_raises
    Config JSON absent; assert FileNotFoundError on IntentParser().

test_system_prompt_missing_raises
    Config JSON present but system_prompt_file path does not exist;
    assert FileNotFoundError on IntentParser().
```

### 3b — Cost Tracking for Intent Parse Calls

Intent parse calls should be tracked in `ai_costs` with `interaction_type='intent_parse'`.
Wire this in `IntentParser.parse()` after a successful generation:

```python
# After successful response and JSON parse, record cost
# Session pattern: from workmain.database.connection import get_db (not .session)
# AiCostRepository.create() fields: prompt_tokens, completion_tokens (not input/output_tokens)
# GenerationResponse fields after Issue 1 fix: response.prompt_tokens, response.completion_tokens
try:
    from workmain.database.connection import get_db
    from workmain.database.repositories.ai_costs_repo import AiCostRepository
    db = get_db()
    session = db.get_session()
    repo = AiCostRepository(session)
    repo.create(
        provider="ollama",
        model=response.model,
        interaction_type="intent_parse",
        prompt_tokens=response.prompt_tokens,
        completion_tokens=response.completion_tokens,
        cost_usd=0.0,  # Local model — no API cost (AiCostRepository.create() uses cost_usd)
    )
    session.close()
except Exception as cost_err:
    logger.warning("Cost tracking failed for intent parse: %s", cost_err)
    # Non-fatal — do not interrupt parse result
```

Cost tracking failure must never interrupt the parse result. Wrap in try/except.

Update `intent_parser.py` to v1.1 with version history entry:
```
- v1.1: Gate 3 — wire ai_costs tracking for intent_parse interactions
```

### 3c — `providers costs` Display

Confirm `workmain providers costs` displays `intent_parse` rows once a real
parse has run. No code change should be needed — the command reads from `ai_costs`
and filters by `interaction_type`. Run manually after Gate 3 tests pass to verify.

### Gate 3 Commit

```bash
git add workmain/ai/intent_parser.py \
        tests/test_intent_parser.py
git commit -m "feat(phase13-sprint1): IntentParser tests + ai_costs cost tracking for intent_parse"
```

**STOP:** Report Gate 3 results:
- Test count (all passing, 0 failed)
- `providers costs` output showing intent_parse row (after a manual parse run)

---

## Gate 4 — Version Bump, Changelog, Backlog, Handoff

### 4a — Version Bump

**File:** `workmain/__version__.py`

Bump to `v1.19.0`. Version history entry:

```
- v1.19.0: Phase 13 Sprint 1 — Ollama Provider Activation. OllamaProvider fully
           implemented (generate, check_availability, _build_prompt); Mistral 7B
           on Proxmox. intent_parser.py: natural language → structured JSON action
           dict via Ollama; benchmark-validated against 10 sample inputs.
           config/intent_parse_system_prompt.txt: human-readable system prompt
           (source of truth for Modelfile). workmain-intent:latest Modelfile compiled
           from system prompt + generation parameters via build_workmain_intent.sh.
           config/intent_parse_prompt.json: generation parameters only (temperature
           0.4, top_p, top_k, repeat_penalty). Migration 018:
           ai_costs interaction_type CHECK extended for 'intent_parse'.
           Gate 0 fix: note_condenser.py v2.1 — broken _format_writing_style_context
           replaced with StyleAdapter for consistent AI voice. Item 36 closed:
           ProviderConfig dead code removed from base_provider.py.
           New tests: test_ollama_provider.py, test_intent_parser.py.
```

### 4b — CHANGELOG.md Entry

```markdown
## [1.19.0] - 2026-06-XX

### Added
- `workmain/ai/providers/ollama.py` v1.1 — OllamaProvider fully implemented:
  `generate()` (POST /api/generate, stream=false), `check_availability()`
  (GET /api/tags, model prefix matching), `_build_prompt()` (Mistral [INST] format)
- `workmain/ai/intent_parser.py` — IntentParser: natural language Slack DM input →
  structured JSON action dict via Mistral 7B; markdown fence stripping; IntentParseError
  on non-JSON output; ai_costs tracking for intent_parse interactions
- `config/intent_parse_prompt.json` — generation parameters (temperature: 0.4,
  max_tokens, generation_options: top_p/top_k/repeat_penalty); references system_prompt_file
- `config/intent_parse_system_prompt.txt` — human-readable system prompt; 7 action types
  with examples, tag inference rules; source of truth for Modelfile SYSTEM block
- `ollama-lxc/models/workmain-intent/Modelfile` — Ollama Modelfile; compiles system prompt
  and generation parameters into workmain-intent:latest custom model variant
- Migration 018 — extend ai_costs interaction_type CHECK to include 'intent_parse'
- `tests/test_ollama_provider.py` — OllamaProvider unit tests (10 cases)
- `tests/test_intent_parser.py` — IntentParser unit tests (11 cases)

### Fixed
- `workmain/ai/note_condenser.py` v2.1 — replace broken `_format_writing_style_context`
  (queried non-existent JSON keys, always returned empty) with `StyleAdapter.get_style_prompt`
  for consistent AI voice across condensation and reports

### Removed
- `ProviderConfig` dataclass from `workmain/ai/base_provider.py` — dead code since
  v1.18.0, no remaining consumers (Item 36)

### Database
- Migration 018: `ai_costs` CHECK constraint extended for `'intent_parse'`
```

### 4c — Feature Backlog Updates

**File:** `docs/FEATURE_BACKLOG.md`

- Item 36 — mark **COMPLETE** (v1.19.0, ProviderConfig removed in Gate 1)
- Item 19 — update status note: "CPU path delivered in Phase 13 Sprint 1 (v1.19.0);
  GPU offloading via RTX 4070 remains deferred"
- Add new item: "Ollama Modelfile tuning workflow — workmain-intent:latest Modelfile
  delivered in Sprint 1. As action vocabulary grows in Sprint 2/3, rebuild the model
  after each schema update. Long-term: consider fine-tuning on actual WorkmAIn inputs
  once sufficient real usage data is accumulated. Target: ongoing Sprint 2/3 maintenance."
- Update Summary Statistics accordingly
- Bump FEATURE_BACKLOG.md version

### 4d — Merge Flow

```bash
# Ensure all tests pass
python -m pytest tests/ -q
# Expected: all passed, 0 failed

# Step 1 — merge feature branch into dev (local, no-ff)
git checkout dev
git merge --no-ff feature/phase-13-sprint1-ollama-provider \
    -m "feat(phase13-sprint1): merge Ollama Provider Activation into dev"
git push origin dev

# Step 2 — dev -> main MUST go through a GitHub PR (never a local merge)
# Per GIT_WORKFLOW_STANDARDS: open PR on GitHub, wait for review/merge there
gh pr create \
    --base main \
    --head dev \
    --title "release: v1.19.0 — Phase 13 Sprint 1 Ollama Provider Activation" \
    --body "Merges Phase 13 Sprint 1 into main. See CHANGELOG [1.19.0] for details."
# Merge the PR on GitHub, then pull main locally
git checkout main
git pull origin main

# Step 3 — tag and push
git tag -a v1.19.0 -m "Phase 13 Sprint 1 — Ollama Provider Activation"
git push origin v1.19.0

# Step 4 — delete feature branch (local only — was never pushed to remote)
git branch -d feature/phase-13-sprint1-ollama-provider

# Step 5 — GitHub Release
# Create release at v1.19.0 tag with CHANGELOG [1.19.0] entry as body
```

### 4e — Session Handoff

Create `docs/dev/handoffs/SESSION_HANDOFF_PHASE13_SPRINT1_COMPLETE_<YYYYMMDD>.md`

Required sections:
- Sprint summary (what was built)
- Gate log (gate number, description, commit hash)
- File versions at v1.19.0 (all modified files)
- Benchmark report (the Gate 2 results, preserved for Sprint 2 reference)
- Known issues / deferred
- Sprint 2 prerequisites and first tasks

---

## Gate Summary

| Gate | Deliverable | Hard Stop |
|------|-------------|-----------|
| 0 | Baseline verify + Ollama infra check + writing style fix + branch cut | Yes — infra must be confirmed |
| 1 | OllamaProvider implementation + Migration 018 + Item 36 | Yes — report before Gate 2 |
| 2 | Intent prompt + benchmark 10 samples | **YES — user approval required** |
| 3 | IntentParser tests + cost tracking wire | Yes — report test count |
| 4 | Version bump, CHANGELOG, backlog, merge, handoff | No — proceed through |

---

## File Manifest

### New Files
| File | Version | Gate |
|------|---------|------|
| `config/intent_parse_prompt.json` | v1.1 | 2 |
| `config/intent_parse_system_prompt.txt` | — | 2 |
| `ollama-lxc/models/workmain-intent/Modelfile` | — | 2 (IaC repo) |
| `workmain/ai/intent_parser.py` | v1.1 | 2/3 |
| `workmain/database/migrations/018_extend_ai_costs_interaction_type.sql` | — | 1 |
| `tests/test_ollama_provider.py` | v1.0 | 1 |
| `tests/test_intent_parser.py` | v1.0 | 3 |

### Modified Files
| File | Version Change | Gate |
|------|---------------|------|
| `workmain/ai/providers/ollama.py` | v1.0 → v1.1 | 1 |
| `workmain/ai/base_provider.py` | v1.1 → v1.2 | 1 |
| `workmain/ai/note_condenser.py` | v2.0 → v2.1 | 0 |
| `workmain/database/models.py` | bump | 1 |
| `config/ai_settings.json` | ollama enabled | 1 |
| `workmain/__version__.py` | v1.18.3 → v1.19.0 | 4 |
| `CHANGELOG.md` | [1.19.0] entry | 4 |
| `docs/FEATURE_BACKLOG.md` | Items 36/19 updated | 4 |

---

## Out of Scope — Sprint 1

The following must not be built in Sprint 1. If Claude Code identifies a
dependency or natural extension, log it to FEATURE_BACKLOG.md and continue.

| Item | Target |
|------|--------|
| Inbound Slack polling | Sprint 2 |
| Action executor / orchestration | Sprint 2 |
| Confirmation UX (Block Kit) | Sprint 2 |
| T1–T6 trigger types | Sprint 3 |
| Item 32 (task deduplication) | Sprint 3 |
| Item 33 (correction_note population) | Sprint 3 |
| Item 34 (weekly report confirmed dailies) | Sprint 3 |
| GPU offloading (Item 19 full scope) | Phase 14+ |
| Trigger time configuration UI | Phase 14 |

---

END OF SPEC
WorkmAIn PHASE13_SPRINT1_OLLAMA_PROVIDER_SPEC — v1.8 — 20260605
