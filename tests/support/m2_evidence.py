"""Test-only validator for the future M2 final-acceptance evidence record."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Literal, cast
from urllib.parse import urlsplit

type EvidenceState = Literal["DESIGNED", "IMPLEMENTED", "PASS", "FAIL", "BLOCKED"]
type EvidencePhase = Literal["implementer", "reviewer"]
type ReviewerDecision = Literal["ACCEPTED", "REVIEW CHANGES REQUIRED"]

EVIDENCE_STATES = frozenset({"DESIGNED", "IMPLEMENTED", "PASS", "FAIL", "BLOCKED"})
REVIEWER_DECISIONS = frozenset({"ACCEPTED", "REVIEW CHANGES REQUIRED"})
_HEX_40 = re.compile(r"^[0-9a-f]{40}$")
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_URL = re.compile(r"[a-z][a-z0-9+.-]*://[^\s\"'<>]+", re.IGNORECASE)
_DSN_OR_SECRET_ASSIGNMENT = re.compile(
    r"(?:^|\s)(?:database_url|dbname|dsn|host|password|passwd|private_key|"
    r"secret|token|user|username)\s*[:=]",
    re.IGNORECASE,
)
_FORBIDDEN_KEY_PARTS = frozenset(
    {"credential", "database_url", "dsn", "password", "private_key", "secret", "token"}
)
_FORBIDDEN_VALUE_PARTS = (
    "authorization:",
    "bearer ",
    "credential=",
    "jdbc:postgresql:",
)


class EvidenceValidationError(ValueError):
    """The candidate evidence record is incomplete, unsafe or out of contract."""


@dataclass(frozen=True, slots=True)
class EvidenceExpectations:
    bundles: frozenset[str]
    scenarios: frozenset[str]
    predicates: frozenset[str]


@dataclass(frozen=True, slots=True)
class ArtifactEvidence:
    path: str
    byte_size: int
    member_count: int
    sha256: str


@dataclass(frozen=True, slots=True)
class RuntimeLockEvidence:
    path: str
    byte_size: int
    package_count: int
    sha256: str


@dataclass(frozen=True, slots=True)
class EnvironmentEvidence:
    python: str
    uv: str
    hatchling: str
    postgresql: str
    linux: str


@dataclass(frozen=True, slots=True)
class TestCensus:
    selected: int
    passed: int
    skipped: int
    xfailed: int
    rerun: int
    warnings: int


@dataclass(frozen=True, slots=True)
class CommandEvidence:
    argv: tuple[str, ...]
    exit_status: int
    duration_seconds: float
    census: TestCensus


@dataclass(frozen=True, slots=True)
class SchemaEvidence:
    table_count: int
    alembic_bases: tuple[str, ...]
    alembic_heads: tuple[str, ...]
    database_revisions: tuple[str, ...]
    compare_metadata: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OperationCensus:
    business_http: int
    health_http: int
    cli_remote: int
    cli_local: int
    cli_examples: int


@dataclass(frozen=True, slots=True)
class RuntimeCensus:
    skipped: int
    xfailed: int
    rerun: int
    warnings: int
    supported_40p01: int
    unexpected_40001: int


@dataclass(frozen=True, slots=True)
class FinalEvidenceRecord:
    schema_version: int
    candidate_commit: str
    branch: str
    release_version: str
    wheel: ArtifactEvidence
    runtime_lock: RuntimeLockEvidence
    environment: EnvironmentEvidence
    locked_environment_confirmed: bool
    build_confirmed: bool
    commands: tuple[CommandEvidence, ...]
    evidence_bundles: dict[str, EvidenceState]
    scenarios: dict[str, EvidenceState]
    predicates: dict[str, EvidenceState]
    schema: SchemaEvidence
    operations: OperationCensus
    installed_t9: EvidenceState
    runtime_census: RuntimeCensus
    open_findings: tuple[str, ...]
    reviewer_decision: ReviewerDecision | None = None


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceValidationError(message)


def _validate_nonnegative(value: int | float, name: str) -> None:
    _require(not isinstance(value, bool) and value >= 0, f"{name} must be non-negative")


def _validate_census(census: TestCensus, name: str) -> None:
    for field_name in (
        "selected",
        "passed",
        "skipped",
        "xfailed",
        "rerun",
        "warnings",
    ):
        _validate_nonnegative(getattr(census, field_name), f"{name}.{field_name}")
    _require(census.passed <= census.selected, f"{name}.passed exceeds selected")


def _validate_secret_free(value: object, path: str = "record") -> None:
    if isinstance(value, Mapping):
        mapping = cast(Mapping[object, object], value)
        for key, item in mapping.items():
            normalized = str(key).lower()
            _require(
                not any(part in normalized for part in _FORBIDDEN_KEY_PARTS),
                f"forbidden evidence field at {path}.{key}",
            )
            _validate_secret_free(item, f"{path}.{key}")
        return
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        sequence = cast(Sequence[object], value)
        for index, item in enumerate(sequence):
            _validate_secret_free(item, f"{path}[{index}]")
        return
    if isinstance(value, str):
        lowered = value.lower()
        _require(
            not any(part in lowered for part in _FORBIDDEN_VALUE_PARTS),
            f"secret-bearing value at {path}",
        )
        _require(
            _DSN_OR_SECRET_ASSIGNMENT.search(value) is None,
            f"database DSN or secret-bearing value at {path}",
        )
        for match in _URL.finditer(value):
            raw_url = match.group(0).rstrip(").,;]}")
            parsed = urlsplit(raw_url)
            _require(
                parsed.scheme.lower() in {"http", "https"},
                f"database or unsupported URL at {path}",
            )
            _require(
                parsed.hostname is not None,
                f"invalid HTTP endpoint at {path}",
            )
            _require(
                parsed.username is None and parsed.password is None,
                f"URL userinfo is forbidden at {path}",
            )


def validate_evidence_record(
    record: FinalEvidenceRecord,
    expectations: EvidenceExpectations,
    *,
    phase: EvidencePhase = "implementer",
) -> None:
    """Validate exact ledgers, safe values and reviewer ownership."""
    _require(record.schema_version == 1, "unsupported evidence schema version")
    _require(bool(_HEX_40.fullmatch(record.candidate_commit)), "invalid candidate SHA")
    _require(record.branch == "M2", "candidate branch must be M2")
    _require(bool(record.release_version), "release version is required")
    _require(record.wheel.path.endswith(".whl"), "wheel path must identify a wheel")
    _require(bool(_HEX_64.fullmatch(record.wheel.sha256)), "invalid wheel SHA-256")
    _require(
        bool(_HEX_64.fullmatch(record.runtime_lock.sha256)),
        "invalid runtime-lock SHA-256",
    )
    for name, value in (
        ("wheel.byte_size", record.wheel.byte_size),
        ("wheel.member_count", record.wheel.member_count),
        ("runtime_lock.byte_size", record.runtime_lock.byte_size),
        ("runtime_lock.package_count", record.runtime_lock.package_count),
    ):
        _validate_nonnegative(value, name)
    _require(
        record.runtime_lock.path == "src/netauto/release/runtime.pylock.toml",
        "invalid lock path",
    )
    _require(
        all(asdict(record.environment).values()),
        "all environment versions are required",
    )
    _require(record.locked_environment_confirmed, "locked environment is unconfirmed")
    _require(record.build_confirmed, "build is unconfirmed")
    _require(bool(record.commands), "command ledger is empty")
    for index, command in enumerate(record.commands):
        _require(bool(command.argv), f"commands[{index}].argv is empty")
        _validate_nonnegative(command.exit_status, f"commands[{index}].exit_status")
        _validate_nonnegative(
            command.duration_seconds, f"commands[{index}].duration_seconds"
        )
        _validate_census(command.census, f"commands[{index}].census")

    for ledger_name, ledger, expected in (
        ("evidence_bundles", record.evidence_bundles, expectations.bundles),
        ("scenarios", record.scenarios, expectations.scenarios),
        ("predicates", record.predicates, expectations.predicates),
    ):
        _require(frozenset(ledger) == expected, f"{ledger_name} identifier drift")
        _require(
            all(state in EVIDENCE_STATES for state in ledger.values()),
            f"{ledger_name} contains an invalid state",
        )

    _validate_nonnegative(record.schema.table_count, "schema.table_count")
    _require(record.schema.table_count == 15, "schema table census drift")
    _require(
        record.schema.alembic_bases == ("0001_m2_kernel",),
        "Alembic base drift",
    )
    _require(
        record.schema.alembic_heads == ("0001_m2_kernel",),
        "Alembic head drift",
    )
    _require(
        record.schema.database_revisions == ("0001_m2_kernel",),
        "database revision drift",
    )
    _require(record.schema.compare_metadata == (), "metadata drift is not empty")
    _require(
        record.operations == OperationCensus(63, 1, 63, 8, 65),
        "public/CLI operation census drift",
    )
    _require(record.installed_t9 in EVIDENCE_STATES, "invalid T9 state")
    for field_name in (
        "skipped",
        "xfailed",
        "rerun",
        "warnings",
        "supported_40p01",
        "unexpected_40001",
    ):
        _validate_nonnegative(
            getattr(record.runtime_census, field_name),
            f"runtime_census.{field_name}",
        )
    _require(phase in {"implementer", "reviewer"}, "invalid evidence validation phase")
    if phase == "implementer":
        _require(
            record.reviewer_decision is None,
            "reviewer decision is reviewer-owned during implementer phase",
        )
    else:
        _require(
            record.reviewer_decision in REVIEWER_DECISIONS,
            "reviewer phase requires one finite reviewer decision",
        )
    _validate_secret_free(asdict(record))


def stable_evidence_json(record: FinalEvidenceRecord) -> str:
    """Return deterministic compact JSON suitable for a reviewed Git record."""
    return (
        json.dumps(
            asdict(record),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    )
