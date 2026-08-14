"""Project-wide pytest fixtures."""

import pytest

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
