WorkmAIn
HOTFIX_INTENT_PARSE_CONFIG_CONSOLIDATION_20260622 v1.0
20260622

# Problem

`intent_parse_prompt.json`'s `_doc` block redundantly stores three version
fields (`config_version`, `config_updated`, `model_built`) that are already
authoritatively maintained in `config/intent_parse_system_prompt.txt`'s
header. During the Intent Action Service Layer sprint, one of these
redundant copies (`config_version`) was stale (`"1.5"` in `.json` vs
`1.6` correct everywhere else), causing Claude Code to fixate on the
discrepancy and consume significant sprint time despite the model being
fully correct and operational.

The fix is narrow: remove the redundant version fields from `.json`,
replace them with a single pointer to the `.txt` as the version authority,
and document the correct single-source-of-truth workflow explicitly.

# Scope

- `config/intent_parse_prompt.json` — remove redundant version fields from
  `_doc`, add pointer to `.txt`
- `config/intent_parse_system_prompt.txt` — add explicit "version authority"
  note to header comment, no other changes
- `CLAUDE.md` — add a note clarifying which file owns version metadata and
  where the system prompt content lives, so future Claude Code sessions
  don't re-derive the wrong answer

**Not in scope:**
- Any changes to `IntentParser` or any Python code — runtime behavior is
  unchanged
- Any changes to the Modelfile or IaC repo
- Any changes to `ai_settings.json`
- Any version bump — this is a documentation/config cleanup only; no
  application behavior changes, no migration, no new tests required

# What each file owns (for reference)

| File | Owns | Does NOT own |
|------|------|--------------|
| `intent_parse_system_prompt.txt` | System prompt content (action types, examples, rules); version metadata (`config_version`, `config_updated`, `model_built`) | Generation parameters |
| `intent_parse_prompt.json` | Runtime parameters (`ollama_model`, `ollama_host`, `max_tokens`); generation parameter reference (`generation_options`) | Version metadata — pointer to `.txt` only |
| Modelfile (IaC repo) | Build artifact — SYSTEM block (verbatim from `.txt` body) + PARAMETER blocks (from `generation_options`) | Neither file's version metadata |

# Git Workflow

This touches 3 files — eligible for `hotfix/*` per `GIT_WORKFLOW_STANDARDS.md`.
Branch from `main`:

```bash
git checkout main
git pull
git checkout -b hotfix/intent-parse-config-consolidation
```

Merge to both `main` and `dev` on completion per hotfix workflow.

Commit message:
```
docs(config): consolidate intent parse version metadata to txt as single source of truth

Removes config_version, config_updated, and model_built from
intent_parse_prompt.json _doc block — these fields were redundant
copies of metadata already authoritatively maintained in
intent_parse_system_prompt.txt header. Stale copy (config_version
"1.5" vs correct "1.6" everywhere else) caused significant confusion
during the Intent Action Service Layer sprint.

intent_parse_prompt.json: replaced three version fields with a single
version_authority pointer to intent_parse_system_prompt.txt. Retained
ollama_model and ollama_host in _doc as useful quick-reference (these
do not duplicate version metadata). Updated notes field to reflect
corrected update workflow.

intent_parse_system_prompt.txt: added VERSION AUTHORITY comment block
to header explicitly declaring this file as the single source of truth
for config_version, config_updated, and model_built.

CLAUDE.md: added Intent Parser Config section documenting file
ownership boundaries, version authority, and a 6-step version bump
workflow (matching the .txt's existing tuning workflow, including the
ai_settings.json model field update step) so future sessions do not
re-derive the wrong answer or produce conflicting workflow references.

No runtime behavior changes. No migration. No version bump.
624 tests expected to pass unchanged.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

# Changes

## 1. `config/intent_parse_prompt.json`

Remove `config_version`, `config_updated`, and `model_built` from the
`_doc` block. Replace with a single `version_source` pointer. Update the
`notes` field to reflect the corrected workflow.

**Before (`_doc` block):**
```json
"_doc": {
    "name": "WorkmAIn Intent Parse — Generation Config",
    "description": "Generation parameters for Mistral 7B intent parsing via Ollama. Controls max_tokens only at runtime — temperature/top_p/top_k/repeat_penalty are baked into the Modelfile and listed here as the editable reference for rebuilds.",
    "system_prompt_source": "config/intent_parse_system_prompt.txt",
    "ollama_model": "workmain-intent:latest",
    "ollama_host": "workmain-ollama.lab.haloschaos.com:11434",
    "config_version": "1.6",
    "config_updated": "20260611",
    "model_built": "workmain-intent:v1.6",
    "notes": "After editing generation_options, update Modelfile PARAMETER blocks to match, rebuild model via build_workmain_intent.sh, then set model_built to today's date."
}
```

**After (`_doc` block):**
```json
"_doc": {
    "name": "WorkmAIn Intent Parse — Generation Config",
    "description": "Generation parameters for Mistral 7B intent parsing via Ollama. Controls max_tokens only at runtime — temperature/top_p/top_k/repeat_penalty are baked into the Modelfile and listed here as the editable reference for rebuilds.",
    "system_prompt_source": "config/intent_parse_system_prompt.txt",
    "ollama_model": "workmain-intent:latest",
    "ollama_host": "workmain-ollama.lab.haloschaos.com:11434",
    "version_authority": "Version metadata (config_version, config_updated, model_built) is maintained exclusively in config/intent_parse_system_prompt.txt header. Do not add version fields here — read the .txt header for current version state.",
    "notes": "To update generation parameters: edit generation_options below, sync PARAMETER blocks in the Modelfile (IaC repo), rebuild model via build_workmain_intent.sh, then update config_version/config_updated/model_built in intent_parse_system_prompt.txt only."
}
```

The `ollama_model` and `ollama_host` fields at the top level of `_doc`
are documentation-only (runtime values are read from the top-level fields
outside `_doc`). Leave them in place — they are useful as a quick
reference and do not duplicate version metadata.

## 2. `config/intent_parse_system_prompt.txt`

Add a single line to the header comment block explicitly stating this file
is the version authority. Insert after the `# model_built:` line:

**Before:**
```
# config_version:    1.6
# config_updated:    20260611
# ollama_model:      workmain-intent:latest
# ollama_host:       workmain-ollama.lab.haloschaos.com:11434
# model_built:       workmain-intent:v1.6
#
# Description:
```

**After:**
```
# config_version:    1.6
# config_updated:    20260611
# ollama_model:      workmain-intent:latest
# ollama_host:       workmain-ollama.lab.haloschaos.com:11434
# model_built:       workmain-intent:v1.6
#
# VERSION AUTHORITY: This file is the single source of truth for
#   config_version, config_updated, and model_built. These fields
#   do NOT appear in intent_parse_prompt.json — read this header
#   for current version state.
#
# Description:
```

No other changes to this file.

## 3. `CLAUDE.md`

Add a section (or extend the existing IntentParser/Ollama section if one
exists) with the following content. Place it wherever model config
guidance currently lives in `CLAUDE.md`:

```markdown
## Intent Parser Config — Source of Truth

Two files govern the IntentParser. They own different things:

- `config/intent_parse_system_prompt.txt` — system prompt content AND
  version metadata (`config_version`, `config_updated`, `model_built`).
  This is the ONLY place version state is tracked. Edit this file when
  changing action types, examples, or inference rules.

- `config/intent_parse_prompt.json` — runtime generation parameters ONLY
  (`ollama_model`, `ollama_host`, `max_tokens`, `generation_options`).
  No version fields. Do not add config_version or model_built here.

The Modelfile lives in the IaC repo
(`haloschaos-lab/automation-scripts/ollama-lxc/models/workmain-intent/Modelfile`)
— it is a build artifact, not a WorkmAIn source file. Its SYSTEM block
must match the body of `intent_parse_system_prompt.txt` exactly; its
PARAMETER blocks must match `generation_options` in
`intent_parse_prompt.json`.

**Version bump workflow:**
1. Edit `intent_parse_system_prompt.txt` (prompt content changes)
2. Sync SYSTEM block to Modelfile in IaC repo
3. Run `build_workmain_intent.sh` on Proxmox LXC
4. Update `config_version`, `config_updated`, `model_built` in
   `intent_parse_system_prompt.txt` header ONLY
5. Update `ollama_model` in `ai_settings.json` if the model name changed
   (e.g. a new versioned tag rather than `latest`)
6. Nothing else needs updating — `intent_parse_prompt.json` has no
   version fields to maintain
```

# Verification

After making changes, confirm:

1. `intent_parse_prompt.json` contains no `config_version`,
   `config_updated`, or `model_built` fields anywhere in the file:
   ```bash
   grep -E "config_version|config_updated|model_built" config/intent_parse_prompt.json
   # expect: no output
   ```

2. `intent_parse_system_prompt.txt` header contains all three version
   fields and the VERSION AUTHORITY note:
   ```bash
   grep -E "config_version|config_updated|model_built|VERSION AUTHORITY" config/intent_parse_system_prompt.txt
   # expect: 4 lines
   ```

3. Application still starts and IntentParser initializes without error:
   ```bash
   workmain --version
   ```

4. No test failures (no behavior change expected — run as a sanity check):
   ```bash
   python -m pytest tests/ -v --tb=short 2>&1 | tail -5
   # expect: 624 passed, 0 failed
   ```

# Summary

One problem, one fix: version metadata now lives in exactly one place.
The `.txt` owns it; the `.json` points to it. Nothing about the runtime
behavior, the build workflow, or the prompt engineering workflow changes —
only the number of places you have to update when a version changes goes
from 4 to 3 (`.txt` header fields, Modelfile SYSTEM block sync, rebuild).
