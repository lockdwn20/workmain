# WorkmAIn Development Standards

How work gets built. `.claude/skills/session-start/SKILL.md` owns who does what (the three-role model). `CLAUDE.md` owns what this project is (stack, architecture) and domain decisions (tag system, time format, trigger terminology, write-path map). This document owns everything else — process, git workflow, code patterns, database, CLI structure, and testing.

The only text here also stated in `CLAUDE.md` is its § Critical Rules subset; nothing else appears in both.

## How this document is stored

This is one document, stored as this header and one file for each top-level section. Sections are numbered once across all the files: the file holding a section is the one whose name begins with the section's top-level number, so `§4.3` is in `docs/standards/4-database.md`. "This document", in any of these files, means all of them.

It was a single file, `docs/DEVELOPMENT_STANDARDS.md`, until issue #244 split it. No § number changed. A citation of that file, in `docs/archive/`, `CHANGELOG.md` or an issue body, resolves by its § number to the file below.

## Sections

Read the section that covers the work before doing it.

| File | Section | Read it before |
| --- | --- | --- |
| `docs/standards/1-workflow.md` | §1 Development Workflow | any work — it governs every role |
| `docs/standards/2-git.md` | §2 Git Workflow | cutting a branch, committing, merging or releasing |
| `docs/standards/3-code.md` | §3 Code Standards | writing or changing a module |
| `docs/standards/4-database.md` | §4 Database Standards | code that opens a session or uses a repository, or a migration |
| `docs/standards/5-cli.md` | §5 CLI Standards | adding or changing a command |
| `docs/standards/6-testing.md` | §6 Testing Standards | writing a test, or recording test evidence |
| `docs/standards/7-file-placement.md` | §7 File Placement | creating a file |
