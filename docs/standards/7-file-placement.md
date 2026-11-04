## 7. File Placement

Where the development process keeps its own files. Where application code lives, and the files the application reads and writes, is `docs/ARCHITECTURE.md`.

| Content | Location |
| --- | --- |
| Design studies and recon | `docs/dev/design/` |
| Specs | `docs/dev/specs/` |
| Implementation results | `docs/dev/results/` |
| Application tests, `test_<component>.py`, collected by a bare `pytest` through `testpaths` | `tests/` |
| Test data (JSON, CSV), never Python test files | `tests/fixtures/` |
| Fakes for external services, never test files | `tests/mocks/` |
| Utilities and demos, never tests | `scripts/` |
| Non-application dev tooling and its own tests (`*_test.py`), never mixed with the application suite | `automation/` |

Dev artifacts always go in `docs/dev/<type>/`, never in the `docs/` root.

`scripts-deprecated/` is excluded from collection. Nothing is added to it and it is never run with pytest; a diagnostic script goes in `scripts/`.
