"""Central process logging configuration."""

import logging

from netauto.settings import LogLevel

_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def configure_logging(level: LogLevel) -> None:
    """Configure human-readable process logging through the standard library."""
    logging.basicConfig(level=level, format=_LOG_FORMAT)
