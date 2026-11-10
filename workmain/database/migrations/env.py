"""
Alembic environment for the WorkmAIn schema.

Connects to the database DATABASE_URL in workmain.database.connection names,
built from the DB_* environment variables, so the configuration file holds no
database URL. The target metadata is the models' declarative base, which is
what Alembic compares a database against.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from workmain.database.connection import DATABASE_URL
from workmain.database.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Emit the revisions' SQL as script output, without connecting.
    """
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run the revisions against the database, in one transaction.
    """
    engine = create_engine(DATABASE_URL, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
