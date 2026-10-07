# Structured Issue Acceptance Criteria — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261007
**Branch:** `chore/issue-120-structured-acs` (from `main`)
**Target release:** n/a — `chore/*` carries no release (`docs/DEVELOPMENT_STANDARDS.md` §2.2)
**Originating item:** Issue #120
**Design study:** `../design/DESIGN_ISSUE_AC_FIELDS.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261007 | Ray | Design study Q1 — the validator rejects a missing field and two content forms of a criterion that is its check (D1-B) | **Superseded** 20261007 by the only-code-rule row below |
| 20261007 | Ray | Design study Q2 — a criterion renders as a bullet with its check as a `Checked by:` child bullet (D2-A) | Decided — DR3 |
| 20261007 | Ray | Design study Q3 — AC3's issue is created through `--create`, read by Ray, and closed as not planned (D3-A). The live read is one-time evidence that GitHub renders the format distinctly; the format itself is held on every run by `test_structured_render_keeps_criterion_and_check_distinct` | Decided — step 3 |
| 20261007 | Spanner | D1-B as written in the design study refused any code span shared by a criterion and its check. A dry run of the rule found that refuses §1.2's own good form whenever the check also names a path, e.g. `workmain/`. The repeat rule is narrowed to spans containing whitespace — a command has arguments, a path or symbol does not | Confirmed by Ray 20261007; **superseded** the same day by the only-code-rule row below |
| 20261007 | Caliper | F1 — the narrowed repeat rule refuses criteria that meet §1.2. Run over every live issue's ACs, it refuses #138 (`` `meetings create` ``) and #176 (`` `workmain providers test` ``): in both the shared command is the subject of the property, not its evidence. Telling the two apart is a reading | Accepted |
| 20261007 | Ray | The repeat rule is dropped. The validator keeps only the only-code rule, which is issue AC2's own wording — a criterion that states only a command. A criterion that names a command alongside prose is §1.2's and review's | Decided — DR2. Dry run in §2: 0 of 164 live pairs refused |
| 20261007 | Caliper | F2 — §2 is missing; `validate_schema` gains `path` and `render_body`'s `acs` changes from strings to objects, so §1.2 requires the call-sites rows | Accepted — §2 added. The direct path omits §2 by default; a contract change brings its call-sites row back |
| 20261007 | Caliper | F3 — step 4 told the implementer to fill the design study's §6 disposition, which is already filled | Accepted — instruction removed |
| 20261007 | Caliper | F4 — AC2.1's check ran `--create` against live GitHub, so a regressed rule would create a real issue | Accepted — the check runs without `--create`; `test_structured_refusal_stops_the_create_path_before_gh_runs` covers `--create` with `subprocess.run` stubbed |
| 20261007 | Spanner | No issue is edited at close-out to restate its ACs in the new shape — not #120, and not any other. Issue AC4 forbids it, and §1.2 makes the wording rule prospective | Decided |

---

## 1. Scope

**In scope:**

- `.github/ISSUE_TEMPLATE/issue.schema.json` — the `acs` entry type.
- `.github/ISSUE_TEMPLATE/issue.template.json` — the `--new` skeleton.
- `automation/issue_validator.py` — nested-object validation, the criterion rule, the body render.
- `automation/issue_validator_test.py` and `automation/fixtures/` — 19 fixtures converted, one rewritten, two added; three existing tests updated, seven added.
- `docs/DEVELOPMENT_STANDARDS.md` §1.2 — the one sentence that describes the issue schema's current shape.
- One test issue, created and closed by step 3.

**Out of scope:**

- **Every existing issue and its criteria**, including #120's own. Issue AC4.
- **An `id` field on a criterion, or `ACn` numbering on issues.** Nothing in #120 asks for it; `unknown key` refuses one today, and the refusal is tested.
- **`docs/dev/specs/_TEMPLATE_SPEC.md`.** Its §5 already separates the two halves.
- **`automation/closeout_acs.py` and `.claude/skills/closeout/`.** Neither reads an issue body (design study F3).
- **Recognising a command by name.** It needs a list of command names, a hand-maintained register (design study D1).
- **Refusing a criterion that repeats a command from its check.** Whether the shared command is the property's subject or its evidence is a reading (Decision Log, Caliper F1).
- **`gh issue create` run directly.** It bypasses the validator, so no schema can refuse what it is given; the supported path is `automation/issue_validator.py`, which is what issue AC2 names.

## 2. Verified current state

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| Call sites of `validate_schema`, `render_body` and `validate_issue`, found by `grep -rn 'validate_schema(\|render_body(\|validate_issue(' --include='*.py' .` | `automation/issue_validator.py:291` (`validate_issue` → `validate_schema`), `:336` (`main` → `validate_issue`), `:346` (`main` → `render_body`); `automation/issue_validator_test.py:47` (`run_validate` → `validate_issue`), `:221` (`test_single_line_render_body_is_not_repaired` → `render_body`). No caller outside these two files. `validate_schema` gains an optional `path` and keeps its existing call; `render_body`'s `acs` changes from strings to objects at both of its call sites, and step 1 updates both |
| No consumer reads an issue body's ACs back | Design study F3 |
| Every live issue's existing ACs pass `validate_criterion_rule` as step 1 writes it | Each `- ` line under `**ACs**` in `gh issue list --state all --limit 300 --json number,body`, split at the first `checked by`, run through the step 1 function: 164 pairs, 0 refused. The same run against the repeat rule refused #138 and #176 |

## 3. Design rules

- **DR1 —** An `acs` entry's schema is written in the same key-spec form as the top level, and `validate_schema` checks it by calling itself, so every existing per-key rule applies to the nested fields. No second validation mechanism.
- **DR2 —** The schema refuses a missing, empty or multi-line `criterion` or `check`. `validate_criterion_rule` refuses a criterion with no word outside its code spans. It refuses nothing else; what a criterion means is §1.2's and review's.
- **DR3 —** The body renders each criterion as `- <criterion>` with a child line `  - Checked by: <check>`. Nothing is escaped.
- **DR4 —** §1.2 owns how a criterion is worded; the schema owns the shape that carries it. §1.2 cites the schema and the validator and restates neither.

## 4. Steps

Before step 1, run `pytest` and `pytest automation/` from the repository root on this branch and record both sets of counts in the results artifact §5 — the baseline for AC6.1.

**Step 1 — schema, skeleton, validator and tests.** One commit, because the schema change and the fixtures it invalidates cannot land apart without a red suite.

1a. Apply this diff from the repository root with `git apply`:

```diff
--- a/.github/ISSUE_TEMPLATE/issue.schema.json
+++ b/.github/ISSUE_TEMPLATE/issue.schema.json
@@ -11,10 +11,23 @@
   },
   "acs": {
     "type": "array",
-    "items": "string",
+    "items": {
+      "type": "object",
+      "keys": {
+        "criterion": {
+          "type": "string",
+          "required": true,
+          "single_line": true
+        },
+        "check": {
+          "type": "string",
+          "required": true,
+          "single_line": true
+        }
+      }
+    },
     "required": true,
-    "min_items": 1,
-    "single_line": true
+    "min_items": 1
   },
   "milestone": {
     "type": "string",
--- a/.github/ISSUE_TEMPLATE/issue.template.json
+++ b/.github/ISSUE_TEMPLATE/issue.template.json
@@ -1,7 +1,12 @@
 {
   "title": "",
   "context": "",
-  "acs": [],
+  "acs": [
+    {
+      "criterion": "",
+      "check": ""
+    }
+  ],
   "milestone": null,
   "parent": null,
   "labels": [],
--- a/automation/issue_validator.py
+++ b/automation/issue_validator.py
@@ -4,8 +4,9 @@
 
 The schema (`.github/ISSUE_TEMPLATE/issue.schema.json`) declares the key set
 and each key's type and required-ness. This script owns the rules the schema
-file cannot express: the §1.3 label-pair rule and existence checks
-against live GitHub state (labels, milestones, referenced issues).
+file cannot express: the §1.3 label-pair rule, the §1.2 rule that a criterion
+is not only a command, and existence checks against live GitHub state (labels,
+milestones, referenced issues).
 
 Why this exists: GitHub carries no type-vs-area marking on a label
 (`Repository.issueTypes` is null for this repository), so the label
@@ -94,9 +95,9 @@
 def _has_line_break(value: str) -> bool:
     """A line break in a single-line field is refused, not repaired (#88).
 
-    `render_body()` emits one `- ` marker per `acs` item, so an embedded
-    newline renders as a bullet followed by a loose line belonging to no AC,
-    and the created issue silently misrepresents its own AC list.
+    `render_body()` emits one line per criterion and one per check, so an
+    embedded newline renders as a loose line belonging to no AC, and the
+    created issue silently misrepresents its own AC list.
     """
     return "\n" in value or "\r" in value
 
@@ -108,15 +109,19 @@
         return isinstance(value, str)
     if type_name == "array":
         return isinstance(value, list)
+    if type_name == "object":
+        return isinstance(value, dict)
     return False
 
 
-def validate_schema(data, schema: dict):
+def validate_schema(data, schema: dict, path: str = ""):
     """Check `data` against `schema`. Returns (errors, normalized_data).
 
     Every declared key is checked; unknown keys fail by name. Missing
     optional keys are filled with their default so downstream checks never
-    have to special-case absence.
+    have to special-case absence. An array whose `items` is itself a key
+    spec has each item checked by this same function, with `path` naming the
+    item in every error it reports (`acs[1].criterion`).
     """
     if not isinstance(data, dict):
         return (["issue data must be a JSON object"], {})
@@ -124,14 +129,15 @@
     errors = []
     for key in data:
         if key not in schema:
-            errors.append(f"unknown key: {key}")
+            errors.append(f"unknown key: {path}{key}")
 
     normalized = dict(data)
     for key, spec in schema.items():
+        name = f"{path}{key}"
         required = spec.get("required", False)
         if key not in data:
             if required:
-                errors.append(f"missing required key: {key}")
+                errors.append(f"missing required key: {name}")
             else:
                 normalized[key] = spec.get("default")
             continue
@@ -139,35 +145,40 @@
         value = data[key]
         if value is None:
             if not spec.get("nullable", False):
-                errors.append(f"key '{key}' must not be null")
+                errors.append(f"key '{name}' must not be null")
             continue
 
         expected = spec["type"]
         if not _check_type(value, expected):
-            errors.append(f"key '{key}' must be of type {expected}")
+            errors.append(f"key '{name}' must be of type {expected}")
             continue
 
         if expected == "string":
             if not value.strip():
-                errors.append(f"key '{key}' must be non-empty")
+                errors.append(f"key '{name}' must be non-empty")
             max_length = spec.get("max_length")
             if max_length is not None and len(value) > max_length:
-                errors.append(f"key '{key}' must be at most {max_length} characters")
+                errors.append(f"key '{name}' must be at most {max_length} characters")
             if spec.get("single_line") and _has_line_break(value):
-                errors.append(f"key '{key}' must be a single line")
+                errors.append(f"key '{name}' must be a single line")
 
         if expected == "array":
             min_items = spec.get("min_items")
             if min_items is not None and len(value) < min_items:
-                errors.append(f"key '{key}' must have at least {min_items} entry(ies)")
-            item_type = spec.get("items")
+                errors.append(f"key '{name}' must have at least {min_items} entry(ies)")
+            item_spec = spec.get("items")
+            item_type = item_spec.get("type") if isinstance(item_spec, dict) else item_spec
+            normalized[key] = list(value)
             for i, item in enumerate(value):
                 if item_type and not _check_type(item, item_type):
-                    errors.append(f"key '{key}[{i}]' must be of type {item_type}")
+                    errors.append(f"key '{name}[{i}]' must be of type {item_type}")
+                elif item_type == "object":
+                    item_errors, normalized[key][i] = validate_schema(item, item_spec["keys"], f"{name}[{i}].")
+                    errors.extend(item_errors)
                 elif item_type == "string" and not item.strip():
-                    errors.append(f"key '{key}[{i}]' must be non-empty")
+                    errors.append(f"key '{name}[{i}]' must be non-empty")
                 elif item_type == "string" and spec.get("single_line") and _has_line_break(item):
-                    errors.append(f"key '{key}[{i}]' must be a single line")
+                    errors.append(f"key '{name}[{i}]' must be a single line")
 
     return errors, normalized
 
@@ -192,6 +203,30 @@
     return []
 
 
+_CODE_SPAN_RE = re.compile(r"`([^`]+)`")
+
+
+def validate_criterion_rule(data: dict) -> list:
+    """§1.2: a criterion names a property; its check is the evidence, not the criterion.
+
+    A criterion with no words outside its code spans states only a command,
+    and is refused. Whether a command a criterion does name is its subject or
+    its evidence is a reading, and is not checked here. Shape errors are the
+    schema's to report; an entry without a non-empty string criterion is
+    skipped here.
+    """
+    errors = []
+    for i, ac in enumerate(data.get("acs") or []):
+        if not isinstance(ac, dict):
+            continue
+        criterion = ac.get("criterion")
+        if not isinstance(criterion, str) or not criterion.strip():
+            continue
+        if not re.search(r"\w", _CODE_SPAN_RE.sub("", criterion)):
+            errors.append(f"acs[{i}].criterion is only code — it names no property of the delivered system")
+    return errors
+
+
 def _check_open_issue(field: str, number: int, get_issue_state) -> list:
     state = get_issue_state(number)
     if state is None:
@@ -226,7 +261,9 @@
 
 def render_body(context: str, acs: list) -> str:
     lines = [context.strip(), "", "**ACs**", ""]
-    lines.extend(f"- {ac.strip()}" for ac in acs)
+    for ac in acs:
+        lines.append(f"- {ac['criterion'].strip()}")
+        lines.append(f"  - Checked by: {ac['check'].strip()}")
     return "\n".join(lines) + "\n"
 
 
@@ -290,6 +327,7 @@
     """Run every check and return (errors, normalized_data). Total reporting — DR4."""
     errors, normalized = validate_schema(data, schema)
     errors += validate_label_pair_rule(normalized, label_pair)
+    errors += validate_criterion_rule(normalized)
     errors += validate_live_state(normalized, live_labels, live_milestones, get_issue_state)
     return errors, normalized
 
--- a/automation/issue_validator_test.py
+++ b/automation/issue_validator_test.py
@@ -186,7 +186,7 @@
 
     def test_single_line_newline_in_an_ac_is_refused_naming_the_index(self):
         errors, _ = run_validate(fixture("single_line_newline_in_ac.json"))
-        assert "key 'acs[1]' must be a single line" in errors
+        assert "key 'acs[1].criterion' must be a single line" in errors
 
     def test_single_line_newline_in_the_title_is_refused(self):
         errors, _ = run_validate(fixture("single_line_newline_in_title.json"))
@@ -199,7 +199,7 @@
         data["extra_bogus_key"] = True
 
         errors, _ = run_validate(data)
-        assert "key 'acs[1]' must be a single line" in errors
+        assert "key 'acs[1].criterion' must be a single line" in errors
         assert any("not-a-real-label" in e for e in errors)
         assert any("unknown key: extra_bogus_key" in e for e in errors)
 
@@ -218,11 +218,77 @@
 
     def test_single_line_render_body_is_not_repaired(self):
         """DR6 — the fix is refusal at validation, not repair at render."""
-        rendered = issue_validator.render_body("Context line.", ["one", "two\nsplit"])
-        assert rendered.count("- ") == 2
+        acs = [
+            {"criterion": "one", "check": "first"},
+            {"criterion": "two\nsplit", "check": "second"},
+        ]
+        rendered = issue_validator.render_body("Context line.", acs)
+        assert len([line for line in rendered.splitlines() if line.startswith("- ")]) == 2
         assert "\nsplit" in rendered
 
 
+class TestStructuredCriteria:
+    """A criterion and its check are separate fields, and a criterion that is only a command is refused (#120)."""
+
+    def test_structured_skeleton_carries_the_criterion_and_check_fields(self):
+        result = subprocess.run(
+            [sys.executable, str(ROOT / "automation" / "issue_validator.py"), "--new"],
+            capture_output=True,
+            text=True,
+            check=True,
+        )
+        skeleton_acs = json.loads(result.stdout)["acs"]
+        assert len(skeleton_acs) == 1
+        assert sorted(skeleton_acs[0]) == sorted(SCHEMA["acs"]["items"]["keys"])
+
+    def test_structured_criterion_that_is_only_code_is_refused(self):
+        errors, _ = run_validate(fixture("criterion_only_code.json"))
+        assert errors == ["acs[0].criterion is only code — it names no property of the delivered system"]
+
+    def test_structured_one_string_criterion_is_refused(self):
+        errors, _ = run_validate(fixture("criterion_legacy_string.json"))
+        assert errors == ["key 'acs[0]' must be of type object"]
+
+    def test_structured_criterion_without_a_check_is_refused(self):
+        data = fixture("valid_minimal.json")
+        del data["acs"][0]["check"]
+        errors, _ = run_validate(data)
+        assert errors == ["missing required key: acs[0].check"]
+
+    def test_structured_unknown_key_in_a_criterion_is_named(self):
+        data = fixture("valid_minimal.json")
+        data["acs"][0]["id"] = "AC1"
+        errors, _ = run_validate(data)
+        assert errors == ["unknown key: acs[0].id"]
+
+    def test_structured_refusal_stops_the_create_path_before_gh_runs(self, tmp_path, monkeypatch):
+        issue_file = tmp_path / "issue.json"
+        issue_file.write_text(json.dumps(fixture("criterion_only_code.json")))
+
+        monkeypatch.setattr(issue_validator, "gh_live_labels", lambda: LIVE_LABELS)
+        monkeypatch.setattr(issue_validator, "gh_live_milestones", lambda: LIVE_MILESTONES)
+        monkeypatch.setattr(issue_validator, "gh_issue_state", fake_issue_state())
+        monkeypatch.setattr(
+            subprocess,
+            "run",
+            lambda *a, **k: pytest.fail("gh issue create must not run for a refused issue"),
+        )
+
+        assert issue_validator.main([str(issue_file), "--create"]) == 1
+
+    def test_structured_render_keeps_criterion_and_check_distinct(self):
+        acs = [{"criterion": "no module carries a header", "check": "`grep -rn x workmain/` returns zero hits"}]
+        rendered = issue_validator.render_body("Context line.", acs)
+        assert rendered == (
+            "Context line.\n"
+            "\n"
+            "**ACs**\n"
+            "\n"
+            "- no module carries a header\n"
+            "  - Checked by: `grep -rn x workmain/` returns zero hits\n"
+        )
+
+
 class TestAC3:
     def test_ac3_1_default_run_creates_nothing(self, tmp_path, monkeypatch, capsys):
         issue_file = tmp_path / "issue.json"
```

1b. Convert the 19 fixtures that carry the old one-string criterion. Each holds exactly this line:

```json
  "acs": ["AC1: something is true"],
```

which becomes:

```json
  "acs": [{"criterion": "something is true", "check": "reading this fixture"}],
```

Run `sed -i 's|"acs": \["AC1: something is true"\],|"acs": [{"criterion": "something is true", "check": "reading this fixture"}],|' automation/fixtures/*.json`; `grep -l 'reading this fixture' automation/fixtures/*.json | wc -l` returns 19.

1c. Replace the whole of `automation/fixtures/single_line_newline_in_ac.json` with:

```json
{
  "title": "Newline inside an AC",
  "context": "Otherwise valid; acs[1].criterion carries an embedded newline.",
  "acs": [
    {"criterion": "single line AC", "check": "reading this fixture"},
    {"criterion": "wrapped AC\nsecond physical line", "check": "reading this fixture"},
    {"criterion": "third AC", "check": "reading this fixture"}
  ],
  "milestone": null,
  "parent": null,
  "labels": ["cli", "defect"],
  "blocked_by": [],
  "blocking": []
}
```

1d. Add `automation/fixtures/criterion_only_code.json`:

```json
{
  "title": "Criterion that is only a command",
  "context": "Otherwise valid; acs[0].criterion is the command alone, with no property of the delivered system.",
  "acs": [
    {"criterion": "`grep -rn '^Version:' workmain/ --include='*.py'`", "check": "`grep -rn '^Version:' workmain/ --include='*.py'` returns zero hits"}
  ],
  "milestone": null,
  "parent": null,
  "labels": ["cli", "defect"],
  "blocked_by": [],
  "blocking": []
}
```

1e. Add `automation/fixtures/criterion_legacy_string.json`:

```json
{
  "title": "Criterion in the retired one-string form",
  "context": "Otherwise valid; acs[0] is a plain string carrying both halves in one sentence.",
  "acs": ["no module under workmain/ carries a version header, checked by grep returning zero hits"],
  "milestone": null,
  "parent": null,
  "labels": ["cli", "defect"],
  "blocked_by": [],
  "blocking": []
}
```

Run `pytest automation/`. Commit.

**Step 2 — `docs/DEVELOPMENT_STANDARDS.md` §1.2.** Replace:

```markdown
  - `docs/dev/specs/_TEMPLATE_SPEC.md` §5 carries the two as separate columns, `Criterion` and `How it is checked`. On an issue, where `.github/ISSUE_TEMPLATE/issue.schema.json` types an acceptance criterion as one string, the wording is what carries that separation instead.
```

with:

```markdown
  - `docs/dev/specs/_TEMPLATE_SPEC.md` §5 carries the two as separate columns, `Criterion` and `How it is checked`. On an issue, `.github/ISSUE_TEMPLATE/issue.schema.json` carries them as separate fields, and `automation/issue_validator.py` refuses a criterion it can see is only its check. A criterion that passes the validator still has to meet this rule.
```

Commit.

**Step 3 — the rendered body on GitHub.** Write this payload to the scratchpad, not the repository:

```json
{
  "title": "Rendering check for issue #120 — closed once read",
  "context": "Created by issue #120 step 3 to show how a structured criterion renders on GitHub. Closed as not planned once read.",
  "acs": [
    {"criterion": "no Python module under `workmain/` carries a version header in its docstring", "check": "`grep -rn '^Version:' workmain/ --include='*.py'` returns zero hits"},
    {"criterion": "each criterion and its check read as two distinct lines on GitHub", "check": "a stated reading by Ray of this issue's body"}
  ],
  "milestone": null,
  "parent": null,
  "labels": ["process", "gap"],
  "blocked_by": [],
  "blocking": []
}
```

Run `python3 automation/issue_validator.py <payload> --create`. Ray reads the issue on GitHub. Then run `gh issue close <N> --reason "not planned"`. Record both commands and `<N>` in the results artifact. No commit — this step changes no file.

**Step 4 — results artifact** `docs/dev/results/ISSUE_AC_FIELDS_RESULTS.md`: the §3 AC table, the baseline and after counts for both suites in §5, and every `gh issue` write command this work ran. Commit.

### Authorization points

None. Step 3 creates one issue and closes it; neither is on the §1.4 set, and the issue is closed, not deleted.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | An issue's criterion carries the property and its check as two separate required fields, and an issue in the old one-string form is refused | Reading `issue.schema.json`'s `acs.items`; `pytest automation/issue_validator_test.py -k "one_string_criterion or without_a_check"` passes |
| AC1.2 | `--new` prints a skeleton whose criterion has both fields | `python3 automation/issue_validator.py --new` shows `acs[0]` with `criterion` and `check`; `test_structured_skeleton_carries_the_criterion_and_check_fields` passes |
| AC2.1 | An issue whose criterion is only a command is refused on the supported create path before `gh issue create` runs. The entry path is `automation/issue_validator.py <file> --create`; `gh issue create` run directly is omitted because it bypasses every validator (§1 Out of scope) | `python3 automation/issue_validator.py automation/fixtures/criterion_only_code.json` exits 1 naming `acs[0].criterion`; `test_structured_refusal_stops_the_create_path_before_gh_runs` passes |
| AC3.1 | An issue created through the validator shows each criterion and its check as visibly distinct lines on GitHub | Stated reading by Ray of the step 3 issue's body on GitHub; `test_structured_render_keeps_criterion_and_check_distinct` pins the rendered Markdown on every run |
| AC4.1 | No existing issue is edited, reopened or restructured by this work | The results artifact lists every `gh issue` write command this work ran; the list contains no `edit`, `reopen` or `--body` invocation against an issue this work did not create |
| AC5.1 | §1.2 owns the wording of a criterion and the schema owns its shape, each citing rather than restating the other | Stated reading by Ray of the step 2 sentence against `CLAUDE.md`'s opening single-home rule, read for any restatement of the schema's fields or the validator's rules |
| AC6.1 | `pytest` is unchanged by this work, and `pytest automation/` gains exactly this spec's seven tests with nothing failing or skipped | Both suites' `passed, failed, skipped` counts, before step 1 and after step 4, in the results artifact §5: `pytest` identical; `pytest automation/` at baseline + 7 passed, 0 failed, 0 skipped |

## 6. Test plan

- **Baseline before this work:** recorded in the results artifact §5 before step 1, per AC6.1.
- **Expected after:** `pytest` — the baseline counts unchanged. `pytest automation/` — baseline + 7 passed, 0 failed, 0 skipped.
- **Updated:** `test_single_line_newline_in_an_ac_is_refused_naming_the_index` and `test_single_line_refusal_participates_in_total_reporting` name the path `acs[1].criterion`; `test_single_line_render_body_is_not_repaired` passes the new entry shape and counts top-level bullets only.
- **Added:** class `TestStructuredCriteria`, seven tests, in `automation/issue_validator_test.py`.
- **Expected failures, observed at authoring** on a scratch copy of this branch's base:
  - New tests and fixtures against the current validator and schema: 6 of 7 fail. `test_structured_refusal_stops_the_create_path_before_gh_runs` passes there, because the current schema refuses an object entry for its own reason.
  - Against the step 1 code with the `validate_criterion_rule` call removed: the only-code and create-path tests fail — so the create-path test does exercise the criterion rule.

## 7. Risks and rollback

- **An issue drafted in the old shape is refused.** Intended; the error names `acs[i]` and `--new` shows the new shape.
- **The criterion rule refuses a legitimate criterion.** It refuses only a criterion with no word outside its code spans, and refused none of the 164 live pairs (§2).
- **The step 3 issue stays on the board, closed.** §1.6's `is:open` read never shows it.
- Steps 1, 2 and 4 are one commit each and revert alone. Step 3 is undone only by deleting the issue, which is an authorization point and is not planned.
