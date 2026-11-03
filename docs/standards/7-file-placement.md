## 7. File Placement

Where the development process keeps its own files. Where application code lives, and the files the application reads and writes, is `docs/ARCHITECTURE.md`.

| Content | Location |
| --- | --- |
| Design studies and recon | `docs/dev/design/` |
| Specs | `docs/dev/specs/` |
| Implementation results | `docs/dev/results/` |
| Tests, test data and mocks | `tests/`, `tests/fixtures/`, `tests/mocks/` |
| Utility scripts | `scripts/` |
| Non-application dev tooling | `automation/` |

Dev artifacts always go in `docs/dev/<type>/`, never in the `docs/` root.
