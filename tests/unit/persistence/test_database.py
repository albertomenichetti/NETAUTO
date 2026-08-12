from unittest.mock import Mock

import pytest

from netauto.persistence.sqlalchemy.database import create_database_engine


def test_create_database_engine_builds_lazy_psycopg_postgresql_engine() -> None:
    engine = create_database_engine("postgresql+psycopg://user:password@localhost/netauto")
    try:
        assert engine.dialect.name == "postgresql"
        assert engine.dialect.driver == "psycopg"
    finally:
        engine.dispose()


def test_create_database_engine_calls_sqlalchemy_create_engine_for_supported_postgresql(
    monkeypatch,
) -> None:
    create_engine_mock = Mock()
    engine = Mock()
    create_engine_mock.return_value = engine
    monkeypatch.setattr("netauto.persistence.sqlalchemy.database.create_engine", create_engine_mock)

    result = create_database_engine("postgresql+psycopg://user:password@localhost/netauto")

    assert result is engine
    create_engine_mock.assert_called_once_with(
        "postgresql+psycopg://user:password@localhost/netauto"
    )


@pytest.mark.parametrize(
    "database_url",
    [
        "sqlite:///netauto.db",
        "mysql://user:password@localhost/netauto",
        "postgresql+psycopg2://user:password@localhost/netauto",
        "postgresql+asyncpg://user:password@localhost/netauto",
    ],
)
def test_create_database_engine_rejects_unsupported_runtime_urls(database_url: str) -> None:
    with pytest.raises(RuntimeError, match="DATABASE_URL must use postgresql\\+psycopg\\."):
        create_database_engine(database_url)
