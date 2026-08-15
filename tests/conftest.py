"""Project-wide pytest fixtures."""

from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine

from tests.support.postgresql import (
    TestDatabaseConfigurationError,
    load_test_database_url,
)


@pytest.fixture
def test_database_url() -> str:
    """Return the externally supplied PostgreSQL target or fail explicitly."""
    try:
        return load_test_database_url()
    except TestDatabaseConfigurationError as error:
        failure_message = str(error)

    pytest.fail(failure_message, pytrace=False)


@pytest.fixture
def migrated_database_engine(test_database_url: str) -> Iterator[Engine]:
    """Upgrade the externally supplied target for one non-parallel PG test."""
    engine = create_engine(test_database_url)
    config = Config("alembic.ini")
    with engine.connect() as connection:
        config.attributes["connection"] = connection
        command.downgrade(config, "base")
        command.upgrade(config, "head")
    try:
        yield engine
    finally:
        with engine.connect() as connection:
            config.attributes["connection"] = connection
            command.downgrade(config, "base")
        engine.dispose()
