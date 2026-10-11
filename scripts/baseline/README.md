# Provider baseline (issue #181 follow-up)

Two scripts to measure Gemini against Claude on WorkmAIn's real report prompts, outside the app's generation path.

| Script | Touches WorkmAIn / DB? | What it does |
| --- | --- | --- |
| `capture_baseline_prompts.py` | Yes, **read-only** | Builds the exact prompts production would send and freezes them to JSON fixtures |
| `run_baseline.py` | No | Replays the fixtures against both providers, N samples each, and writes results and a side-by-side |

The fixtures stay fixed while the code changes. Rerun `run_baseline.py` against the same fixtures after each fix, and any difference comes from the fix, not from different data.

## Read-only guarantees (capture)

- `SET TRANSACTION READ ONLY` is the first statement. PostgreSQL rejects any write after it.
- `session.commit()` is replaced with a function that raises.
- `SHOW transaction_read_only` is checked after every item. The capture aborts if it is not `on`.
- The session is rolled back and closed in a `finally` block.
- It calls only `PromptBuilder.build_prompt()`, `NoteCondenser.select_condensation_notes()` and `build_condensation_request()`. Nothing is generated, saved or condensed, and no AI provider is called.

## Install (WSL, repository root)

```bash
mkdir -p scripts/baseline
# copy capture_baseline_prompts.py, run_baseline.py, README.md and variants/ into scripts/baseline/
```

Outputs go under `staging/baseline/`, which `staging/` in `.gitignore` already covers. They contain client work content. Never commit or paste them.

## 1. Capture (once)

```bash
source .venv/bin/activate        # or however you enter the WorkmAIn venv
python scripts/baseline/capture_baseline_prompts.py \
    --daily 2026-10-07,2026-10-08,2026-10-09 \
    --weekly 2026-09-25,2026-10-02,2026-10-09
```

- The weekly reports use the current `active_client_id`, the same as production.
- Condensation fixtures are the meetings on the `--daily` dates that have non-info-only notes. Change this with `--condense <dates>` or `--condense none`.
- Exit status is `0` only if every item was captured. Failures are listed in `manifest.json`.

## 2. Check the plan, then run

```bash
FX=staging/baseline/fixtures/<timestamp>
python scripts/baseline/run_baseline.py --fixtures $FX --dry-run       # prints the call count, calls nothing
python scripts/baseline/run_baseline.py --fixtures $FX --samples 3 --blind
```

- API keys are read from `.env` (`GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`), or from `--env-file`.
- Providers are interleaved per sample, so any drift over the run affects both.
- Each call is retried 3 times with backoff. A call that still fails is recorded as an error, and the run continues.
- Exit status is `0` only if every call returned content with a normal stop reason.

Useful flags: `--only daily_internal,weekly_client`, `--providers gemini`, `--gemini-model <name>`, `--out <dir>`.

## 3. Read the results (`staging/baseline/runs/<timestamp>/`)

| File | Contents |
| --- | --- |
| `summary.md` | Tokens, thinking tokens, latency and estimated cost per call type and provider; structure checks per sample; a verdict table for you to fill in |
| `side_by_side.md` | Every sample **after production formatting** (a copy of `_format_output` as of v1.42.2), which is what reaches staging, email and Drive |
| `blind_key.json` | Present with `--blind`. Maps Output A/B to providers. Open it after you have judged. |
| `results.jsonl` | One record per call: raw output, formatted output, tokens, finish reason, latency, cost, checks |
| `run_meta.json` | Models, policies, the fixture manifest and the variant |

Structure checks for reports:
- whether the model wrote its own title line
- where production put the Subject line: `under_title` is good, `inside_section` is the defect seen on 10-09
- the heading levels used for sections
- whether every template section is present and in order
- how many sections are "None at this time" or similar boilerplate
- bullet and word counts

Condensation checks: length within 200 characters, a single line, a `Type: points` prefix, and no Markdown.

Blind mode hides the provider names, but writing style can still give a provider away. For example, Claude writes a title line. Judge content first.

## 4. Variants (for later fixes)

`--variant <file.json>` replays the same fixtures with a modified prompt, so a prompt fix can be measured against this baseline before any app change. `variants/example_skeleton.json` shows the shape:

| Key | Effect |
| --- | --- |
| `name` | Used as a suffix on the run folder |
| `apply_to` | List of call types it applies to. Empty means all. |
| `system_prompt_append` / `user_prompt_append` / `system_prompt_replace` | The prompt changes |
| `per_call_type` | The same keys, applied to one call type only |
| `format_output` | `"v1.42.2"` (default, production today), `"proposed"` (the app writes the title, Subject and Date and drops any title the model wrote), or `"none"` (raw output) |

Run-level overrides (recorded in `summary.md` and `run_meta.json`):

| Flag | Effect |
| --- | --- |
| `--gemini-thinking-level low` | Replaces `thinking_config.thinking_level` for this run only. The policy file is not changed. |
| `--format-output proposed` | Applies a formatting mode to every report, overriding the variant |
| `--tag <text>` | Adds a suffix to the run folder name |

The example is a starting point, not a decision. It is not part of the baseline run.
