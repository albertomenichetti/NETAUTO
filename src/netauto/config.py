"""Minimal runtime configuration helpers."""

from __future__ import annotations

import os

DEFAULT_DATABASE_URL = "postgresql+psycopg://localhost/netauto"


def get_database_url() -> str:
    """Return the configured database URL or the default PostgreSQL runtime URL."""

    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
