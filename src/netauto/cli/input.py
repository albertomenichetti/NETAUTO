"""CLI input parsing helpers."""

from __future__ import annotations

import json
import sys
from collections.abc import Iterable
from pathlib import Path

from netauto.cli.client import JSONObject, JSONValue
from netauto.cli.errors import InputError


def parse_constraint(spec: str) -> dict[str, JSONValue]:
    name, separator, raw_value = spec.partition("=")
    if separator == "":
        raise InputError("Constraint must use NAME=JSON_VALUE syntax.")
    if not name:
        raise InputError("Constraint name must not be empty.")
    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError as error:
        raise InputError("Constraint value must be valid JSON.") from error
    return {"name": name, "value": value}


def parse_constraints(values: Iterable[str]) -> list[dict[str, JSONValue]]:
    return [parse_constraint(value) for value in values]


def load_json_object(path: str) -> JSONObject:
    try:
        raw = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise InputError("Could not read JSON input.") from error

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise InputError("Input file must contain valid JSON.") from error

    if not isinstance(payload, dict):
        raise InputError("Input JSON must be an object.")
    return payload


def parse_json_object(value: str, *, kind: str) -> JSONObject:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as error:
        raise InputError(f"{kind} must be valid JSON.") from error

    if not isinstance(payload, dict):
        raise InputError(f"{kind} must be a JSON object.")
    return payload


def ensure_modes_are_exclusive(
    *,
    file: str | None,
    inline_values_present: bool,
) -> None:
    if file is not None and inline_values_present:
        raise InputError("File input and inline options are mutually exclusive.")
