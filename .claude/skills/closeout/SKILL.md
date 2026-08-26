---
name: closeout
description: Perform an issue's close-out — merge the branch where its type requires, bump the version, cut the tag and Release, restart the daemon, mark the spec and design artifact Shipped, and complete the docs/dev/results/ artifact. Re-enterable: the resume point is read from the repository, not from a marker. Stops only at the merge to main.
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
| P4 | Exactly one spec in `docs/dev/specs/` names this branch in its `**Branch:**` field, and its `**Status:**` is `Approved` or `Shipped` | never | No spec: §1.1 permits no implementation without one. Several: the `**Branch:**` fields collide and one is wrong. `Shipped` is **not** a failure — it means an earlier run reached the artifact step, and § Resume point decides where this one starts |
| P5 | The results artifact exists at the derived path and its `**Status:**` is one `docs/DEVELOPMENT_STANDARDS.md` §1.5 defines | never | Anvil writes it from `_TEMPLATE_RESULTS.md` as his last implementation step. Close-out is what sets it to `Shipped`; requiring that here would reproduce the re-entry defect this skill was corrected for |
| P5a | The design artifact named by the spec's `**Design study:**` field exists, and its `**Status:**` is one `docs/DEVELOPMENT_STANDARDS.md` §1.5 defines | never | No field: §1.1 permits no spec without a recon or design study first. Missing file: the citation is broken and the spec cannot be verified against what it was built from |
| P6 | `python3 automation/closeout_acs.py --branch <name>` exits `0` — every spec AC id has a row, every row is `Met` or a `Carried` citing `#N`, every `Met` row has evidence, and no row carries an id the spec lacks | never | The module names the offending id on stderr. Fill the missing row, or carry the AC to a follow-up issue and cite it. This skill does not judge whether the disposal is right — that is what P6 is not (DR4) |
| P7 | The spec's §5 maps its sub-ACs to the issue's ACs, as an opening paragraph or an `Issue AC` column | never | Add the mapping — §1.2 requires it in either form |
| P8 | `pytest tests/` passes | never | Fix the failures; a close-out cannot proceed past a red suite |
| P9 | `pytest automation/` passes | the branch changed no path under `automation/`, diffed against the merge base | Fix the failures |
| P10 | `automation/check_release_integrity.py` exits zero | never | Repo-wide, so a `chore/*` branch can meet it without having caused it; the fix is the missing Release or `CHANGELOG.md` section it names |
| P11 | Against the merge base: `workmain/__version__.py` is unchanged, no `CHANGELOG.md` section was added, and no tag points at the branch | branch type is `feature` or `hotfix`, where all three are required rather than forbidden | §2.2 forbids all three on `chore/*`. **This is an assertion of absence and is never reported `n/a` for a `chore/*` branch** |

If any row fails, the run stops here having written nothing, and prints the remedy for each failure.

## Resume point

Close-out is re-enterable. **Nothing about where a run stopped is recorded.** The resume point is read from the repository on every run, so a run ended by a declined prompt, a closed terminal, or a crash all re-enter the same way.

After preflight and before the first write, walk the variant's steps in order and find the first whose **Done when** observable is not yet true. That step is where this run starts. State the resume point before writing anything — which steps are already done, and which one is next.

Nothing is inferred from a status field, a marker file, or anything this skill wrote. A `**Status:** Shipped` spec means step 1 ran, not that the close-out finished.

If every step's observable is already true, the close-out is complete. Say so and stop — do not re-merge, re-tag, or re-compose the closing comment.

## Choosing the variant

Reached only when every preflight row passed. Read `P3`'s branch prefix and load exactly one reference file — never more than one, and never inline what it contains:

- `chore/*` → `references/chore.md`
- `feature/*` → `references/feature.md`
- `hotfix/*` → `references/hotfix.md`

Each carries that type's full perform sequence: what gets committed on the branch before the first merge, the merge order, the two authorization points, and — where the type carries one — the post-merge daemon restart.

## The stop

Every close-out crosses exactly **one** authorization point (§1.4): **merging this branch to `main`** — which on `feature/*` takes the shape of waiting for Ray to merge the `dev → main` PR, since §2.2 requires the PR and he merges it himself. It is one `AskUserQuestion` call stating what is about to happen. Two answers — proceed, or stop — and *stop* ends the run naming what has already happened and what has not.

Nothing else stops.

- **The post-merge restart does not stop** — §1.4 carves it out.
- Pushing `main` or `dev`, creating the tag, and creating the Release do not stop.
- **Deleting the branch does not stop.** No working branch in this project is ever pushed (§2.3), so the delete is a local ref removal, not the GitHub object deletion §1.4's set names. A branch that *does* exist on `origin` is the §2.3 exception: deleting it there is a GitHub object deletion and stops.

## The closing comment

Composed once the variant's last step is done, printed, and not run — `/closeout` does not post it and does not close the issue (DR1). Print it as `gh issue comment <N> --body-file -` with the body inline, so posting is one paste.

The body carries, in this order, every item that applies to the branch type:

- the merge commit SHA on `main`, and the branch it merged
- the path to the results artifact
- the AC verdict from `automation/closeout_acs.py` — the verdict itself, not a restatement of the table
- the version, the tag, and the Release URL — `feature/*` and `hotfix/*` only; §2.2 gives `chore/*` none of the three
- the confirmed `ActiveEnterTimestamp` — `feature/*` and `hotfix/*` only; §2.6 requires no restart on `chore/*`
- the PR number — `feature/*` only, which is where it first exists

An item that does not apply to this branch type is omitted, not written as `n/a`.

## Anything not covered here

**STOP and surface to Ray.** No self-resolution, no scope adjustment — the same rule that governs every implementation session.
