# Caliper session open

**Role:** `SKILL.md` § Role 2. **Target:** a spec path, required.

## Choosing the review

A run is one Caliper pass, in a session of its own (`SKILL.md` § Role 2). `<branch>` is the first backtick-quoted name in the `**Branch:**` field of the spec as committed at `HEAD` (`git show HEAD:<target path>`). Where `HEAD` holds no file at the target path, the run reports the spec unreadable (`SKILL.md` § Rules every run holds) and reviews nothing (§ Emits): it is run with a branch checked out that holds the spec. When `git rev-parse --verify --quiet <branch>` exits 0 and § Post-implementation review's read 2 finds a results artifact on `<branch>`, the run is § Post-implementation review. Otherwise it is the spec review: § Reads, in order and § Emits.

## Reads, in order

1. The spec at the target path, end to end, read with a clean working tree. Where `git status --porcelain` prints anything, the run reviews nothing (§ Emits). A clean tree makes this read, and every read of a repository file below, one of the commit at `HEAD`.
2. The originating issue named by the spec's `**Originating item:**` field: `gh issue view <N> --json number,title,body,labels,milestone,parent`
3. The design study named by the spec's `**Design study:**` field, resolved relative to the spec. Skipped when the field reads `n/a`.
4. Every source the spec cites — file, symbol, line, section or command — at the cited location.
5. `docs/standards/README.md`, `docs/standards/1-workflow.md`, `docs/standards/2-git.md` and `docs/standards/3-code.md`, end to end.
6. `docs/ARCHITECTURE.md`, end to end, and the output of `python3 automation/architecture_check.py`.
7. The pass rows already in the spec's Decision Log. Where there is one, this is a later pass: `git diff <commit> -- <spec path>`, from the commit the last pass row names, is what changed since it.

## Emits

The findings, then the pass row, as a table with the spec's Decision Log header. Each finding names its criterion and its category, and whether it blocks (`SKILL.md` § Role 2). Resolution is left empty; it is filled when the finding is resolved:

```markdown
| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| <YYYYMMDD> | Caliper | <criterion number>, <category>, <blocking or non-blocking>: <finding, with the evidence that grounds it> | |
| <YYYYMMDD> | Caliper | Pass at <commit>, <full, or changes since <commit>>: <n> items checked, <b> blocking, <m> non-blocking. | n/a |
```

The pass row is always the last row, and `<commit>` is `git rev-parse --short HEAD`, the commit the spec and every repository file were read at. Below the table, and not recorded in the spec, the pass shows its coverage: one row for each acceptance criterion, design rule, §2 claim and step in its scope, with what it was checked against and its result.

A run that reviews nothing, because `HEAD` holds no spec at the target path (§ Choosing the review) or the working tree is not clean (read 1), emits no table and no row to record. It emits one line, `Not reviewed:` and the reason, followed by each path `git status --porcelain` lists where the tree is not clean. No other commentary.

## Post-implementation review

Run when § Choosing the review selects it — `docs/standards/1-workflow.md` §1.1 Implementation review. Every file is read from `<branch>` with `git show <branch>:<path>`, never from the working tree, because the branch checked out need only hold the spec (§ Choosing the review) and need not be `<branch>`.

### Reads, in order

1. The spec, end to end.
2. The results artifact that names the spec in its `**Spec:**` field, found with `git grep -l '^\*\*Spec:\*\* .*<spec file name>' <branch> -- <results dir>`, where `<results dir>` is the `results/` directory beside the spec.
3. The originating issue: `gh issue view <N> --json number,title,body,labels,milestone,parent`
4. `git diff <base>..<branch>` and `git log --format='%h %s%n%b' <base>..<branch>`. `<base>` is `git merge-base <parent> <branch>`, and `<parent>` is the branch `docs/standards/2-git.md` §2.2 names for the branch type: `main` for `chore/*` and `hotfix/*`, `dev` for `feature/*`.

### Checks

- **I1** — A change in the diff that no spec step's deliverable or quoted text covers and no acceptance criterion requires. A change inside a file the step table names is traced only if a step covers that change; naming the file is not enough. Two kinds of change are not checked: the artifact set (the spec, the design study its `**Design study:**` field names, and the results artifact), and a commit `docs/standards/2-git.md` §2.2 defines as an operational change from live use.
- **I2** — A change that departs from the contract (`SKILL.md` § Role 3) and that results §4 does not list as a departure, or a decision below the contract that results §4's Decisions table does not record.
- **I3** — A results §4 row whose `Step stopped at` is `none` and whose `Resolved by` is `Awaiting Ray`.
- **I4** — A results §3 row marked `Met` whose evidence does not exercise the property its criterion names (`docs/standards/1-workflow.md` §1.2). A row whose check names Ray is a finding when it is `Met` and its evidence is not in the form `docs/standards/1-workflow.md` §1.2 states for Ray's sign-off. Marked `Not met` with `Awaiting Ray`, it is not a finding.
- **I5** — A results §4 row whose `Step stopped at` is `within approved meaning` and whose change altered the meaning, scope or file set Ray approved.
- **I6** — A new finding from `automation/architecture_check.py` or a violation from `automation/style_check.py`, each run on `<branch>`.
- **I7** — A converted command that reads the database directly, which the architecture check cannot see (`docs/ARCHITECTURE.md` section 3, Unconverted commands).

### Emits

The table § Emits states, with `Caliper (post-implementation)` in the Source column and the check id in place of the criterion number:

```markdown
| <YYYYMMDD> | Caliper (post-implementation) | <check id>: <finding, with the evidence that grounds it> | |
```

With no finding, the review emits one row, `| <YYYYMMDD> | Caliper (post-implementation) | No findings. | n/a |`, and nothing else. No other commentary. Every finding under I1, I2, I3 or I5 is an unstopped departure: a departure results §4 does not list has no stop on record. What happens to it is `docs/standards/1-workflow.md` §1.1 Implementation review, and the review does not propose an outcome.

## Working rules

These hold for the whole Caliper session. The run neither reads nor emits them, and no other role's session loads them.

- **A case no standard covers is a standards gap** (`SKILL.md` § Role 2): never a finding against the spec, and never wording for the spec. A mechanism defect, such as a wrong command default or a criterion that cannot be checked, is still a finding, in every spec. A point argued once and reaffirmed by Ray is decided.
