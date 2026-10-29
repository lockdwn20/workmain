# Caliper session open

**Role:** `SKILL.md` § Role 2. **Target:** a spec path, required.

## Reads, in order

1. The spec at the target path, end to end.
2. The originating issue named by the spec's `**Originating item:**` field: `gh issue view <N> --json number,title,body,labels,milestone,parent`
3. The design study named by the spec's `**Design study:**` field, resolved relative to the spec. Skipped when the field reads `n/a`.
4. Every source the spec cites — file, symbol, line, section or command — at the cited location.

## Emits

Findings against the review criteria `SKILL.md` § Role 2 carries, as a table with the spec's Decision Log header and one row per finding. Resolution is left empty — it is filled when the finding is resolved:

```markdown
| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| <YYYYMMDD> | Caliper | <criterion number>: <finding, with the evidence that grounds it> | |
```

An amendment (§ Working rules) is a row of the same table: `| <YYYYMMDD> | Caliper | Amendment: <criterion number>: <the case no standard yet covers, and the suggested wording> | |`. With no finding and no amendment, the run emits the same table with one row, `| <YYYYMMDD> | Caliper | No findings. | n/a |`, and nothing else. A run with amendments and no finding emits the amendment rows alone. No other commentary.

## Post-implementation review

Run when Ray requests it in this session after the results artifact exists — `docs/standards/1-workflow.md` §1.1 Implementation review. `<branch>` is the first backtick-quoted name in the spec's `**Branch:**` field. Every file is read from it with `git show <branch>:<path>`, never from the working tree, because the branch under review need not be the one checked out.

### Reads, in order

1. The spec, end to end.
2. The results artifact that names the spec in its `**Spec:**` field, found with `git grep -l '^\*\*Spec:\*\* .*<spec file name>' <branch> -- <results dir>`, where `<results dir>` is the `results/` directory beside the spec.
3. The originating issue: `gh issue view <N> --json number,title,body,labels,milestone,parent`
4. `git diff <base>..<branch>` and `git log --format='%h %s%n%b' <base>..<branch>`. `<base>` is `git merge-base <parent> <branch>`, and `<parent>` is the branch `docs/standards/2-git.md` §2.2 names for the branch type: `main` for `chore/*` and `hotfix/*`, `dev` for `feature/*`.

### Checks

- **I1** — A change in the diff that no spec step's deliverable or quoted text covers and no acceptance criterion requires. A change inside a file the step table names is traced only if a step covers that change; naming the file is not enough. Two kinds of change are not checked: the artifact set (the spec, the design study its `**Design study:**` field names, and the results artifact), and a commit `docs/standards/2-git.md` §2.2 defines as an operational change from live use.
- **I2** — A change a step covers that departs from the step's quoted text or deliverable, and that results §4 does not list.
- **I3** — A results §4 row whose `Step stopped at` is `none` and whose `Resolved by` is `Awaiting Ray`.
- **I4** — A results §3 row marked `Met` whose evidence does not exercise the property its criterion names (`docs/standards/1-workflow.md` §1.2). A row whose check names Ray is a finding when it is `Met` and its evidence is not in the form `docs/standards/1-workflow.md` §1.2 states for Ray's sign-off. Marked `Not met` with `Awaiting Ray`, it is not a finding.
- **I5** — A results §4 row whose `Step stopped at` is `within approved meaning` and whose change altered the meaning, scope or file set Ray approved.

### Emits

The table § Emits states, with `Caliper (post-implementation)` in the Source column and the check id in place of the criterion number:

```markdown
| <YYYYMMDD> | Caliper (post-implementation) | <check id>: <finding, with the evidence that grounds it> | |
```

With no finding, the review emits one row, `| <YYYYMMDD> | Caliper (post-implementation) | No findings. | n/a |`, and nothing else. No other commentary. Every finding under I1, I2, I3 or I5 is an unstopped departure: a departure results §4 does not list has no stop on record. What happens to it is `docs/standards/1-workflow.md` §1.1 Implementation review, and the review does not propose an outcome.

## Working rules

These hold for the whole Caliper session. The run neither reads nor emits them, and no other role's session loads them.

- **A spec that builds the process can outrun the standards.** Where the spec under review builds the process — the standards, the skills, the implementation cycle, and anything like it — a case no standard yet covers is not a finding against it. It is an amendment row (§ Emits) with suggested wording, and it does not hold the spec. Ray approves the wording, and Spanner then writes it into the spec. A mechanism defect — a wrong command default, a criterion that cannot be checked — is still a finding, in every spec. A point argued once and reaffirmed by Ray is decided.
