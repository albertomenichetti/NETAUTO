"""Installed Alembic environment for explicit PostgreSQL migration commands."""

from alembic import context
from sqlalchemy import Connection, engine_from_config, pool

from netauto.persistence.metadata import metadata
from netauto.settings import load_settings

config = context.config
target_metadata = metadata


def get_database_url() -> str:
    """Load the migration target from explicit NETAUTO process settings."""
    return load_settings().database_url


def run_migrations_offline() -> None:
    """Run migrations without creating an Engine."""
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations(connection: Connection) -> None:
    """Run migrations on an already established administrative connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Use an injected test connection or the explicit administrative target."""
    injected_connection = config.attributes.get("connection")
    if isinstance(injected_connection, Connection):
        run_migrations(injected_connection)
        return

    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_database_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
