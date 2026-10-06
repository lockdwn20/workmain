# A contract change enumerates its call sites; a verification names its entry path — Spec

**Status:** Shipped
**Author:** Spanner (Role 1)
**Date:** 20261006
**Branch:** `chore/issue-135-call-sites-entry-paths` (from `main`)
**Target release:** n/a — `chore/*` carries no release (`docs/DEVELOPMENT_STANDARDS.md` §2.2)
**Originating item:** Issue #135
**Design study:** `n/a` — direct path, no recon was run

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261006 | Spanner | No recon. A search of `CLAUDE.md`, `docs/DEVELOPMENT_STANDARDS.md`, `docs/dev/` and `.claude/` for either rule (`call site`, `entry path`, `integration-verified`, `transitiv`, `provenance`) returns one site, `CLAUDE.md:233`. One restatement site does not need a recon to find it. | Decided |
| 20261006 | Spanner | The call-site rule requires the §2 row to carry the search that produced it. The issue says "found by search"; without the search recorded, a reviewer cannot tell an enumeration that is complete from one that stopped at the usual entry point, which is the #130 failure. | Decided — DR2 |
| 20261006 | Spanner | §1.2's forward-only bullet names only the wording rule. Left alone, the entry-path rule would read as applying to every criterion already on the queue. It is extended to name the entry-path rule too. The call-site rule binds specs, and `docs/dev/specs/` holds no spec but the template, so it needs no carve-out. | Decided — step 1c |
| 20261006 | Spanner | The template points at §1.2 with an example row and a one-line citation, not a copy of either rule. A spec-template column for the entry path was considered and not taken: `automation/closeout_acs.py` reads §5 rows by id only, so a column is safe, but a fourth column is a second statement of the rule in table form. | Decided — DR3 |
| 20261006 | Ray | Issue #135 says #131 carries the close-out's *a test that does not run reports as skipped* proposal. It does not: `docs/DEVELOPMENT_STANDARDS.md` §6 has no such rule, and `PytestReturnNotNoneWarning` as an error catches only a test that returns a value, not a bare early `return`. #131 is closed, so the rule had no live home. | Folded in as step 4 and AC8.1 — a declared scope extension. No issue AC names it, and issue AC6 forbids editing #135 to add one. A search of `tests/` and `automation/` finds no test that skips by early `return`, so the rule lands unbroken |
| 20261006 | Ray | The first wording of the step 4 bullet (*"a test that cannot run … calls `pytest.skip()`"*) reads as permission to skip a test that does not run successfully — the same misreading of `SKIP_API_TESTS` that §1.5 records | Reworded. The bullet governs reporting only and says so; the one mechanism is `@pytest.mark.skipif`, decided before the test body runs, so a skip cannot be a reaction to the outcome; a test that ran and failed is a failure. `pytest.skip()` is dropped because it can be called after the test has exercised the system. Ray then found the headline still described one situation rather than the general rule; it now states that a test reports what actually happened, and defines passed, failed and skipped, so the early-`return` case is one instance of the rule rather than the rule itself. The suite's one existing skip, `tests/test_ai_providers_live.py:28`, is a `skipif` on absent credentials and complies |
| 20261006 | Ray | **Approved.** | `Status: Approved`. Implementation may begin at step 1 |

---

## 1. Scope

**In scope:**

- `docs/DEVELOPMENT_STANDARDS.md` §1.2 — two new bullets and one edit to the forward-only bullet.
- `docs/dev/specs/_TEMPLATE_SPEC.md` §2 and §5.
- `CLAUDE.md` § Common Pitfalls, the *Component-verified ≠ integration-verified* line.
- `docs/DEVELOPMENT_STANDARDS.md` §6 — one new bullet, a declared scope extension (Decision Log, Ray, 20261006).

**Out of scope:**

- **Proposal 2 of the #79 / #126 close-out** (the recorded command is the one run). §6 already carries it, from #131.
- **`CLAUDE.md` Role 2's review questions.** Questions 5 and 7 are adjacent to these rules but are review prompts, not copies of them; nothing in the issue asks for a Caliper question.
- **`.claude/skills/closeout/`** and `automation/closeout_acs.py`. Neither states either rule, and close-out does not judge AC content.
- **Every existing issue and its criteria.** Issue AC6.
- **The archived results artifact** `docs/archive/results/VENDOR_SDK_PINNING_RESULTS.md`. §1.5 makes it read-only history; it is the origin of the two rules, not a source this spec relies on.

## 3. Design rules

- **DR1 —** Each rule has one home, §1.2. `CLAUDE.md` and the template cite it; neither restates it (`CLAUDE.md` opening paragraph).
- **DR2 —** The call-site enumeration records the search that produced it, so its completeness is reviewable.
- **DR3 —** Template text is a prompt and a citation. If a template line could be deleted without losing anything §1.2 says, it is the right size.

## 4. Steps

Before step 1, run `pytest` and `pytest automation/` from the repository root on this branch and record both sets of counts — the baseline for AC7.1.

**Step 1 — `docs/DEVELOPMENT_STANDARDS.md` §1.2.**

1a. Insert as a new bullet directly after the bullet beginning `- Every claim about existing behaviour is verified against source at authoring time` and its two sub-bullets:

```markdown
- **A contract change enumerates its call sites.** Where a spec changes a signature, a required input, or an invariant of something already called elsewhere, its §2 table lists every call site found by a search of the whole repository — `tests/` and `automation/` included — together with the search that found them, and an acceptance criterion covers the whole enumerated set. A call site that bypasses the usual entry point is still a call site. #79 gave the providers a required policy input, its §2 enumerated nothing that constructs a provider, and the seven construction sites outside `ProviderManager` broke without any criterion covering them (#130).
```

1b. Insert as a new bullet directly after the bullet beginning `- **A criterion names a property of the delivered system.` and its sub-bullets:

```markdown
- **A criterion that verifies changed behaviour names the entry path it exercises.** Where more than one entry path reaches the change, the criteria cover the set, or state which paths are omitted and why. A green check through the one path that works is not coverage: #79's live check ran `workmain providers test claude`, which goes through `ProviderManager` — the one path the #130 defect could not reach.
```

1c. Replace:

```markdown
- **The wording rule applies to criteria authored from here forward.** Criteria already written are not rewritten and no issue is reopened to reword one; there is no retrospective sweep of the queue.
```

with:

```markdown
- **The wording rule and the entry-path rule apply to criteria authored from here forward.** Criteria already written are not rewritten and no issue is reopened to reword one; there is no retrospective sweep of the queue.
```

Commit.

**Step 2 — `docs/dev/specs/_TEMPLATE_SPEC.md`.**

2a. §2 — replace the empty table:

```markdown
| Claim | Evidence (file:line, symbol) |
| --- | --- |
```

with:

```markdown
| Claim | Evidence (file:line, symbol) |
| --- | --- |
| Call sites of `<symbol>`, found by `grep -rn '<pattern>' --include='*.py' .` | every `file:line` the search returns |
```

and insert after the paragraph beginning `Anything not verified here is a guess`:

```markdown
The call-sites row is required where this spec changes a signature, a required input or an invariant of something already called elsewhere — `docs/DEVELOPMENT_STANDARDS.md` §1.2.
```

2b. §5 — insert after the line beginning `Semantic criteria is only applicable`:

```markdown
A criterion that verifies changed behaviour names the entry path it exercises — `docs/DEVELOPMENT_STANDARDS.md` §1.2 states what it owes where there is more than one.
```

Commit.

**Step 3 — `CLAUDE.md` § Common Pitfalls.** Replace:

```markdown
- **Component-verified ≠ integration-verified** — trace handle and session provenance at every call site, diff drafted code against any claimed reference verbatim (not just shape), and never accept an elided "unchanged" block without checking it against the recon's own quote.
```

with:

```markdown
- **Component-verified ≠ integration-verified** — the spec-time rules (call sites, entry paths) are `docs/DEVELOPMENT_STANDARDS.md` §1.2. At implementation, trace handle and session provenance at every call site, diff drafted code against any claimed reference verbatim (not just shape), and never accept an elided "unchanged" block without checking it against the recon's own quote.
```

Commit.

**Step 4 — `docs/DEVELOPMENT_STANDARDS.md` §6.** Insert as a new bullet directly after the bullet beginning `- Non-application suites, such as \`pytest automation/\``:

```markdown
- **A test reports what actually happened.** Passed means it ran and its assertions held. Failed means it ran and did not — an error, a timeout or a wrong answer. Skipped means it did not run because a precondition declared with `@pytest.mark.skipif` was absent; that is the only way a test is skipped, and it is decided before the test exercises anything. A test never reports passed without having run, which is what an early `return` does, and never reports skipped after it has run. A skip is never added to turn a red suite green. Four live API tests in `tests/test_ai_clients.py` returned early under `SKIP_API_TESTS=1`, counted as passed, and the failures they hid shipped to `main` (#130, #131).
```

Commit.

**Step 5 — results artifact** `docs/dev/results/CALL_SITES_AND_ENTRY_PATHS_RESULTS.md`: the §3 AC table, the baseline and after counts for both suites, and every `gh issue` write command this work ran. Commit.

### Authorization points

None.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | §1.2 requires a spec that changes a signature, a required input or an invariant of something already called elsewhere to enumerate every call site found by search in its §2 table, and requires a criterion covering the whole set | Stated reading by Ray of §1.2's *A contract change enumerates its call sites* bullet, read for the trigger, the search-wide enumeration, and the covering criterion |
| AC2.1 | §1.2 requires a criterion verifying changed behaviour to name its entry path, and where more than one exists, to cover the set or state the omissions and why | Stated reading by Ray of §1.2's entry-path bullet, read for both obligations |
| AC3.1 | Each rule is stated once, in §1.2; `CLAUDE.md`, the spec template and `.claude/` cite it and carry no copy | Stated reading by Ray of the step 2 and step 3 text against `CLAUDE.md`'s opening single-home rule; `grep -rn -i 'call site\|entry path' CLAUDE.md docs/dev/specs/_TEMPLATE_SPEC.md .claude/` returns only lines that cite §1.2 or the pitfall's implementation-time clause |
| AC4.1 | An author starting from the template is prompted for the call-site enumeration in §2 and the entry path in §5 | Reading `docs/dev/specs/_TEMPLATE_SPEC.md` §2 and §5 for the step 2 text |
| AC5.1 | Both rules have a live home in §1.2, and nothing live cites the archived artifact as their source | The results artifact's AC1.1 and AC2.1 rows name the §1.2 bullets; `grep -rn 'VENDOR_SDK_PINNING_RESULTS' docs/dev/ CLAUDE.md .claude/` returns no hit that treats the artifact as authoritative — this spec's own §1 and §5 mentions name it as origin and as the check |
| AC6.1 | No existing issue is edited, reopened or restructured by this work | The results artifact lists every `gh issue` write command this work ran; the list contains no `edit`, `reopen` or `--body` invocation against an issue this work did not create |
| AC7.1 | The test suites are unchanged by this work | `pytest` and `pytest automation/` report the same passed, failed and skipped counts as the baseline recorded before step 1, both recorded in the results artifact §5 |
| AC8.1 | §6 requires every test's reported outcome — passed, failed or skipped — to be what actually happened, with `@pytest.mark.skipif` as the only way to skip, and grants no way to turn a test that ran and failed into a skip | Stated reading by Ray of the step 4 bullet in §6, read for each outcome's definition, `skipif` as the only skip, and the absence of any permission to skip a failing test; `grep -rn 'pytest.skip(' tests/ automation/` returns zero hits, so no test skips from inside its body |

## 6. Test plan

No file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` changes. Both suites are run before step 1 and after step 4 for AC7.1; close-out runs them again regardless.

## 7. Risks and rollback

Each step is one commit and reverts alone. The only risk is wording that restates rather than cites, which AC3.1's reading catches.
