# Provider Tests State Their Routing — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20261023
**Branch:** `hotfix/issue-236-provider-test-routing` (from `main`)
**Target release:** v1.52.2
**Originating item:** Issue #236
**Design study:** `../design/DESIGN_PROVIDER_TEST_ROUTING.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261023 | Ray | Design study Q1: Option A — `stubbed_manager` takes the routing as a required argument. | DR1–DR3. |
| 20261023 | Ray | Design study Q2: a provider the test does not stub must not be reachable. | DR4. |
| 20261023 | Ray | Design study Q3: the routing change is committed under `docs/DEVELOPMENT_STANDARDS.md` §2.2 § Operational changes from live use, and #236's third AC ("The committed routing of daily_internal, weekly_client and note_condensation is Claude primary…") is removed from the issue. §2.2 is not changed. | Step 1. The issue's ACs are renumbered by that removal; this spec's `ACn.m` numbers follow the issue as it will read after the close-out edit: AC1 routing-independence, AC2 `stubbed_manager`, AC3 §6.2, AC4 full suite. |
| 20261023 | Ray | Design study Q4: Ray cut `providers.claude.notes` and `providers.gemini.notes` to the model name in the working tree. | Committed with the routing in Step 1. |
| 20261023 | Ray | Design study Q5: the swapped-routing check runs against an isolated copy of the tree, never the live file. | §6 Swapped-routing run. The issue's AC1 check wording is changed to match at close-out. |
| 20261023 | Caliper | 5: DR4 reaches only providers in `manager._providers`. A provider disabled in config or whose constructor failed (e.g. no key in `.env`) sits in `_disabled` or `_disabled_reasons` instead; `get_provider` raises `ProviderUnavailableError`, a `ProviderError`, which `generate` catches and falls back on — so a misrouted call falls back silently and the first §6 test depends on `.env`. Related: the stub loop clears `_disabled` but not `_disabled_reasons`, so a stub for a provider whose constructor failed is unreachable. | Accepted. DR4 covers every name in `manager.get_configured_provider_names()`, and for stubs and raising replacements alike sets `_providers[name]` and removes the name from `_disabled` and `_disabled_reasons`. §6's first test routes to a provider it names, so its result does not depend on `.env`. |
| 20261023 | Caliper | 4: Step 1 puts Ray's hand-trimmed `notes` in the §2.2 operational `chore(config)` commit, but §2.2 says that path "covers only a file a `workmain` command wrote. A hand edit to `config/` or `templates/` is development". Recommended two commits staged with `git add -p`. | Accepted, with a non-interactive staging method in place of `git add -p`, which cannot run in the implementer's harness: Step 1 stages the CLI-written hunks with `git apply --cached --unidiff-zero` (dry-run with `--check` against this branch, 20261023: five hunks stage, the two `notes` hunks remain). The `notes` trim is this issue's scope by Ray's Q4 answer; it carries no AC, since #236 does not ask for it and the edit is Ray's own. |
| 20261023 | Spanner | `drop_fallback` and `stubbed_manager`'s `edit` parameter are removed. `routing` states "no fallback" as `(primary, None)`, and `drop_fallback` is the only `edit` any caller passes (§2), so both are dead once routing is required. | DR3. |

---

## 1. Scope

**In scope:**

- `tests/mocks/stub_providers.py`: `stubbed_manager` takes the routing, refuses unstubbed providers, and loses `edit` and `drop_fallback`.
- Every `stubbed_manager` call site in §2, which passes its routing.
- `tests/test_compare_providers.py` `test_default_types_follow_routing`, which states the routing it asserts against.
- New tests pinning the helper's refusal of unstubbed providers, in `tests/test_provider_foundation.py`.
- `docs/DEVELOPMENT_STANDARDS.md` §6.2: the rule for tests that build a real `ProviderManager`.
- `config/ai_settings.json`: Ray's working-tree change, in two commits (Step 1) — the CLI-written routing as a §2.2 operational change, and Ray's hand trim of `providers.claude.notes` and `providers.gemini.notes` to the model name as this issue's development (design study Q4).

**Out of scope:**

- Test helpers that copy the live file but replace `pm.generate` before any routing is read, and the other sites in design study F7. They pass under both routings with no real call (design study §2 Runs), so routing does not decide their result.
- `tests/test_ai_costs.py::TestProviderManagerConfig::test_primary_differs_from_fallback` — a check of the live configuration; #132 owns it (#236 body).
- Caps, `accepts` and the provider set in the copied file. No command writes them; they change on a branch, with their tests (design study Option C).
- `tests/test_ai_providers_live.py`, which is billed by design.

## 2. Verified current state

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| `stubbed_manager` copies the live file, applies an optional `edit`, and replaces only the named providers. Its docstring says the routing is "the shipped ones unless `edit` changes the settings dict". | `tests/mocks/stub_providers.py:61-82` |
| `drop_fallback` is an `edit` that pops `fallback_provider` from each named call type in `report_types` or `application_functions`. | `tests/mocks/stub_providers.py:85-91` |
| Call sites of `stubbed_manager` and `drop_fallback`, found by `git grep -n 'stubbed_manager(\|drop_fallback(' -- .` and read: `tests/test_cost_display.py:214`; `tests/test_eod_workflow.py:1379` (with `drop_fallback`, `:1381`), `:1473`; `tests/test_intent_parser.py:433`, `:469`, `:492`; `tests/test_meetings_condense.py:216`; `tests/test_narration.py:130` (with `drop_fallback`, `:133`), `:151`; `tests/test_note_condenser.py:324` (with `drop_fallback`, `:326`), `:341`, `:363`, `:392`; `tests/test_provider_foundation.py:1349`, `:1373`, `:1395` (with `drop_fallback`, `:1401`), `:1427`, `:1453` (with `drop_fallback`, `:1456`), `:1475`; `tests/test_report_generator.py:262` (with `drop_fallback`, `:264`), `:282`, `:312`, `:347`. No hit outside `tests/`. The `_stubbed_manager(` hits in `test_intent_parser.py`, `test_note_condenser.py` and `test_report_generator.py` are each file's own local helper, not this one. No caller passes an `edit` other than `drop_fallback`. | the grep, run 20261023 |
| `ProviderManager.generate` catches only `ProviderError` and `RateLimitError` from the primary before trying the fallback. | `workmain/ai/provider_manager.py:273-315` |
| A provider disabled in config goes into `_disabled`; one whose constructor raises (e.g. no API key) goes into `_disabled_reasons`; neither is put in `_providers`. `get_provider` checks `_disabled_reasons`, then `_disabled`, before `_providers`, and raises `ProviderUnavailableError`, a `ProviderError`. `get_configured_provider_names()` returns every name under `providers`, enabled or not. | `workmain/ai/provider_manager.py:461-477`, `:119-146`, `:338-340`; `workmain/ai/base_provider.py:260` |
| The stub loop sets `_providers[name]` and discards the name from `_disabled`, but not from `_disabled_reasons`. | `tests/mocks/stub_providers.py:79-81` |
| No `except:` or `except BaseException` exists under `workmain/`, and `click.testing.CliRunner.invoke` catches `SystemExit` and `Exception` only. An exception deriving from `BaseException` but not `Exception` therefore leaves every application path and every `CliRunner` call a test makes, and pytest records it as a failure (probed 20261023). | `git grep -n 'except:\|except BaseException' -- workmain` (no hits); Click 8.1.7 `CliRunner.invoke` |
| `daemon/narration.py` catches `Exception` around its provider call and returns the plain observation text, which is how a misrouted call passed silently in design study F5. | `workmain/daemon/narration.py:57`; `tests/test_narration.py:55-66` relies on it |
| `workmain providers test <name>` calls `pm.get_provider(name).generate(...)` directly, not through any call type's routing. | `workmain/cli/commands/providers.py:139`, `:158` |
| `scripts/compare_providers.py` `_default_types` selects every `report_types` entry whose primary is the candidate. `test_default_types_follow_routing` asserts `expected >= {"daily_internal", "weekly_client", "note_condensation"}` against the live routing. `_manager`'s `routing` sets primaries only. | `scripts/compare_providers.py:73-78`; `tests/test_compare_providers.py:47-61`, `:167-186` |
| On this branch at `b39d432` with Ray's routing, and in an isolated copy with every fallback-bearing entry swapped, the failures and real vendor calls are as design study F3–F5 record. | design study §3 |
| `ProviderManager()` with no `config_path` reads `config/ai_settings.json` relative to the package, not the working directory. | `workmain/ai/provider_manager.py:438-440` |

## 3. Design rules

- **DR1 — The routing is an argument.** `stubbed_manager(tmp_path, stubs, routing)`. `routing` has no default. It maps each call type the test exercises to `(primary, fallback)`, where `fallback` is a provider name or `None`.
- **DR2 — The argument replaces the file's routing for those call types.** For each key, the helper finds the entry in `report_types`, else `application_functions`, of the copied settings, and sets `primary_provider`. It sets `fallback_provider` to the fallback, or removes it when the fallback is `None`. A key that is in neither block raises `KeyError` naming it. An empty mapping is valid for a test that reaches a provider by name only (`providers test`).
- **DR3 — `edit` and `drop_fallback` are removed.** `(primary, None)` states no fallback.
- **DR4 — An unstubbed provider is unreachable.** The helper goes over every name in `manager.get_configured_provider_names()`, enabled or not and whether or not its constructor succeeded. A name in `stubs` gets its stub; every other name gets a replacement whose `generate` and `check_availability` raise `UnstubbedProviderCall`, defined in `stub_providers.py` as a subclass of `BaseException`, not `Exception`, with a message naming the provider. For both, the helper sets `_providers[name]` and removes the name from `_disabled` and `_disabled_reasons`, so that `get_provider` returns what the test set and never raises `ProviderUnavailableError` — which `generate` would catch and fall back on — and so that the result does not depend on which keys are in `.env`. `UnstubbedProviderCall` derives from `BaseException` so that neither `ProviderManager.generate`'s fallback nor any `except Exception` in the application can turn the call into a passing result (§2).
- **DR5 — A call site's routing reproduces the routing it was written against.** Each site in §2 passes the routing in the table below: the committed routing at `b39d432` for its call types, with `None` where it passed `drop_fallback` for that call type. The site's stubs and assertions do not change.

| Site | `routing` |
| --- | --- |
| `test_cost_display.py:214`, `test_meetings_condense.py:216`, `test_eod_workflow.py:1473`, `test_note_condenser.py:341`, `:363`, `:392` | `{"note_condensation": ("gemini", "claude")}` |
| `test_note_condenser.py:324` | `{"note_condensation": ("gemini", None)}` |
| `test_eod_workflow.py:1379`, `test_provider_foundation.py:1395`, `:1453`, `test_report_generator.py:262` | `{"daily_internal": ("gemini", None)}` |
| `test_provider_foundation.py:1349`, `:1373`, `:1427`, `test_report_generator.py:282`, `:312`, `:347` | `{"daily_internal": ("gemini", "claude")}` |
| `test_narration.py:130` | `{"daemon_narration": ("claude", None)}` |
| `test_narration.py:151` | `{"daemon_narration": ("claude", "gemini")}` |
| `test_intent_parser.py:433`, `:469`, `:492` | `{"intent_parse": ("ollama", None), "task_match": ("ollama", None), "note_dedup": ("ollama", None)}` |
| `test_provider_foundation.py:1475` | `{}` |

- **DR6 — `test_default_types_follow_routing` states every report type's routing.** It routes every `report_types` entry in the copy to `claude`, then `daily_internal`, `weekly_client` and `note_condensation` to `gemini`, and asserts that `compare` selects exactly `{"daily_internal", "weekly_client", "note_condensation"}`. It then routes `daily_internal` to `claude` as well and asserts the selection is `{"weekly_client", "note_condensation"}`. Routing every entry, not only the three, is what stops a report type added to the file later from changing the result. `_manager`'s `routing` argument keeps its form (call type → primary), since `_default_types` reads primaries only.
- **DR7 — The docstring states the contract.** `stubbed_manager`'s docstring says the routing comes from `routing`, that caps, `accepts` and the provider set come from the copied file, and that an unstubbed provider raises `UnstubbedProviderCall`. It does not contain the phrase "shipped ones".

Anything this spec does not cover: stop and surface, per `.claude/skills/session-start/SKILL.md` § Role 3.

## 4. Steps

Each step ends with a commit. There is no approval stop between steps.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Ray's working-tree change, before any other work, in two commits. **(a)** The hunks `workmain providers set default` wrote — `last_updated`, the `≤` rewrite of `providers.gemini.cost_structure`, and the `report_types` routing of `daily_internal`, `weekly_client` and `note_condensation` — staged without touching the working tree, with `S` a fresh scratchpad directory: `git diff -U0 config/ai_settings.json > "$S/full.patch"`; drop every hunk containing `"notes"` (split the file at each line that begins with the hunk marker `@@`, keep the header and the other hunks) into `"$S/operational.patch"`; `git apply --cached --unidiff-zero "$S/operational.patch"`; confirm with `git diff --cached` that only those lines are staged; commit as `chore(config)`, the body stating it is an operational change made through the CLI (§2.2). **(b)** `git add config/ai_settings.json`, which now stages only Ray's hand trim of `providers.claude.notes` and `providers.gemini.notes`; commit as `fix(config)`, the body stating the notes went stale whenever routing changed and now name the model only. | `config/ai_settings.json` |
| 2 | DR1–DR7: `stubbed_manager`, `UnstubbedProviderCall`, removal of `edit` and `drop_fallback`, every §2 call site with its DR5 routing and with `drop_fallback` dropped from its imports, `test_default_types_follow_routing`, and the §6 tests. | `tests/mocks/stub_providers.py`, `tests/test_cost_display.py`, `tests/test_eod_workflow.py`, `tests/test_intent_parser.py`, `tests/test_meetings_condense.py`, `tests/test_narration.py`, `tests/test_note_condenser.py`, `tests/test_provider_foundation.py`, `tests/test_report_generator.py`, `tests/test_compare_providers.py` |
| 3 | `docs/DEVELOPMENT_STANDARDS.md` §6.2 Rules gains rule 8, verbatim: "**A test that builds a real `ProviderManager` states the routing it needs.** It passes the primary and fallback of every call type it exercises, and never relies on the routing in `config/ai_settings.json`, which `workmain providers set default` changes in ordinary use. A provider the test does not stub must not be reachable: `tests/mocks/stub_providers.py`'s `stubbed_manager` takes the routing as a required argument and makes every unstubbed provider raise." | `docs/DEVELOPMENT_STANDARDS.md` |

### Authorization points

None.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | No test's result depends on the provider routing in `config/ai_settings.json`. Entry path: the full application suite. | Bare `pytest` from the repository root reports 0 failed with the committed routing, and the §6 swapped-routing run reports 0 failed. |
| AC1.2 | No test reaches a real vendor provider's `generate` through a routing change. Entry path: the full application suite under both routings. | The §6 real-call trap, run with the committed routing and in the swapped copy, records no test outside `tests/test_ai_providers_offline.py` and `tests/test_ai_providers_live.py`. |
| AC1.3 | A call routed to a provider the test did not stub fails the test instead of falling back or being swallowed, through `ProviderManager.generate` and through narration's `except Exception`. | `pytest tests/test_provider_foundation.py -k TestStubbedManager` passes (§6). |
| AC2.1 | `stubbed_manager` takes its routing from its caller and has no way to inherit it from the live file. | `python -c "import inspect; from tests.mocks.stub_providers import stubbed_manager as f; p=inspect.signature(f).parameters; assert p['routing'].default is inspect.Parameter.empty and 'edit' not in p"` exits 0, and `git grep -n 'shipped ones\|drop_fallback' -- tests` returns no hits. |
| AC2.2 | `stubbed_manager`'s docstring states where routing, caps and the provider set come from, and what an unstubbed provider does. | A stated reading by Ray of `tests/mocks/stub_providers.py` `stubbed_manager` and its docstring, against DR7. |
| AC3.1 | `docs/DEVELOPMENT_STANDARDS.md` §6.2 tells a test author that a test using a real `ProviderManager` states its routing and never reads it from `config/ai_settings.json`. | A stated reading by Ray of §6.2 rule 8. |
| AC4.1 | The full suite passes. | Bare `pytest` reporting 0 failed. |

## 6. Test plan

- **Baseline before this work:** the counts in `CHANGELOG.md` [1.52.1], in the form `docs/DEVELOPMENT_STANDARDS.md` §6 states. With Ray's routing the suite is red until Step 2 (design study F3).
- **Expected after:** the baseline's passed count plus the new tests below, 0 failed, the baseline's skipped count. Anvil records the actual counts.
- **New tests**, `class TestStubbedManager` in `tests/test_provider_foundation.py` beside `TestManagerRecording`:
  - A call type routed to a provider absent from `stubs` raises `UnstubbedProviderCall` out of `manager.generate`, and the stubbed fallback's `calls` is 0. The test names both providers in its routing, so its result does not depend on `.env`.
  - A stub for a provider whose constructor failed is the one `generate` calls. The test removes the key with `monkeypatch.delenv("GOOGLE_API_KEY", raising=False)`, asserts the precondition — a plain `ProviderManager(config_path=...)` on a copy of the file has `"gemini"` in `_disabled_reasons` (observed with the key absent, 20261023) — then builds `stubbed_manager` with a `gemini` stub routed primary and asserts the stub's `calls` is 1.
  - The same through `narration.narrate`, with the manager set as `provider_manager._provider_manager_instance` as `tests/test_narration.py` does: `UnstubbedProviderCall` propagates out of `narrate`.
  - A `routing` key in neither block raises `KeyError` naming it.
  - `(primary, None)` leaves the copied entry with no `fallback_provider`.
- **Swapped-routing run (AC1.1, AC1.2).** Never edits the live file. From the repository root, with `S` set to a fresh directory under the session scratchpad:

  ```bash
  rsync -a --exclude .git --exclude __pycache__ ./ "$S/swap/"
  python - "$S/swap/config/ai_settings.json" <<'EOF'
  import json, sys
  p = sys.argv[1]; s = json.load(open(p))
  for block in ("report_types", "application_functions"):
      for entry in s[block].values():
          if entry.get("fallback_provider"):
              entry["primary_provider"], entry["fallback_provider"] = entry["fallback_provider"], entry["primary_provider"]
  json.dump(s, open(p, "w"), indent=2)
  EOF
  cd "$S/swap" && PYTHONPATH="$S/swap" pytest
  ```

  `PYTHONPATH` makes `import workmain` resolve to the copy, so `ProviderManager()`'s package-relative read (§2) also gets the swapped file; confirm with `PYTHONPATH="$S/swap" python -c 'import workmain; print(workmain.__file__)'`. A failure whose cause is the copy's location — a long path wrapped by Rich — is an artifact of the probe, not a finding.
- **Real-call trap (AC1.2).** Written to `$S/probe/realcall_probe.py`, never into `tests/`, and loaded with `PYTHONPATH="$S/probe" pytest -p realcall_probe` (prefix the swap path for the swapped run):

  ```python
  import pytest
  HITS = []
  class RealCall(Exception): pass
  @pytest.fixture(autouse=True)
  def _trap(request, monkeypatch):
      from workmain.ai.providers.claude import ClaudeProvider
      from workmain.ai.providers.gemini import GeminiProvider
      for cls in (ClaudeProvider, GeminiProvider):
          def g(self, req, _n=cls.__name__):
              HITS.append((request.node.nodeid, _n)); raise RealCall(_n)
          monkeypatch.setattr(cls, "generate", g)
  def pytest_sessionfinish(session):
      print("\nREAL CALLS:"); [print(" ", h) for h in HITS]
  ```

  Hits from `tests/test_ai_providers_offline.py` (which tests `generate` against a mocked SDK client) and `tests/test_ai_providers_live.py` are expected; any other hit fails AC1.2.

## 7. Risks and rollback

- **A call site's DR5 routing is wrong for what it scripts.** The test then reaches an unstubbed provider and fails with `UnstubbedProviderCall`, which names the provider — loud, and never a vendor call. Rollback: revert Step 2.
- **A test reached an unstubbed provider's `check_availability` legitimately.** It now fails under DR4. None is known (design study §2 Runs); if one appears, it is a stop-and-surface, not a reason to narrow DR4.
- **Step 1 is Ray's live configuration.** Reverting it changes production routing, so it is never part of a rollback of Steps 2–3.
