"""CLI-local exceptions."""

from dataclasses import dataclass


class CliError(Exception):
    """Base CLI error."""


@dataclass(slots=True)
class ApiError(CliError):
    """Server returned a valid NETAUTO error response."""

    status_code: int
    code: str
    message: str
    details: list[dict[str, object]]


class TransportError(CliError):
    """Network or timeout failure."""


class ProtocolError(CliError):
    """Server response is incompatible with the public contract."""


class InputError(CliError):
    """Local CLI input or configuration failure."""

