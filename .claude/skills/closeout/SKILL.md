---
name: closeout
description: Perform an issue's close-out — merge the branch where its type requires, bump the version, cut the tag and Release, restart the daemon, mark the spec Shipped, and complete the docs/dev/results/ artifact. Stops at each authorization point it crosses and nowhere else.
disable-model-invocation: true
user-invocable: true
---

# `/closeout`

User-initiated only. This skill **performs** the close-out — it is not a report. `/closeout` merges, bumps, tags, releases, restarts and completes the results artifact for whatever issue's branch is currently checked out. It does **not** post the closing comment and does **not** close the issue: it composes the comment and prints the `gh issue comment` command that would post it (DR1). Posting and closing stay Ray's, on the same principle as merging a `dev → main` PR (§2.8).

## When this runs

At the point Anvil's last implementation commit lands on the branch being closed out, before that branch has merged anywhere. `--branch <name>` is the escape hatch for an issue whose branch has already merged and been deleted (§2.3) — in that case the branch is resolved from the merge commit instead, and every file read below comes from its second parent, `git show <merge>^2:<path>`, not the working tree. These are the only two modes, and this skill states which one it is in before reporting a single row (Caliper F2) — the retired script mixed them, reading the working tree while resolving the branch from refs.

**Base ref.** Anything asking what this branch changed diffs against `git merge-base main <branch>`, never against `main` itself — a branch cut before a later change landed on `main` differs from it without having touched it (Caliper F9, F13).

## Preflight — read-only, total, no writes

Run every row below, in order, every time. **Nothing here writes anything.** No write of any kind happens until every row has run and passed, so a failing run leaves the repository exactly as it found it and is re-runnable with nothing to undo (DR3).

Every row is reported `pass`, `fail`, or `n/a`, **with its reason**, on every run — a failing run as much as a passing one. A check that could not be evaluated is a failure, never `n/a` (DR6): "could not determine" is not the same claim as "does not apply here", and reporting the two alike is how a row silently stops being checked. Failures print once, to stderr only (C7) — never to stdout as well, which is how four failures once read as eight.

`P5` and `P6` both report, always. When the results artifact named by `P5` is absent, `P6` fails too, reading `not evaluated — the artifact named by P5 is absent`. It is never silently skipped and never `n/a`: two failures for one cause is correct, because they carry different remedies (Caliper G5).

| # | Check | `n/a` when | Remedy on failure |
| --- | --- | --- | --- |
| P1 | The working tree is clean | never | Commit or stash before running close-out |
| P2 | The branch resolves — `git branch --show-current`, or `--branch <name>` for an already-merged branch | never | Check out the branch being closed out, or pass `--branch` |
| P3 | The branch prefix is one of `chore`, `feature`, `hotfix` | never | §2.2 defines three; a fourth is a mistake or a standards change this table has not caught up with |
| P4 | Exactly one spec in `docs/dev/specs/` names this branch in its `**Branch:**` field, and its `**Status:**` is `Approved` | never | No spec: §1.1 permits no implementation without one. Several: the `**Branch:**` fields collide and one is wrong. `**Status:** Shipped`: this issue has already been closed out, and a second run is not expected to pass |
| P5 | The results artifact exists at the derived path and its `**Status:**` is `Shipped` or `Superseded` | never | Anvil writes it from `_TEMPLATE_RESULTS.md` as his last implementation step |
| P6 | `python3 automation/closeout_acs.py --branch <name>` exits `0` — every spec AC id has a row, every row is `Met` or a `Carried` citing `#N`, every `Met` row has evidence, and no row carries an id the spec lacks | never | The module names the offending id on stderr. Fill the missing row, or carry the AC to a follow-up issue and cite it. This skill does not judge whether the disposal is right — that is what P6 is not (DR4) |
| P7 | The spec's §5 maps its sub-ACs to the issue's ACs, as an opening paragraph or an `Issue AC` column | never | Add the mapping — §1.2 requires it in either form |
| P8 | `pytest tests/` passes | never | Fix the failures; a close-out cannot proceed past a red suite |
| P9 | `pytest automation/` passes | the branch changed no path under `automation/`, diffed against the merge base | Fix the failures |
| P10 | `automation/check_release_integrity.py` exits zero | never | Repo-wide, so a `chore/*` branch can meet it without having caused it; the fix is the missing Release or `CHANGELOG.md` section it names |
| P11 | Against the merge base: `workmain/__version__.py` is unchanged, no `CHANGELOG.md` section was added, and no tag points at the branch | branch type is `feature` or `hotfix`, where all three are required rather than forbidden | §2.2 forbids all three on `chore/*`. **This is an assertion of absence and is never reported `n/a` for a `chore/*` branch** |

If any row fails, the run stops here having written nothing, and prints the remedy for each failure.

## Choosing the variant

Reached only when every preflight row passed. Read `P3`'s branch prefix and load exactly one reference file — never more than one, and never inline what it contains:

- `chore/*` → `references/chore.md`
- `feature/*` → `references/feature.md`
- `hotfix/*` → `references/hotfix.md`

Each carries that type's full perform sequence: what gets committed on the branch before the first merge, the merge order, the two authorization points, and — where the type carries one — the post-merge daemon restart.

## The two stops

Every close-out crosses exactly two authorization points (§1.4): **merging this branch to `main`** (shaped as the PR wait on `feature/*`, since Ray merges that PR himself), and **deleting this branch, local and remote**. Each is one `AskUserQuestion` call stating what is about to happen and that it is irreversible or reaches outside the working tree. Two answers — proceed, or stop — and *stop* ends the run naming what has already happened and what has not.

Nothing else stops. The post-merge daemon restart does not stop — §1.4 carves it out by name, so it runs as a step. Pushing `main` or `dev` does not stop. Tag and Release creation do not stop. Anything not named above is a step.

## Anything not covered here

**STOP and surface to Ray.** No self-resolution, no scope adjustment — the same rule that governs every implementation session.
