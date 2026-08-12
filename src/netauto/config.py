"""Minimal runtime configuration helpers."""

from __future__ import annotations

import os

DEFAULT_DATABASE_URL = "sqlite:///netauto.sqlite3"


def get_database_url() -> str:
    """Return the configured database URL or the current SQLite default."""

    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
