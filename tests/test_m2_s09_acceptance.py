"""Permanent lifecycle, registry, collector, and real-record checks for M2-S09."""

from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

import tests.support.s09_acceptance as s09_acceptance
from tests.support.m2_evidence import (
    ArtifactEvidence,
    CommandEvidence,
    EnvironmentEvidence,
    EvidenceExpectations,
    EvidenceState,
    FinalEvidenceRecord,
    OperationCensus,
    ReviewerDecision,
    RuntimeCensus,
    RuntimeLockEvidence,
    SchemaEvidence,
    stable_evidence_json,
)
from tests.support.m2_evidence import TestCensus as EvidenceTestCensus
from tests.support.s09_acceptance import (
    S09_BUNDLE_TARGET_UNION,
    S09_BUNDLE_TARGETS,
    S09_CONTRACT_QUALITY_TARGET_UNION,
    S09_FINAL_GATE_TARGETS,
    S09_IDENTIFIER_CENSUS,
    S09_OPERATION_CENSUS,
    S09_PREDICATE_ASSERTION_TARGET,
    S09_PREDICATE_TARGET_UNION,
    S09_SCENARIO_RECIPES,
    S09_SCENARIO_TARGET_UNION,
    S09_SCENARIO_TARGETS,
    ParsedPytestRun,
    S09State,
    blocked_pytest_run,
    derive_acceptance_ledger,
    derive_ledger,
    derive_outcome_ledger,
    derive_predicate_ledger,
    gate_exit_status,
    gate_result,
    parse_pytest_junit,
    s09_state,
    target_is_collected,
    validate_evidence_lifecycle,
    validate_s09_lifecycle,
)
from tests.test_m2_traceability import (
    M2_ACCEPTANCE_CRITERIA,
    M2_CONCURRENCY_SCENARIOS,
    M2_CONTRACT_QUALITY_GATE_TO_TARGETS,
    M2_CONTRACT_QUALITY_GATES,
    M2_EVIDENCE_BUNDLES,
    M2_EVIDENCE_TO_TARGETS,
    M2_NEGATIVE_SURFACE_TO_TARGETS,
    M2_OUTCOMES,
    M2_PREDICATE_TO_SCENARIOS,
    collected_test_nodes,
)

ROOT = Path(__file__).parents[1]
STATUS = ROOT / "docs/milestones/M2/status.md"
EXPECTATIONS = EvidenceExpectations(
    bundles=M2_EVIDENCE_BUNDLES,
    scenarios=M2_CONCURRENCY_SCENARIOS,
    predicates=frozenset(M2_PREDICATE_TO_SCENARIOS),
)


def _complete_record() -> FinalEvidenceRecord:
    return FinalEvidenceRecord(
        schema_version=1,
        candidate_commit="a" * 40,
        branch="M2",
        release_version="0.2.0",
        wheel=ArtifactEvidence(
            path="dist/netauto-0.2.0-py3-none-any.whl",
            byte_size=165_978,
            member_count=77,
            sha256="b" * 64,
        ),
        runtime_lock=RuntimeLockEvidence(
            path="src/netauto/release/runtime.pylock.toml",
            byte_size=48_238,
            package_count=29,
            sha256="c" * 64,
        ),
        environment=EnvironmentEvidence(
            python="CPython 3.14.0",
            uv="0.8.12",
            hatchling="1.27.0",
            postgresql="18.0",
            linux="Linux x86_64",
        ),
        locked_environment_confirmed=True,
        build_confirmed=True,
        commands=(
            CommandEvidence(
                argv=("uv", "run", "pytest", "-q"),
                exit_status=0,
                duration_seconds=1.0,
                census=EvidenceTestCensus(1, 1, 0, 0, 0, 1),
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
        runtime_census=RuntimeCensus(0, 0, 0, 1, 0, 0),
        open_findings=(),
    )


_ACCEPTANCE_SUMMARIES = {
    "CANDIDATE READY FOR REVIEW": """# M2 Final Acceptance Candidate
Status: CANDIDATE READY FOR REVIEW
reviewer decision      PENDING / reviewer-owned
M2-S09 is not COMPLETED
M2 is not DELIVERED
""",
    "REVIEW CHANGES REQUIRED": """# M2 Final Acceptance Review
Status: REVIEW CHANGES REQUIRED
reviewer decision      REVIEW CHANGES REQUIRED
M2-S09                 REVIEW CHANGES REQUIRED
M2                     NOT DELIVERED
""",
    "COMPLETED": """# M2 Final Acceptance Review
Status: ACCEPTED
reviewer decision      ACCEPTED
M2-S09                 COMPLETED
M2                     NOT DELIVERED
""",
}


def _lifecycle_tree(
    root: Path,
    state: S09State,
    record: FinalEvidenceRecord | None = None,
    *,
    summary: str | None = None,
) -> None:
    evidence = root / "docs/milestones/M2/evidence"
    evidence.mkdir(parents=True)
    (evidence / "README.md").write_text("format\n")
    if state != "COMPLETED":
        aid = root / "docs" / "milestones" / "M2" / "wip" / "M2-S09-codex-prompt.md"
        aid.parent.mkdir(parents=True)
        aid.write_text("aid\n")
    if record is not None:
        (evidence / f"candidate-{record.candidate_commit}.json").write_text(
            stable_evidence_json(record)
        )
        acceptance = root / "docs/milestones/M2/acceptance.md"
        acceptance.write_text(summary or _ACCEPTANCE_SUMMARIES[state])


def _parsed_run(
    *,
    raw_status: int = 0,
    target_state: EvidenceState = "PASS",
    skipped: int = 0,
    xfailed: int = 0,
    rerun: int = 0,
    warnings: int = 0,
    output: str = "bounded diagnostic",
) -> ParsedPytestRun:
    return ParsedPytestRun(
        argv=("uv", "run", "pytest"),
        exit_status=raw_status,
        duration_seconds=0.1,
        census=EvidenceTestCensus(
            1, int(target_state == "PASS"), skipped, xfailed, rerun, warnings
        ),
        target_states={"tests/test_sample.py::test_case": target_state},
        output_tail=output,
    )


def test_s09_final_gate_registries_are_exact_derived_and_collected() -> None:
    assert S09_IDENTIFIER_CENSUS == {
        "outcomes": 16,
        "acceptance_criteria": 32,
        "evidence_bundles": 32,
        "scenarios": 83,
        "predicates": 21,
        "negative_surfaces": 131,
        "contract_quality_gates": 10,
    }
    assert S09_OPERATION_CENSUS == {
        "business_http": 63,
        "health_http": 1,
        "cli_remote": 63,
    }
    assert set(S09_BUNDLE_TARGETS) == M2_EVIDENCE_BUNDLES
    assert set(S09_SCENARIO_TARGETS) == M2_CONCURRENCY_SCENARIOS
    assert set(S09_SCENARIO_RECIPES) == M2_CONCURRENCY_SCENARIOS
    assert all(
        M2_EVIDENCE_TO_TARGETS[bundle].state == "IMPLEMENTED" and targets
        for bundle, targets in S09_BUNDLE_TARGETS.items()
    )
    assert all(S09_SCENARIO_TARGETS.values())
    assert all(
        recipe.primary and recipe.primary.startswith("REC-")
        for recipe in S09_SCENARIO_RECIPES.values()
    )
    assert S09_BUNDLE_TARGET_UNION == frozenset(
        target for targets in S09_BUNDLE_TARGETS.values() for target in targets
    )
    assert S09_SCENARIO_TARGET_UNION == frozenset(
        target for targets in S09_SCENARIO_TARGETS.values() for target in targets
    )
    assert S09_PREDICATE_ASSERTION_TARGET in S09_PREDICATE_TARGET_UNION
    assert set(M2_CONTRACT_QUALITY_GATE_TO_TARGETS) == M2_CONTRACT_QUALITY_GATES
    assert S09_CONTRACT_QUALITY_TARGET_UNION == frozenset(
        target
        for targets in M2_CONTRACT_QUALITY_GATE_TO_TARGETS.values()
        for target in targets
    )
    assert S09_FINAL_GATE_TARGETS["negative_surface"] == frozenset(
        target
        for targets in M2_NEGATIVE_SURFACE_TO_TARGETS.values()
        for target in targets
    )
    collected = collected_test_nodes()
    for targets in S09_FINAL_GATE_TARGETS.values():
        assert targets
        for target in targets:
            assert target_is_collected(target, collected), target


def test_s09_junit_collector_derives_parametrized_and_nonpass_targets() -> None:
    xml = b"""<?xml version='1.0' encoding='utf-8'?>
<testsuites><testsuite tests='4' failures='1' skipped='1'>
  <testcase classname='tests.test_sample' name='test_many[a]' />
  <testcase classname='tests.test_sample' name='test_many[b]' />
  <testcase classname='tests.test_sample' name='test_failure'>
    <failure message='bounded'>bounded</failure>
  </testcase>
  <testcase classname='tests.test_sample' name='test_xfail'>
    <skipped type='pytest.xfail' message='expected' />
  </testcase>
</testsuite></testsuites>"""
    targets = frozenset(
        {
            "tests/test_sample.py::test_many",
            "tests/test_sample.py::test_many[a]",
            "tests/test_sample.py::test_failure",
            "tests/test_sample.py::test_xfail",
            "tests/test_sample.py::test_missing",
        }
    )
    result = parse_pytest_junit(
        xml,
        requested_targets=targets,
        argv=("uv", "run", "pytest"),
        exit_status=1,
        duration_seconds=0.1254,
        output="2 passed, 1 failed, 1 xfailed, 1 warning in 0.12s",
    )
    assert result.duration_seconds == 0.125
    assert result.census.selected == 4
    assert result.census.passed == 2
    assert result.census.skipped == 0
    assert result.census.xfailed == 1
    assert result.census.rerun == 0
    assert result.census.warnings == 1
    assert result.target_states == {
        "tests/test_sample.py::test_failure": "FAIL",
        "tests/test_sample.py::test_many": "PASS",
        "tests/test_sample.py::test_many[a]": "PASS",
        "tests/test_sample.py::test_missing": "BLOCKED",
        "tests/test_sample.py::test_xfail": "FAIL",
    }
    assert len(result.output_tail) <= 2000


@pytest.mark.parametrize(
    "parsed",
    [
        _parsed_run(raw_status=1),
        _parsed_run(raw_status=-15),
        _parsed_run(target_state="FAIL"),
        _parsed_run(target_state="BLOCKED"),
        _parsed_run(skipped=1),
        _parsed_run(xfailed=1),
        _parsed_run(rerun=1),
    ],
    ids=("pytest-fail", "signal", "target-fail", "blocked", "skip", "xfail", "rerun"),
)
def test_s09_gate_exit_status_rejects_every_nonpass_condition(
    parsed: ParsedPytestRun,
) -> None:
    assert gate_exit_status(parsed) > 0


def test_s09_gate_exit_status_accepts_all_pass_and_known_warning() -> None:
    assert gate_exit_status(_parsed_run()) == 0
    assert gate_exit_status(_parsed_run(warnings=1)) == 0


def test_s09_gate_exit_status_rejects_xpass_summary() -> None:
    xml = b"""<testsuites><testsuite tests='1'>
      <testcase classname='tests.test_sample' name='test_case' />
    </testsuite></testsuites>"""
    parsed = parse_pytest_junit(
        xml,
        requested_targets=frozenset({"tests/test_sample.py::test_case"}),
        argv=("uv", "run", "pytest"),
        exit_status=0,
        duration_seconds=0.1,
        output="1 xpassed in 0.10s",
    )
    assert parsed.census.xfailed == 1
    assert gate_exit_status(parsed) == 1


def test_s09_missing_junit_is_blocked_and_fails_closed() -> None:
    targets = frozenset({"tests/test_sample.py::test_case"})
    parsed = blocked_pytest_run(
        targets,
        argv=("uv", "run", "pytest"),
        exit_status=0,
        duration_seconds=0.1,
        output="bounded",
    )
    assert parsed.target_states == {"tests/test_sample.py::test_case": "BLOCKED"}
    assert "did not produce JUnit XML" in parsed.output_tail
    assert gate_exit_status(parsed) == 1


def test_s09_gate_result_uses_effective_status_and_bounded_diagnostics() -> None:
    targets = frozenset({"tests/test_sample.py::test_case"})
    parsed = _parsed_run(target_state="BLOCKED", output="x" * 2500)
    result = gate_result("bundles", parsed, targets)
    assert result["pytest_exit_status"] == 0
    assert result["exit_status"] == 1
    assert result["failed_targets"] == ["tests/test_sample.py::test_case"]
    assert len(str(result["output_tail"])) == 2000


def test_s09_run_group_returns_derived_public_status(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    parsed = _parsed_run(skipped=1, output="skip is forbidden")

    def execute_group(group: str, targets: frozenset[str]) -> ParsedPytestRun:
        assert group == "bundles"
        assert targets == S09_BUNDLE_TARGET_UNION
        return parsed

    monkeypatch.setattr(s09_acceptance, "execute_group", execute_group)
    assert s09_acceptance.run_group("bundles") == 1
    result = json.loads(capsys.readouterr().out)
    assert result["pytest_exit_status"] == 0
    assert result["exit_status"] == 1
    assert result["output_tail"] == "skip is forbidden"


def test_s09_ledgers_are_derived_from_concrete_target_results() -> None:
    target_states: dict[str, EvidenceState] = {
        target: "PASS" for target in S09_BUNDLE_TARGET_UNION
    }
    bundle_ledger = derive_ledger(S09_BUNDLE_TARGETS, target_states)
    acceptance_ledger = derive_acceptance_ledger(bundle_ledger)
    outcome_ledger = derive_outcome_ledger(acceptance_ledger)
    assert set(bundle_ledger) == M2_EVIDENCE_BUNDLES
    assert set(acceptance_ledger) == M2_ACCEPTANCE_CRITERIA
    assert set(outcome_ledger) == M2_OUTCOMES
    assert set(bundle_ledger.values()) == {"PASS"}
    assert set(acceptance_ledger.values()) == {"PASS"}
    assert set(outcome_ledger.values()) == {"PASS"}

    failed_target = min(S09_BUNDLE_TARGETS["M2-VER-01"])
    failed_target_states = dict(target_states)
    failed_target_states[failed_target] = "FAIL"
    failed_bundles = derive_ledger(S09_BUNDLE_TARGETS, failed_target_states)
    assert failed_bundles["M2-VER-01"] == "FAIL"

    scenario_ledger: dict[str, EvidenceState] = {
        scenario: "PASS" for scenario in M2_CONCURRENCY_SCENARIOS
    }
    predicate_ledger = derive_predicate_ledger(
        scenario_ledger, predicate_assertion_passed=True
    )
    assert set(predicate_ledger) == set(M2_PREDICATE_TO_SCENARIOS)
    assert set(predicate_ledger.values()) == {"PASS"}
    failed_scenario = min(M2_PREDICATE_TO_SCENARIOS["NU"])
    failed_scenario_ledger = dict(scenario_ledger)
    failed_scenario_ledger[failed_scenario] = "FAIL"
    assert (
        derive_predicate_ledger(
            failed_scenario_ledger, predicate_assertion_passed=True
        )["NU"]
        == "FAIL"
    )
    assert set(
        derive_predicate_ledger(
            scenario_ledger, predicate_assertion_passed=False
        ).values()
    ) == {"FAIL"}


def test_s09_state_vocabulary_is_exact_and_bounded() -> None:
    states = {
        "READY",
        "IN PROGRESS",
        "CANDIDATE READY FOR REVIEW",
        "REVIEW CHANGES REQUIRED",
        "COMPLETED",
    }
    for state in states:
        assert s09_state(f"| `M2-S09` | {state} | dependency |\n") == state
    for invalid in ("BLOCKED", "ACCEPTED", "CANDIDATE", "COMPLETED EXTRA"):
        with pytest.raises(ValueError, match="unsupported M2-S09 state"):
            s09_state(f"| `M2-S09` | {invalid} | dependency |\n")
    with pytest.raises(ValueError, match="status row is missing"):
        s09_state("M2-S09 IN PROGRESS\n")


@pytest.mark.parametrize("state", ["READY", "IN PROGRESS"])
def test_s09_lifecycle_accepts_exact_pre_candidate_states(
    tmp_path: Path, state: S09State
) -> None:
    _lifecycle_tree(tmp_path, state)
    assert validate_s09_lifecycle(tmp_path, state, EXPECTATIONS) is None


@pytest.mark.parametrize(
    ("state", "decision"),
    [
        ("CANDIDATE READY FOR REVIEW", None),
        ("REVIEW CHANGES REQUIRED", "REVIEW CHANGES REQUIRED"),
        ("COMPLETED", "ACCEPTED"),
    ],
)
def test_s09_lifecycle_accepts_exact_state_decision_matrix(
    tmp_path: Path, state: S09State, decision: ReviewerDecision | None
) -> None:
    record = replace(_complete_record(), reviewer_decision=decision)
    _lifecycle_tree(tmp_path, state, record)
    assert validate_s09_lifecycle(tmp_path, state, EXPECTATIONS) == record


@pytest.mark.parametrize(
    ("state", "decision"),
    [
        ("CANDIDATE READY FOR REVIEW", "ACCEPTED"),
        ("CANDIDATE READY FOR REVIEW", "REVIEW CHANGES REQUIRED"),
        ("REVIEW CHANGES REQUIRED", None),
        ("REVIEW CHANGES REQUIRED", "ACCEPTED"),
        ("COMPLETED", None),
        ("COMPLETED", "REVIEW CHANGES REQUIRED"),
    ],
)
def test_s09_lifecycle_rejects_incoherent_state_decision_matrix(
    tmp_path: Path, state: S09State, decision: ReviewerDecision | None
) -> None:
    record = replace(_complete_record(), reviewer_decision=decision)
    _lifecycle_tree(tmp_path, state, record)
    with pytest.raises(ValueError):
        validate_s09_lifecycle(tmp_path, state, EXPECTATIONS)


def test_s09_lifecycle_allows_nonpass_rejection_but_not_candidate(
    tmp_path: Path,
) -> None:
    record = _complete_record()
    bundle = min(record.evidence_bundles)
    nonpass = replace(
        record,
        commands=(replace(record.commands[0], exit_status=1),),
        evidence_bundles=record.evidence_bundles | {bundle: "FAIL"},
        runtime_census=replace(record.runtime_census, skipped=1),
        open_findings=("qualitative reviewer finding",),
    )
    rejected = replace(nonpass, reviewer_decision="REVIEW CHANGES REQUIRED")
    rejected_root = tmp_path / "rejected"
    _lifecycle_tree(rejected_root, "REVIEW CHANGES REQUIRED", rejected)
    assert (
        validate_s09_lifecycle(rejected_root, "REVIEW CHANGES REQUIRED", EXPECTATIONS)
        == rejected
    )

    candidate = replace(nonpass, reviewer_decision=None)
    candidate_root = tmp_path / "candidate"
    _lifecycle_tree(candidate_root, "CANDIDATE READY FOR REVIEW", candidate)
    with pytest.raises(ValueError, match="candidate state requires"):
        validate_s09_lifecycle(
            candidate_root, "CANDIDATE READY FOR REVIEW", EXPECTATIONS
        )


@pytest.mark.parametrize(
    ("state", "stale_summary"),
    [
        (
            "CANDIDATE READY FOR REVIEW",
            _ACCEPTANCE_SUMMARIES["REVIEW CHANGES REQUIRED"],
        ),
        (
            "REVIEW CHANGES REQUIRED",
            _ACCEPTANCE_SUMMARIES["CANDIDATE READY FOR REVIEW"],
        ),
        ("COMPLETED", _ACCEPTANCE_SUMMARIES["CANDIDATE READY FOR REVIEW"]),
    ],
)
def test_s09_lifecycle_rejects_phase_stale_acceptance_summary(
    tmp_path: Path, state: S09State, stale_summary: str
) -> None:
    decisions: dict[S09State, ReviewerDecision | None] = {
        "READY": None,
        "IN PROGRESS": None,
        "CANDIDATE READY FOR REVIEW": None,
        "REVIEW CHANGES REQUIRED": "REVIEW CHANGES REQUIRED",
        "COMPLETED": "ACCEPTED",
    }
    decision = decisions[state]
    record = replace(_complete_record(), reviewer_decision=decision)
    _lifecycle_tree(tmp_path, state, record, summary=stale_summary)
    with pytest.raises(ValueError, match="acceptance summary"):
        validate_s09_lifecycle(tmp_path, state, EXPECTATIONS)


def test_s09_lifecycle_rejects_unclassified_evidence_and_wrong_aid_state(
    tmp_path: Path,
) -> None:
    _lifecycle_tree(tmp_path, "IN PROGRESS")
    evidence = tmp_path / "docs/milestones/M2/evidence"
    (evidence / "unclassified.json").write_text("{}\n")
    with pytest.raises(ValueError, match="unclassified"):
        validate_evidence_lifecycle(tmp_path, "IN PROGRESS")

    (evidence / "unclassified.json").unlink()
    aid = tmp_path / "docs" / "milestones" / "M2" / "wip" / "M2-S09-codex-prompt.md"
    aid.unlink()
    with pytest.raises(ValueError, match="aid lifecycle"):
        validate_s09_lifecycle(tmp_path, "IN PROGRESS", EXPECTATIONS)

    completed_root = tmp_path / "completed"
    accepted = replace(_complete_record(), reviewer_decision="ACCEPTED")
    _lifecycle_tree(completed_root, "COMPLETED", accepted)
    completed_aid = (
        completed_root / "docs" / "milestones" / "M2" / "wip" / "M2-S09-codex-prompt.md"
    )
    completed_aid.parent.mkdir(parents=True)
    completed_aid.write_text("stale aid\n")
    with pytest.raises(ValueError, match="aid lifecycle"):
        validate_s09_lifecycle(completed_root, "COMPLETED", EXPECTATIONS)


def test_s09_real_candidate_record_and_acceptance_follow_current_lifecycle() -> None:
    state = s09_state(STATUS.read_text())
    record = validate_s09_lifecycle(ROOT, state, EXPECTATIONS)
    if state in {"READY", "IN PROGRESS"}:
        assert record is None
        return

    assert record is not None
    record_path = validate_evidence_lifecycle(ROOT, state)
    assert record_path is not None
    match = record_path.name.removeprefix("candidate-").removesuffix(".json")
    record_bytes = record_path.read_bytes()
    assert record.candidate_commit == match
    assert stable_evidence_json(record).encode() == record_bytes
    assert set(record.evidence_bundles) == M2_EVIDENCE_BUNDLES
    assert set(record.scenarios) == M2_CONCURRENCY_SCENARIOS
    assert set(record.predicates) == set(M2_PREDICATE_TO_SCENARIOS)
    if state == "REVIEW CHANGES REQUIRED":
        assert record.reviewer_decision == "REVIEW CHANGES REQUIRED"
    elif state == "CANDIDATE READY FOR REVIEW":
        assert record.reviewer_decision is None
    else:
        assert state == "COMPLETED"
        assert record.reviewer_decision == "ACCEPTED"

    acceptance = (ROOT / "docs/milestones/M2/acceptance.md").read_text()
    for expected in (
        record.candidate_commit,
        record_path.relative_to(ROOT).as_posix(),
        record.wheel.sha256,
        record.runtime_lock.sha256,
        "32 / 32",
        "83 / 83",
        "21 / 21",
    ):
        assert expected in acceptance

    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", record.candidate_commit, "HEAD"],
        cwd=ROOT,
        check=False,
    )
    assert ancestry.returncode == 0
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", record_path.relative_to(ROOT)],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    if tracked.returncode == 0:
        assert record.candidate_commit != head
    else:
        # The bounded pre-commit publication tree momentarily still points at the
        # candidate HEAD. Once this record is tracked, the identities must differ.
        assert record.candidate_commit == head
    candidate_acceptance = subprocess.run(
        [
            "git",
            "cat-file",
            "-e",
            f"{record.candidate_commit}:docs/milestones/M2/acceptance.md",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    assert candidate_acceptance.returncode != 0
