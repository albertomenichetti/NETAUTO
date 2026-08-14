"""Tests for the explicit real-PostgreSQL test boundary."""

import psycopg
import pytest

from tests.support.postgresql import (
    TestDatabaseConfigurationError,
    load_test_database_url,
    psycopg_connection_info,
)

TEST_DATABASE_URL = "postgresql+psycopg://test@example/test_database"


def test_missing_test_database_url_is_refused() -> None:
    with pytest.raises(
        TestDatabaseConfigurationError,
        match="TEST_DATABASE_URL is required",
    ):
        load_test_database_url({})


@pytest.mark.parametrize(
    "database_url",
    [
        "sqlite:///test.db",
        "postgresql+psycopg2://test@example/test_database",
        "postgresql+asyncpg://test@example/test_database",
    ],
)
def test_non_postgresql_psycopg_target_is_refused(database_url: str) -> None:
    with pytest.raises(
        TestDatabaseConfigurationError,
        match=r"must use postgresql\+psycopg",
    ):
        load_test_database_url({"TEST_DATABASE_URL": database_url})


def test_test_database_boundary_reads_only_test_database_url() -> None:
    environment = {
        "NETAUTO_DATABASE_URL": "postgresql+psycopg://runtime@example/runtime",
        "TEST_DATABASE_URL": TEST_DATABASE_URL,
    }

    assert load_test_database_url(environment) == TEST_DATABASE_URL


@pytest.mark.postgresql
def test_real_postgresql_is_available(test_database_url: str) -> None:
    connection_info = psycopg_connection_info(test_database_url)
    with psycopg.connect(connection_info, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            assert cursor.fetchone() == (1,)
