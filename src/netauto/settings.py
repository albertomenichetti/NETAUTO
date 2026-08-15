"""Process configuration loaded explicitly by the composition root."""

from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

LogLevel = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]


class Settings(BaseSettings):
    """Immutable process settings.

    Construction is deliberately explicit. Importing this module never reads process
    configuration or creates a settings singleton.
    """

    model_config = SettingsConfigDict(
        env_prefix="NETAUTO_",
        extra="forbid",
        frozen=True,
    )

    database_url: str = Field()
    log_level: LogLevel = "INFO"

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

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Use explicit values, environment, and mounted secrets; never dotenv."""
        del settings_cls, dotenv_settings
        return init_settings, env_settings, file_secret_settings
