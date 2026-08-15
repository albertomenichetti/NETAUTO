"""Small versioned route/filter-specific opaque keyset cursor codec."""

import base64
import json
from dataclasses import dataclass
from typing import cast

from netauto.domain.primitives import JsonValue
from netauto.failures import ApplicationFailure, FailureClass


@dataclass(frozen=True, slots=True)
class Page[T]:
    items: list[T]
    next_cursor: str | None


def encode_cursor(
    route: str, filters: dict[str, JsonValue], key: list[JsonValue]
) -> str:
    payload: dict[str, JsonValue] = {
        "v": 1,
        "route": route,
        "filters": filters,
        "key": key,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def decode_cursor(
    token: str, route: str, filters: dict[str, JsonValue]
) -> list[JsonValue]:
    try:
        padding = "=" * (-len(token) % 4)
        raw = base64.b64decode(token + padding, altchars=b"-_", validate=True)
        decoded = json.loads(raw)
    except (ValueError, UnicodeError, json.JSONDecodeError) as error:
        raise _invalid_cursor() from error
    if not isinstance(decoded, dict):
        raise _invalid_cursor()
    payload = cast(dict[object, object], decoded)
    if (
        payload.get("v") != 1
        or payload.get("route") != route
        or payload.get("filters") != filters
        or not isinstance(payload.get("key"), list)
    ):
        raise _invalid_cursor()
    return cast(list[JsonValue], payload["key"])


def _invalid_cursor() -> ApplicationFailure:
    return ApplicationFailure(
        FailureClass.INVALID_REQUEST,
        "invalid_cursor",
        "The cursor is malformed or incompatible with this query.",
    )
