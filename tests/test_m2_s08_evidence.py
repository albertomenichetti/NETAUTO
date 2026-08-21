"""M2-S08 tests for the future S09 final-evidence record schema."""

from dataclasses import replace
from pathlib import Path

import pytest

from tests.support.m2_evidence import (
    EVIDENCE_STATES,
    REVIEWER_DECISIONS,
    ArtifactEvidence,
    CommandEvidence,
    EnvironmentEvidence,
    EvidenceExpectations,
    EvidenceValidationError,
    FinalEvidenceRecord,
    OperationCensus,
    RuntimeCensus,
    RuntimeLockEvidence,
    SchemaEvidence,
    stable_evidence_json,
    validate_evidence_record,
)
from tests.support.m2_evidence import TestCensus as EvidenceTestCensus
from tests.support.s09_acceptance import (
    s09_state,
    validate_s09_lifecycle,
)
from tests.test_m2_traceability import (
    M2_CONCURRENCY_SCENARIOS,
    M2_EVIDENCE_BUNDLES,
    M2_PREDICATE_TO_SCENARIOS,
)

ROOT = Path(__file__).parents[1]
EXPECTATIONS = EvidenceExpectations(
    bundles=M2_EVIDENCE_BUNDLES,
    scenarios=M2_CONCURRENCY_SCENARIOS,
    predicates=frozenset(M2_PREDICATE_TO_SCENARIOS),
)


def _record() -> FinalEvidenceRecord:
    return FinalEvidenceRecord(
        schema_version=1,
        candidate_commit="a" * 40,
        branch="M2",
        release_version="0.2.0",
        wheel=ArtifactEvidence(
            path="dist/netauto-0.2.0-py3-none-any.whl",
            byte_size=123_456,
            member_count=47,
            sha256="b" * 64,
        ),
        runtime_lock=RuntimeLockEvidence(
            path="src/netauto/release/runtime.pylock.toml",
            byte_size=54_321,
            package_count=29,
            sha256="c" * 64,
        ),
        environment=EnvironmentEvidence(
            python="CPython 3.14.0",
            uv="0.8.12",
            hatchling="1.27.0",
            postgresql="18.0",
            linux="Linux 6.12 x86_64",
        ),
        locked_environment_confirmed=True,
        build_confirmed=True,
        commands=(
            CommandEvidence(
                argv=("uv", "run", "pytest", "-q"),
                exit_status=0,
                duration_seconds=12.5,
                census=EvidenceTestCensus(4, 4, 0, 0, 0, 0),
            ),
        ),
        evidence_bundles={item: "PASS" for item in M2_EVIDENCE_BUNDLES},
        scenarios={item: "PASS" for item in M2_CONCURRENCY_SCENARIOS},
        predicates={item: "PASS" for item in M2_PREDICATE_TO_SCENARIOS},
        schema=SchemaEvidence(
            table_count=15,
            alembic_bases=("0001_m2_kernel",),
            alembic_heads=("0001_m2_kernel",),
            database_revisions=("0001_m2_kernel",),
            compare_metadata=(),
        ),
        operations=OperationCensus(63, 1, 63, 8, 65),
        installed_t9="PASS",
        runtime_census=RuntimeCensus(0, 0, 0, 0, 0, 0),
        open_findings=(),
    )


def _accepted_gate_counterexamples() -> tuple[tuple[str, FinalEvidenceRecord], ...]:
    record = _record()
    bundle = min(record.evidence_bundles)
    scenario = min(record.scenarios)
    predicate = min(record.predicates)
    return (
        (
            "evidence-bundle-fail",
            replace(
                record,
                evidence_bundles=record.evidence_bundles | {bundle: "FAIL"},
            ),
        ),
        (
            "scenario-blocked",
            replace(record, scenarios=record.scenarios | {scenario: "BLOCKED"}),
        ),
        (
            "predicate-fail",
            replace(record, predicates=record.predicates | {predicate: "FAIL"}),
        ),
        ("installed-t9-blocked", replace(record, installed_t9="BLOCKED")),
        (
            "command-exit-one",
            replace(
                record,
                commands=(replace(record.commands[0], exit_status=1),),
            ),
        ),
        ("open-finding", replace(record, open_findings=("S08-VRF-07",))),
        (
            "runtime-skipped",
            replace(record, runtime_census=replace(record.runtime_census, skipped=1)),
        ),
        (
            "runtime-xfailed",
            replace(record, runtime_census=replace(record.runtime_census, xfailed=1)),
        ),
        (
            "runtime-rerun",
            replace(record, runtime_census=replace(record.runtime_census, rerun=1)),
        ),
        (
            "supported-40p01",
            replace(
                record,
                runtime_census=replace(record.runtime_census, supported_40p01=1),
            ),
        ),
        (
            "unexpected-40001",
            replace(
                record,
                runtime_census=replace(record.runtime_census, unexpected_40001=1),
            ),
        ),
    )


def test_evidence_schema_accepts_one_complete_stable_record() -> None:
    record = _record()
    validate_evidence_record(record, EXPECTATIONS)
    first = stable_evidence_json(record)
    second = stable_evidence_json(record)
    assert first == second
    assert first.endswith("\n")
    assert first.index('"branch"') < first.index('"build_confirmed"')
    assert set(EVIDENCE_STATES) == {
        "DESIGNED",
        "IMPLEMENTED",
        "PASS",
        "FAIL",
        "BLOCKED",
    }


def test_evidence_schema_accepts_finite_reviewer_phase_decisions() -> None:
    assert set(REVIEWER_DECISIONS) == {"ACCEPTED", "REVIEW CHANGES REQUIRED"}
    for decision in REVIEWER_DECISIONS:
        record = replace(_record(), reviewer_decision=decision)
        validate_evidence_record(record, EXPECTATIONS, phase="reviewer")
        assert f'"reviewer_decision":"{decision}"' in stable_evidence_json(record)


def test_reviewer_accepted_requires_complete_all_pass_evidence() -> None:
    accepted = replace(_record(), reviewer_decision="ACCEPTED")
    validate_evidence_record(accepted, EXPECTATIONS, phase="reviewer")
    assert accepted.runtime_census.warnings == 0


@pytest.mark.parametrize(
    ("case", "record"),
    _accepted_gate_counterexamples(),
    ids=[case for case, _ in _accepted_gate_counterexamples()],
)
def test_reviewer_accepted_rejects_nonconforming_gate_but_changes_required_allows_it(
    case: str, record: FinalEvidenceRecord
) -> None:
    with pytest.raises(EvidenceValidationError, match="reviewer ACCEPTED"):
        validate_evidence_record(
            replace(record, reviewer_decision="ACCEPTED"),
            EXPECTATIONS,
            phase="reviewer",
        )
    validate_evidence_record(
        replace(record, reviewer_decision="REVIEW CHANGES REQUIRED"),
        EXPECTATIONS,
        phase="reviewer",
    )
    assert case


def test_evidence_schema_allows_http_endpoints_without_userinfo() -> None:
    record = replace(
        _record(),
        commands=(
            replace(
                _record().commands[0],
                argv=(
                    "netauto",
                    "-n",
                    "https://api.example.test/netauto",
                    "datatype",
                    "list",
                    "callback=http://127.0.0.1:8080/ready",
                ),
            ),
        ),
    )
    validate_evidence_record(record, EXPECTATIONS)


@pytest.mark.parametrize(
    "invalid",
    [
        replace(_record(), candidate_commit="not-a-sha"),
        replace(_record(), wheel=replace(_record().wheel, sha256="f" * 63)),
        replace(
            _record(),
            evidence_bundles={
                key: value
                for key, value in _record().evidence_bundles.items()
                if key != "M2-VER-32"
            },
        ),
        replace(
            _record(),
            scenarios=_record().scenarios | {"ROW-99": "PASS"},
        ),
        replace(
            _record(),
            commands=(replace(_record().commands[0], duration_seconds=-0.01),),
        ),
    ],
)
def test_evidence_schema_rejects_identifier_shape_and_count_drift(
    invalid: FinalEvidenceRecord,
) -> None:
    with pytest.raises(EvidenceValidationError):
        validate_evidence_record(invalid, EXPECTATIONS)


def test_evidence_schema_rejects_secrets_and_implementer_review_decision() -> None:
    unsafe_values = (
        "postgresql+psycopg://example.test/netauto",
        "host=db.example.test dbname=netauto user=operator",
        "https://operator@example.test/netauto",
        "https://operator:password@example.test/netauto",
        "secret=sentinel",
        "Authorization: Bearer sentinel",
    )
    for unsafe_value in unsafe_values:
        unsafe = replace(
            _record(),
            commands=(
                replace(
                    _record().commands[0],
                    argv=("tool", unsafe_value),
                ),
            ),
        )
        with pytest.raises(EvidenceValidationError):
            validate_evidence_record(unsafe, EXPECTATIONS)

    reviewer_owned = replace(_record(), reviewer_decision="ACCEPTED")
    with pytest.raises(EvidenceValidationError, match="reviewer-owned"):
        validate_evidence_record(reviewer_owned, EXPECTATIONS)

    with pytest.raises(EvidenceValidationError, match="requires one finite"):
        validate_evidence_record(_record(), EXPECTATIONS, phase="reviewer")

    invalid_decision = replace(_record(), reviewer_decision="DELIVERED")
    with pytest.raises(EvidenceValidationError, match="requires one finite"):
        validate_evidence_record(invalid_decision, EXPECTATIONS, phase="reviewer")


def test_evidence_documentation_matches_validator_and_reserves_s09_record() -> None:
    readme = ROOT / "docs/milestones/M2/evidence/README.md"
    assert readme.is_file()
    text = readme.read_text()
    normalized_text = " ".join(text.split())
    for required in (
        "non-normative evidence-format guidance",
        "M2-S09",
        "candidate_commit",
        "runtime_lock",
        "evidence_bundles",
        "scenarios",
        "predicates",
        "compare_metadata",
        "reviewer_decision",
        "DESIGNED",
        "IMPLEMENTED",
        "PASS",
        "FAIL",
        "BLOCKED",
        "reviewer-owned `REVIEW CHANGES REQUIRED`",
        "replacement cycle starts from `IN PROGRESS`",
        "Git history preserves the rejection",
        "future candidate uses a new commit SHA",
    ):
        assert required in normalized_text
    assert "S08 does not create or populate" in text
    state = s09_state((ROOT / "docs/milestones/M2/status.md").read_text())
    record = validate_s09_lifecycle(ROOT, state, EXPECTATIONS)
    if state in {"READY", "IN PROGRESS"}:
        assert record is None
        return

    assert record is not None
    if state == "CANDIDATE READY FOR REVIEW":
        assert record.reviewer_decision is None
    elif state == "REVIEW CHANGES REQUIRED":
        assert record.reviewer_decision == "REVIEW CHANGES REQUIRED"
    else:
        assert state == "COMPLETED"
        assert record.reviewer_decision == "ACCEPTED"
