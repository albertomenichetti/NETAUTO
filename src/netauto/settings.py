"""Process configuration loaded explicitly by the composition root."""

from __future__ import annotations

import math
import os
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_validator
from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

LogLevel = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]

_INTEGER_SOURCE_FIELDS = frozenset({"pool_size", "max_overflow", "pool_recycle"})


class SettingsBootstrapError(ValueError):
    """An explicitly selected settings source is not usable."""


def _parse_settings_source_value(field_name: str, value: object) -> object:
    """Parse only canonical environment/file scalar carriers.

    Constructor values remain subject to strict model validation; this parsing is
    applied only to the two string-based production settings sources.
    """
    if not isinstance(value, str):
        return value
    field_name = field_name.removeprefix("NETAUTO_").lower()
    if field_name in _INTEGER_SOURCE_FIELDS:
        if re.fullmatch(r"-?[0-9]+", value) is None:
            return value
        return int(value)
    if field_name == "pool_timeout":
        try:
            return float(value)
        except ValueError:
            return value
    if field_name == "pool_pre_ping":
        normalized = value.lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
    return value


class _ParsedScalarSettingsSource(PydanticBaseSettingsSource):
    """Delegate a source while parsing its canonical scalar string carriers."""

    def __init__(
        self,
        settings_cls: type[BaseSettings],
        source: PydanticBaseSettingsSource,
    ) -> None:
        super().__init__(settings_cls)
        self._source = source

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]:
        return self._source.get_field_value(field, field_name)

    def __call__(self) -> dict[str, Any]:
        values = self._source()
        return {
            key: _parse_settings_source_value(key, value)
            for key, value in values.items()
        }


class Settings(BaseSettings):
    """Exact immutable process settings.

    Importing this module never reads process configuration or creates a settings
    singleton. Environment and explicitly selected file sources are read only when
    one Settings value is constructed by the composition root.
    """

    model_config = SettingsConfigDict(
        env_prefix="NETAUTO_",
        case_sensitive=True,
        extra="forbid",
        frozen=True,
        populate_by_name=True,
    )

    database_url: str = Field(validation_alias="NETAUTO_DATABASE_URL")
    log_level: LogLevel = Field(default="INFO", validation_alias="NETAUTO_LOG_LEVEL")
    pool_size: int = Field(
        default=10, strict=True, ge=1, validation_alias="NETAUTO_POOL_SIZE"
    )
    max_overflow: int = Field(
        default=20,
        strict=True,
        ge=0,
        validation_alias="NETAUTO_MAX_OVERFLOW",
    )
    pool_timeout: float = Field(
        default=5.0,
        strict=True,
        gt=0,
        validation_alias="NETAUTO_POOL_TIMEOUT",
    )
    pool_recycle: int | None = Field(
        default=None,
        strict=True,
        gt=0,
        validation_alias="NETAUTO_POOL_RECYCLE",
    )
    pool_pre_ping: bool = Field(
        default=False, strict=True, validation_alias="NETAUTO_POOL_PRE_PING"
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        """Require the canonical SQLAlchemy Psycopg URL."""
        try:
            parsed = make_url(value)
        except ArgumentError as error:
            raise ValueError("database URL must be a valid SQLAlchemy URL") from error

        if parsed.drivername != "postgresql+psycopg":
            raise ValueError("database URL must use the postgresql+psycopg driver")
        return value

    @field_validator("pool_timeout")
    @classmethod
    def validate_pool_timeout(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("pool_timeout must be finite")
        return value

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Use init, direct environment and explicit secrets; never dotenv."""
        del dotenv_settings
        return (
            init_settings,
            _ParsedScalarSettingsSource(settings_cls, env_settings),
            _ParsedScalarSettingsSource(settings_cls, file_secret_settings),
        )


def load_settings() -> Settings:
    """Load one production Settings value with an explicit secret-dir selector."""
    selected = os.environ.get("NETAUTO_SECRETS_DIR")
    secrets_dir: Path | None = None
    if selected is not None:
        candidate = Path(selected)
        if not candidate.is_absolute():
            raise SettingsBootstrapError("NETAUTO_SECRETS_DIR must be absolute")
        if not candidate.exists():
            raise SettingsBootstrapError("NETAUTO_SECRETS_DIR does not exist")
        if not candidate.is_dir():
            raise SettingsBootstrapError("NETAUTO_SECRETS_DIR is not a directory")
        secrets_dir = candidate

    return Settings(_secrets_dir=secrets_dir)  # pyright: ignore[reportCallIssue]
