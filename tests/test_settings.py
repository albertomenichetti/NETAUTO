"""Tests for explicit and isolated process configuration."""

import pytest
from pydantic import ValidationError

import netauto.settings as settings_module
from netauto.settings import Settings
from tests.support.postgresql import (
    TestDatabaseConfigurationError,
    load_test_database_url,
)

RUNTIME_DATABASE_URL = "postgresql+psycopg://runtime@example/runtime"


def test_settings_are_not_instantiated_at_module_import() -> None:
    assert not any(
        isinstance(value, Settings) for value in vars(settings_module).values()
    )


def test_settings_accept_explicit_test_injection() -> None:
    settings = Settings(database_url=RUNTIME_DATABASE_URL, log_level="DEBUG")

    assert settings.database_url == RUNTIME_DATABASE_URL
    assert settings.log_level == "DEBUG"


def test_runtime_database_url_has_no_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NETAUTO_DATABASE_URL", raising=False)

    with pytest.raises(ValidationError, match="database_url"):
        # The omitted argument deliberately exercises BaseSettings environment loading.
        Settings()  # pyright: ignore[reportCallIssue]


def test_runtime_and_test_database_configuration_are_independent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NETAUTO_DATABASE_URL", RUNTIME_DATABASE_URL)
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)

    # The omitted argument deliberately exercises BaseSettings environment loading.
    settings = Settings()  # pyright: ignore[reportCallIssue]
    assert settings.database_url == RUNTIME_DATABASE_URL
    with pytest.raises(
        TestDatabaseConfigurationError,
        match="TEST_DATABASE_URL is required",
    ):
        load_test_database_url()
