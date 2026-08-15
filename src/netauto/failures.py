"""Transport-neutral application failure contract."""

from enum import StrEnum

from netauto.domain.primitives import JsonValue


class FailureClass(StrEnum):
    INVALID_REQUEST = "INVALID_REQUEST"
    NOT_FOUND = "NOT_FOUND"
    SEMANTIC_VALIDATION = "SEMANTIC_VALIDATION"
    STATE_CONFLICT = "STATE_CONFLICT"
    INTERNAL_FAILURE = "INTERNAL_FAILURE"


class ApplicationFailure(Exception):
    """Stable failure passed from application operations to adapters."""

    def __init__(
        self,
        failure_class: FailureClass,
        code: str,
        message: str,
        details: dict[str, JsonValue] | None = None,
    ) -> None:
        self.failure_class = failure_class
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)
