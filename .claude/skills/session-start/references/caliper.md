# Caliper session open

**Role:** `CLAUDE.md` § Role 2. **Target:** a spec path, required.

## Reads, in order

1. The spec at the target path, end to end.
2. The originating issue named by the spec's `**Originating item:**` field: `gh issue view <N> --json number,title,body,labels,milestone,parent`
3. The design study named by the spec's `**Design study:**` field, resolved relative to the spec. Skipped when the field reads `n/a`.
4. Every source the spec cites — file, symbol, line, section or command — at the cited location.

## Emits

Findings against the review criteria `CLAUDE.md` § Role 2 carries, as a table with the spec's Decision Log header and one row per finding. Resolution is left empty — it is filled when the finding is resolved:

```markdown
| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| <YYYYMMDD> | Caliper | <criterion number>: <finding, with the evidence that grounds it> | |
```

With no finding, the run emits `No findings.` and nothing else. No other commentary.
