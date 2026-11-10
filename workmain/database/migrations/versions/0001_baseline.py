"""
Baseline: the live schema when Alembic was adopted.

The schema is in 0001_baseline.sql beside this file, a cleaned schema-only
dump of the live database. Upgrading from an empty database runs it whole;
the live database was stamped at this revision rather than built by it.
"""

from pathlib import Path
from typing import Sequence, Union

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SQL = Path(__file__).with_name("0001_baseline.sql")


def upgrade() -> None:
    """
    Create the whole schema from 0001_baseline.sql.

    The text goes to the driver as written, without SQLAlchemy's
    bind-parameter processing, so nothing in it is read as a parameter.
    """
    op.get_bind().exec_driver_sql(_SQL.read_text(encoding="utf-8"))


def downgrade() -> None:
    """
    Refuse: the baseline has no earlier schema to return to.
    """
    raise NotImplementedError(
        "Undoing the baseline would drop every table in the schema; "
        "there is no earlier revision to return to."
    )
