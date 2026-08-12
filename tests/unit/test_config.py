import os

from sqlalchemy.engine import make_url

from netauto.config import DEFAULT_DATABASE_URL, get_database_url


def test_get_database_url_returns_default_when_env_is_absent(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert get_database_url() == DEFAULT_DATABASE_URL


def test_get_database_url_returns_env_override(monkeypatch) -> None:
    configured = "postgresql+psycopg://user:secret@localhost/netauto"
    monkeypatch.setenv("DATABASE_URL", configured)

    assert get_database_url() == configured
    assert os.environ["DATABASE_URL"] == configured


def test_default_database_url_is_postgresql_psycopg() -> None:
    url = make_url(DEFAULT_DATABASE_URL)

    assert url.get_backend_name() == "postgresql"
    assert url.get_driver_name() == "psycopg"
