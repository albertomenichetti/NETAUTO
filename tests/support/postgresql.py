"""Explicit boundary for externally supplied PostgreSQL test configuration."""

import os
from collections.abc import Mapping

from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError

TEST_DATABASE_ENVIRONMENT_VARIABLE = "TEST_DATABASE_URL"


class TestDatabaseConfigurationError(ValueError):
    """The explicitly selected PostgreSQL suite lacks a valid target."""

    __test__ = False


def parse_test_database_url(value: str) -> URL:
    """Validate and parse the only supported test database URL form."""
    try:
        parsed = make_url(value)
    except ArgumentError as error:
        raise TestDatabaseConfigurationError(
            "TEST_DATABASE_URL must be a valid SQLAlchemy URL"
        ) from error

    if parsed.drivername != "postgresql+psycopg":
        raise TestDatabaseConfigurationError(
            "TEST_DATABASE_URL must use postgresql+psycopg and point to real "
            "PostgreSQL test infrastructure"
        )
    return parsed


def load_test_database_url(
    environment: Mapping[str, str] | None = None,
) -> str:
    """Load TEST_DATABASE_URL without runtime, localhost, or SQLite fallback."""
    source = os.environ if environment is None else environment
    value = source.get(TEST_DATABASE_ENVIRONMENT_VARIABLE)
    if value is None or not value.strip():
        raise TestDatabaseConfigurationError(
            "TEST_DATABASE_URL is required when PostgreSQL tests are selected"
        )
    parse_test_database_url(value)
    return value


def psycopg_connection_info(database_url: str) -> str:
    """Convert the canonical SQLAlchemy URL to a Psycopg connection URI."""
    parsed = parse_test_database_url(database_url)
    return parsed.set(drivername="postgresql").render_as_string(hide_password=False)
