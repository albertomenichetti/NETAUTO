"""Transport-neutral shared health vocabulary."""

from enum import StrEnum


class HealthStatus(StrEnum):
    OK = "ok"
    ERROR = "error"
