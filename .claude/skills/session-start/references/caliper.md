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

## Working rules

These hold for the whole Caliper session. The run neither reads nor emits them, and no other role's session loads them.

- **A spec that builds the process can outrun the standards.** Where the spec under review is itself writing the rules — the standards, the skills, the implementation cycle — a case no standard yet covers is not a finding against it. It is an amendment row (§ Emits), with suggested wording, for Role 1 to write into the standards; it does not hold the spec. A mechanism defect — a wrong command default, a criterion that cannot be checked — is still a finding, in every spec. A point argued once and reaffirmed by Ray is decided.
