"""Permanent evidence for exact, explicit and isolated process configuration."""

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

import netauto.settings as settings_module
from netauto.settings import Settings, SettingsBootstrapError, load_settings
from tests.support.postgresql import (
    TestDatabaseConfigurationError,
    load_test_database_url,
)

RUNTIME_DATABASE_URL = "postgresql+psycopg://runtime@example/runtime"
SECRET_DATABASE_URL = "postgresql+psycopg://secret@example/secret"

CANONICAL_ENVIRONMENT = {
    "NETAUTO_DATABASE_URL",
    "NETAUTO_LOG_LEVEL",
    "NETAUTO_POOL_SIZE",
    "NETAUTO_MAX_OVERFLOW",
    "NETAUTO_POOL_TIMEOUT",
    "NETAUTO_POOL_RECYCLE",
    "NETAUTO_POOL_PRE_PING",
    "NETAUTO_SECRETS_DIR",
}


@pytest.fixture(autouse=True)
def isolated_runtime_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in CANONICAL_ENVIRONMENT:
        monkeypatch.delenv(name, raising=False)


def test_settings_are_not_instantiated_at_module_import() -> None:
    assert not any(
        isinstance(value, Settings) for value in vars(settings_module).values()
    )


def test_settings_exact_field_inventory_defaults_and_immutability() -> None:
    settings = Settings(database_url=RUNTIME_DATABASE_URL)

    assert tuple(Settings.model_fields) == (
        "database_url",
        "log_level",
        "pool_size",
        "max_overflow",
        "pool_timeout",
        "pool_recycle",
        "pool_pre_ping",
    )
    assert settings.model_dump() == {
        "database_url": RUNTIME_DATABASE_URL,
        "log_level": "INFO",
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 5.0,
        "pool_recycle": None,
        "pool_pre_ping": False,
    }
    with pytest.raises(ValidationError, match="frozen"):
        settings.pool_size = 11


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("pool_size", 0),
        ("pool_size", -1),
        ("pool_size", True),
        ("pool_size", 1.0),
        ("max_overflow", -1),
        ("max_overflow", True),
        ("max_overflow", 1.0),
        ("pool_timeout", 0.0),
        ("pool_timeout", -0.1),
        ("pool_timeout", float("nan")),
        ("pool_timeout", float("inf")),
        ("pool_timeout", float("-inf")),
        ("pool_timeout", True),
        ("pool_recycle", 0),
        ("pool_recycle", -1),
        ("pool_recycle", 1.5),
        ("pool_recycle", True),
        ("pool_pre_ping", 1),
        ("pool_pre_ping", "true"),
    ],
)
def test_settings_reject_every_invalid_pool_boundary(field: str, value: object) -> None:
    with pytest.raises(ValidationError, match=field):
        Settings(
            database_url=RUNTIME_DATABASE_URL,
            **{field: value},  # pyright: ignore[reportArgumentType]
        )


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://runtime@example/runtime",
        "postgresql+asyncpg://runtime@example/runtime",
        "sqlite+aiosqlite:///runtime.db",
        "not a URL",
    ],
)
def test_settings_require_exact_postgresql_psycopg_url(url: str) -> None:
    with pytest.raises(ValidationError, match="database_url"):
        Settings(database_url=url)


def test_canonical_environment_scalars_are_parsed_strictly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    environment = {
        "NETAUTO_DATABASE_URL": RUNTIME_DATABASE_URL,
        "NETAUTO_LOG_LEVEL": "DEBUG",
        "NETAUTO_POOL_SIZE": "3",
        "NETAUTO_MAX_OVERFLOW": "4",
        "NETAUTO_POOL_TIMEOUT": "2.5",
        "NETAUTO_POOL_RECYCLE": "60",
        "NETAUTO_POOL_PRE_PING": "true",
    }
    for name, value in environment.items():
        monkeypatch.setenv(name, value)

    settings = Settings()  # pyright: ignore[reportCallIssue]

    assert settings.model_dump() == {
        "database_url": RUNTIME_DATABASE_URL,
        "log_level": "DEBUG",
        "pool_size": 3,
        "max_overflow": 4,
        "pool_timeout": 2.5,
        "pool_recycle": 60,
        "pool_pre_ping": True,
    }


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("NETAUTO_POOL_SIZE", "true"),
        ("NETAUTO_MAX_OVERFLOW", "-1"),
        ("NETAUTO_POOL_TIMEOUT", "nan"),
        ("NETAUTO_POOL_RECYCLE", "1.5"),
        ("NETAUTO_POOL_PRE_PING", "1"),
    ],
)
def test_invalid_environment_scalars_remain_invalid(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv("NETAUTO_DATABASE_URL", RUNTIME_DATABASE_URL)
    monkeypatch.setenv(name, value)
    with pytest.raises(ValidationError):
        Settings()  # pyright: ignore[reportCallIssue]


def test_constructor_environment_secret_and_default_precedence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "NETAUTO_DATABASE_URL").write_text(f"{SECRET_DATABASE_URL}\n")
    (tmp_path / "NETAUTO_POOL_SIZE").write_text("2\n")
    monkeypatch.setenv("NETAUTO_SECRETS_DIR", str(tmp_path))
    monkeypatch.setenv("NETAUTO_DATABASE_URL", RUNTIME_DATABASE_URL)
    monkeypatch.setenv("NETAUTO_POOL_SIZE", "3")

    loaded = load_settings()
    explicit = Settings(
        database_url="postgresql+psycopg://explicit@example/explicit",
        pool_size=4,
        _secrets_dir=tmp_path,  # pyright: ignore[reportCallIssue]
    )

    assert loaded.database_url == RUNTIME_DATABASE_URL
    assert loaded.pool_size == 3
    assert loaded.max_overflow == 20
    assert explicit.database_url.endswith("/explicit")
    assert explicit.pool_size == 4


def test_explicit_secret_file_accepts_one_final_newline(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "NETAUTO_DATABASE_URL").write_text(f"{SECRET_DATABASE_URL}\n")
    monkeypatch.setenv("NETAUTO_SECRETS_DIR", str(tmp_path))

    assert load_settings().database_url == SECRET_DATABASE_URL


@pytest.mark.parametrize("kind", ["relative", "missing", "file"])
def test_invalid_explicit_secret_selector_fails_without_environment_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, kind: str
) -> None:
    monkeypatch.setenv("NETAUTO_DATABASE_URL", RUNTIME_DATABASE_URL)
    if kind == "relative":
        selected = "relative/secrets"
    elif kind == "missing":
        selected = str(tmp_path / "missing")
    else:
        selected_path = tmp_path / "not-a-directory"
        selected_path.write_text("x")
        selected = str(selected_path)
    monkeypatch.setenv("NETAUTO_SECRETS_DIR", selected)

    with pytest.raises(SettingsBootstrapError, match="NETAUTO_SECRETS_DIR"):
        load_settings()


def test_no_dotenv_or_implicit_secret_directory_discovery(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / ".env").write_text(f"NETAUTO_DATABASE_URL={SECRET_DATABASE_URL}\n")
    implicit = tmp_path / "secrets"
    implicit.mkdir()
    (implicit / "NETAUTO_DATABASE_URL").write_text(SECRET_DATABASE_URL)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValidationError, match="NETAUTO_DATABASE_URL"):
        load_settings()


def test_runtime_database_url_has_no_default() -> None:
    with pytest.raises(ValidationError, match="NETAUTO_DATABASE_URL"):
        Settings()  # pyright: ignore[reportCallIssue]


def test_runtime_and_test_database_configuration_are_independent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NETAUTO_DATABASE_URL", RUNTIME_DATABASE_URL)
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)

    settings = Settings()  # pyright: ignore[reportCallIssue]
    assert settings.database_url == RUNTIME_DATABASE_URL
    with pytest.raises(
        TestDatabaseConfigurationError,
        match="TEST_DATABASE_URL is required",
    ):
        load_test_database_url()


def test_bootstrap_selector_is_not_a_settings_field() -> None:
    with pytest.raises(ValidationError, match="extra_forbidden"):
        Settings(
            database_url=RUNTIME_DATABASE_URL,
            NETAUTO_SECRETS_DIR="/tmp",  # pyright: ignore[reportCallIssue]
        )


def test_settings_dump_never_adds_host_port_worker_or_profile_fields() -> None:
    dumped: dict[str, Any] = Settings(database_url=RUNTIME_DATABASE_URL).model_dump()
    assert not ({"host", "port", "workers", "profile", "secrets_dir"} & dumped.keys())
