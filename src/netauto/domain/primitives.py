"""Authoritative M1 PrimitiveType parsing and constraint semantics."""

import ipaddress
import json
import re
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import cast

type JsonScalar = str | int | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]
type CanonicalValue = str | int | bool


class PrimitiveType(StrEnum):
    STRING = "core.string"
    INTEGER = "core.integer"
    NUMBER = "core.number"
    BOOLEAN = "core.boolean"
    DATE = "core.date"
    DATETIME = "core.datetime"
    IP = "core.ip"
    IP_PREFIX = "core.ip_prefix"
    BYTE_SIZE = "core.byte_size"


class PrimitiveValidationError(ValueError):
    """A value or constraint candidate violates frozen primitive semantics."""

    def __init__(self, path: str, rule: str) -> None:
        self.path = path
        self.rule = rule
        super().__init__(f"{path}: {rule}")


_DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z")
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
_DATETIME = re.compile(
    r"(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})T"
    r"(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})"
    r"(?:\.(?P<fraction>[0-9]+))?"
    r"(?P<offset>Z|[+-][0-9]{2}:[0-9]{2})\Z"
)
_BYTE_SIZE = re.compile(
    r"(?P<quantity>(?:0|[1-9][0-9]*)(?:\.[0-9]+)?)(?: ?)(?P<unit>"
    r"B|kB|MB|GB|TB|PB|EB|KiB|MiB|GiB|TiB|PiB|EiB)\Z"
)
_UNITS = {
    "B": 1,
    "kB": 1000,
    "MB": 1000**2,
    "GB": 1000**3,
    "TB": 1000**4,
    "PB": 1000**5,
    "EB": 1000**6,
    "KiB": 1024,
    "MiB": 1024**2,
    "GiB": 1024**3,
    "TiB": 1024**4,
    "PiB": 1024**5,
    "EiB": 1024**6,
}
_ALLOWED_CONSTRAINTS = {
    PrimitiveType.STRING: ("min_length", "max_length", "pattern", "enum"),
    PrimitiveType.INTEGER: ("minimum", "maximum", "enum"),
    PrimitiveType.NUMBER: ("minimum", "maximum", "enum"),
    PrimitiveType.BOOLEAN: ("enum",),
    PrimitiveType.DATE: ("minimum", "maximum", "enum"),
    PrimitiveType.DATETIME: ("minimum", "maximum", "enum"),
    PrimitiveType.IP: ("ip_version", "enum"),
    PrimitiveType.IP_PREFIX: ("ip_version", "enum"),
    PrimitiveType.BYTE_SIZE: ("minimum", "maximum", "enum"),
}


def parse_primitive_type(value: str) -> PrimitiveType:
    try:
        return PrimitiveType(value)
    except ValueError as error:
        raise PrimitiveValidationError("base_type", "unsupported_primitive") from error


def _canonical_decimal(value: object, path: str) -> str:
    if not isinstance(value, str) or _DECIMAL.fullmatch(value) is None:
        raise PrimitiveValidationError(path, "invalid_number")
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise PrimitiveValidationError(path, "invalid_number") from error
    if not number.is_finite():
        raise PrimitiveValidationError(path, "invalid_number")
    if number == 0:
        return "0"
    rendered = format(number, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered


def _canonical_date(value: object, path: str) -> str:
    if not isinstance(value, str) or _DATE.fullmatch(value) is None:
        raise PrimitiveValidationError(path, "invalid_date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise PrimitiveValidationError(path, "invalid_date") from error
    if parsed.isoformat() != value:
        raise PrimitiveValidationError(path, "invalid_date")
    return value


def _canonical_datetime(value: object, path: str) -> str:
    if not isinstance(value, str):
        raise PrimitiveValidationError(path, "invalid_datetime")
    match = _DATETIME.fullmatch(value)
    if match is None:
        raise PrimitiveValidationError(path, "invalid_datetime")
    fraction = match.group("fraction") or ""
    if len(fraction) > 6 and any(digit != "0" for digit in fraction[6:]):
        raise PrimitiveValidationError(path, "datetime_precision")
    microsecond = int((fraction[:6] + "000000")[:6])
    offset_text = match.group("offset")
    if offset_text == "Z":
        zone = UTC
    else:
        sign = 1 if offset_text[0] == "+" else -1
        offset_hour = int(offset_text[1:3])
        offset_minute = int(offset_text[4:6])
        if offset_hour > 23 or offset_minute > 59:
            raise PrimitiveValidationError(path, "invalid_datetime")
        zone = timezone(sign * timedelta(hours=offset_hour, minutes=offset_minute))
    try:
        parsed_date = date.fromisoformat(match.group("date"))
        parsed = datetime(
            parsed_date.year,
            parsed_date.month,
            parsed_date.day,
            int(match.group("hour")),
            int(match.group("minute")),
            int(match.group("second")),
            microsecond,
            zone,
        ).astimezone(UTC)
    except ValueError as error:
        raise PrimitiveValidationError(path, "invalid_datetime") from error
    rendered = (
        f"{parsed.year:04d}-{parsed.month:02d}-{parsed.day:02d}T"
        f"{parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d}"
    )
    if parsed.microsecond:
        rendered += f".{parsed.microsecond:06d}".rstrip("0")
    return rendered + "Z"


def _canonical_ip(value: object, path: str) -> str:
    if not isinstance(value, str) or "/" in value or "%" in value:
        raise PrimitiveValidationError(path, "invalid_ip")
    try:
        return str(ipaddress.ip_address(value))
    except ValueError as error:
        raise PrimitiveValidationError(path, "invalid_ip") from error


def _canonical_prefix(value: object, path: str) -> str:
    if not isinstance(value, str) or value.count("/") != 1 or "%" in value:
        raise PrimitiveValidationError(path, "invalid_ip_prefix")
    address, prefix = value.split("/", 1)
    if not prefix.isascii() or not prefix.isdecimal():
        raise PrimitiveValidationError(path, "invalid_ip_prefix")
    try:
        network = ipaddress.ip_network(value, strict=True)
        ipaddress.ip_address(address)
    except ValueError as error:
        raise PrimitiveValidationError(path, "invalid_ip_prefix") from error
    return str(network)


def _canonical_byte_size(value: object, path: str) -> int:
    if isinstance(value, bool):
        raise PrimitiveValidationError(path, "invalid_byte_size")
    if isinstance(value, int):
        if value < 0:
            raise PrimitiveValidationError(path, "invalid_byte_size")
        return value
    if not isinstance(value, str):
        raise PrimitiveValidationError(path, "invalid_byte_size")
    match = _BYTE_SIZE.fullmatch(value)
    if match is None:
        raise PrimitiveValidationError(path, "invalid_byte_size")
    quantity = Decimal(match.group("quantity"))
    sign, digits, exponent = quantity.as_tuple()
    if not isinstance(exponent, int):
        raise PrimitiveValidationError(path, "invalid_byte_size")
    coefficient = int("".join(str(digit) for digit in digits))
    if sign:
        coefficient = -coefficient
    scaled = coefficient * _UNITS[match.group("unit")]
    if exponent >= 0:
        return scaled * 10**exponent
    divisor = 10 ** (-exponent)
    byte_count, remainder = divmod(scaled, divisor)
    if remainder:
        raise PrimitiveValidationError(path, "inexact_byte_size")
    return byte_count


def canonicalize_value(
    primitive: PrimitiveType | str, value: object, path: str = "value"
) -> CanonicalValue:
    kind = parse_primitive_type(str(primitive))
    if kind is PrimitiveType.STRING:
        if not isinstance(value, str):
            raise PrimitiveValidationError(path, "invalid_string")
        return value
    if kind is PrimitiveType.INTEGER:
        if isinstance(value, bool) or not isinstance(value, int):
            raise PrimitiveValidationError(path, "invalid_integer")
        return value
    if kind is PrimitiveType.NUMBER:
        return _canonical_decimal(value, path)
    if kind is PrimitiveType.BOOLEAN:
        if not isinstance(value, bool):
            raise PrimitiveValidationError(path, "invalid_boolean")
        return value
    if kind is PrimitiveType.DATE:
        return _canonical_date(value, path)
    if kind is PrimitiveType.DATETIME:
        return _canonical_datetime(value, path)
    if kind is PrimitiveType.IP:
        return _canonical_ip(value, path)
    if kind is PrimitiveType.IP_PREFIX:
        return _canonical_prefix(value, path)
    return _canonical_byte_size(value, path)


def _ordered(value: JsonValue, path: str) -> CanonicalValue:
    if isinstance(value, (str, int, bool)):
        return value
    raise PrimitiveValidationError(path, "invalid_constraint")


def _compare(
    primitive: PrimitiveType, left: CanonicalValue, right: CanonicalValue
) -> int:
    if primitive is PrimitiveType.NUMBER:
        left_value = Decimal(str(left))
        right_value = Decimal(str(right))
        return (left_value > right_value) - (left_value < right_value)
    if primitive is PrimitiveType.DATE:
        left_date = date.fromisoformat(str(left))
        right_date = date.fromisoformat(str(right))
        return (left_date > right_date) - (left_date < right_date)
    if primitive is PrimitiveType.DATETIME:
        left_datetime = datetime.fromisoformat(str(left).replace("Z", "+00:00"))
        right_datetime = datetime.fromisoformat(str(right).replace("Z", "+00:00"))
        return (left_datetime > right_datetime) - (left_datetime < right_datetime)
    if primitive in {PrimitiveType.INTEGER, PrimitiveType.BYTE_SIZE}:
        left_integer = int(left)
        right_integer = int(right)
        return (left_integer > right_integer) - (left_integer < right_integer)
    left_text = str(left)
    right_text = str(right)
    return (left_text > right_text) - (left_text < right_text)


def _validate_against_constraints(
    primitive: PrimitiveType,
    value: str | int | bool,
    constraints: dict[str, JsonValue],
    path: str,
) -> None:
    if (
        "minimum" in constraints
        and _compare(
            primitive, value, _ordered(constraints["minimum"], "constraints.minimum")
        )
        < 0
    ):
        raise PrimitiveValidationError(path, "minimum")
    if (
        "maximum" in constraints
        and _compare(
            primitive, value, _ordered(constraints["maximum"], "constraints.maximum")
        )
        > 0
    ):
        raise PrimitiveValidationError(path, "maximum")
    if isinstance(value, str):
        min_length = constraints.get("min_length")
        max_length = constraints.get("max_length")
        if isinstance(min_length, int) and len(value) < min_length:
            raise PrimitiveValidationError(path, "min_length")
        if isinstance(max_length, int) and len(value) > max_length:
            raise PrimitiveValidationError(path, "max_length")
        if (
            "pattern" in constraints
            and re.fullmatch(str(constraints["pattern"]), value) is None
        ):
            raise PrimitiveValidationError(path, "pattern")
    if "ip_version" in constraints:
        version = ipaddress.ip_network(str(value), strict=False).version
        if version != constraints["ip_version"]:
            raise PrimitiveValidationError(path, "ip_version")


def canonicalize_constraints(
    primitive: PrimitiveType | str, candidate: object
) -> dict[str, JsonValue]:
    kind = parse_primitive_type(str(primitive))
    if not isinstance(candidate, dict):
        raise PrimitiveValidationError("constraints", "invalid_constraints")
    raw_candidate = cast(dict[object, object], candidate)
    if not all(isinstance(key, str) for key in raw_candidate):
        raise PrimitiveValidationError("constraints", "invalid_constraints")
    values_by_key = cast(dict[str, object], raw_candidate)
    unknown = set(values_by_key) - set(_ALLOWED_CONSTRAINTS[kind])
    if unknown:
        raise PrimitiveValidationError(
            f"constraints.{sorted(unknown)[0]}", "unsupported_constraint"
        )

    canonical: dict[str, JsonValue] = {}
    for key in _ALLOWED_CONSTRAINTS[kind]:
        if key not in values_by_key or key == "enum":
            continue
        value = values_by_key[key]
        path = f"constraints.{key}"
        if key in {"min_length", "max_length"}:
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise PrimitiveValidationError(path, "invalid_length")
            canonical[key] = value
        elif key == "pattern":
            if not isinstance(value, str):
                raise PrimitiveValidationError(path, "invalid_pattern")
            try:
                re.compile(value)
            except re.error as error:
                raise PrimitiveValidationError(path, "invalid_pattern") from error
            canonical[key] = value
        elif key == "ip_version":
            if isinstance(value, bool) or value not in (4, 6):
                raise PrimitiveValidationError(path, "invalid_ip_version")
            canonical[key] = value
        else:
            canonical[key] = canonicalize_value(kind, value, path)

    minimum = canonical.get("minimum")
    maximum = canonical.get("maximum")
    if (
        minimum is not None
        and maximum is not None
        and _compare(
            kind,
            _ordered(minimum, "constraints.minimum"),
            _ordered(maximum, "constraints.maximum"),
        )
        > 0
    ):
        raise PrimitiveValidationError("constraints", "minimum_gt_maximum")
    min_length = canonical.get("min_length")
    max_length = canonical.get("max_length")
    if isinstance(min_length, int) and isinstance(max_length, int):
        if min_length > max_length:
            raise PrimitiveValidationError("constraints", "min_length_gt_max_length")

    if "enum" in values_by_key:
        raw_enum = values_by_key["enum"]
        if not isinstance(raw_enum, list):
            raise PrimitiveValidationError("constraints.enum", "invalid_enum")
        raw_values = cast(list[object], raw_enum)
        values: list[JsonValue] = []
        seen: set[str] = set()
        for index, raw in enumerate(raw_values):
            path = f"constraints.enum.{index}"
            value = canonicalize_value(kind, raw, path)
            identity = json.dumps(value, sort_keys=True, separators=(",", ":"))
            if identity in seen:
                raise PrimitiveValidationError(path, "duplicate_enum_member")
            _validate_against_constraints(kind, value, canonical, path)
            seen.add(identity)
            values.append(value)
        values.sort(key=lambda item: json.dumps(item, separators=(",", ":")))
        canonical["enum"] = values
    return canonical


def validate_value(
    primitive: PrimitiveType | str,
    value: object,
    constraints: dict[str, JsonValue],
    path: str = "value",
) -> CanonicalValue:
    kind = parse_primitive_type(str(primitive))
    canonical_value = canonicalize_value(kind, value, path)
    _validate_against_constraints(kind, canonical_value, constraints, path)
    enum = constraints.get("enum")
    if isinstance(enum, list) and canonical_value not in enum:
        raise PrimitiveValidationError(path, "enum")
    return canonical_value
