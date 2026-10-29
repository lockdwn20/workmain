## 7. File Placement

| Content | Location |
| --- | --- |
| CLI commands | `workmain/cli/commands/` |
| CLI output: the renderer, views and the group class (`WorkmAInGroup`) | `workmain/cli/output.py` |
| CLI argument types | `workmain/cli/params.py` |
| Repositories | `workmain/database/repositories/` |
| Models | `workmain/database/models.py` |
| Migrations | `workmain/database/migrations/NNN_name.sql` |
| Daemon / scheduler | `workmain/daemon/` |
| AI providers | `workmain/ai/providers/` |
| Workflows | `workmain/workflows/` |
| Services | `workmain/services/` |
| Utilities | `workmain/utils/` |
| Configs | `config/` |
| Templates | `templates/` |
| Staged report output | `staging/` — **not** `output/`, which does not exist |
| Tests / data / mocks | `tests/`, `tests/fixtures/`, `tests/mocks/` |
| Utility scripts | `scripts/` |
| Non-application dev tooling | `automation/` |
| Design studies and recon | `docs/dev/design/` |
| Specs | `docs/dev/specs/` |
| Implementation results | `docs/dev/results/` |

Dev artifacts always go in `docs/dev/<type>/`, never in the `docs/` root.
