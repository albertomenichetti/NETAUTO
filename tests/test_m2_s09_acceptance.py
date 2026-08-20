"""Permanent lifecycle, registry, collector, and real-record checks for M2-S09."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.support.m2_evidence import (
    REVIEWER_DECISIONS,
    EvidenceExpectations,
    EvidenceState,
    stable_evidence_json,
    validate_evidence_record,
)
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
    derive_acceptance_ledger,
    derive_ledger,
    derive_outcome_ledger,
    derive_predicate_ledger,
    final_evidence_from_json,
    parse_pytest_junit,
    s09_state,
    target_is_collected,
    validate_evidence_lifecycle,
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


def test_s09_evidence_lifecycle_accepts_pre_candidate_candidate_and_review(
    tmp_path: Path,
) -> None:
    evidence = tmp_path / "docs/milestones/M2/evidence"
    evidence.mkdir(parents=True)
    (evidence / "README.md").write_text("format\n")
    assert validate_evidence_lifecycle(tmp_path, "IN PROGRESS") is None

    candidate = evidence / f"candidate-{'a' * 40}.json"
    candidate.write_text("{}\n")
    acceptance = tmp_path / "docs/milestones/M2/acceptance.md"
    acceptance.write_text("candidate\n")
    assert (
        validate_evidence_lifecycle(tmp_path, "CANDIDATE READY FOR REVIEW") == candidate
    )
    assert validate_evidence_lifecycle(tmp_path, "COMPLETED") == candidate

    extra = evidence / "unclassified.json"
    extra.write_text("{}\n")
    with pytest.raises(ValueError, match="unclassified"):
        validate_evidence_lifecycle(tmp_path, "CANDIDATE READY FOR REVIEW")


def test_s09_real_candidate_record_and_acceptance_follow_current_lifecycle() -> None:
    state = s09_state(STATUS.read_text())
    record_path = validate_evidence_lifecycle(ROOT, state)
    if state in {"READY", "IN PROGRESS"}:
        assert record_path is None
        return

    assert record_path is not None
    match = record_path.name.removeprefix("candidate-").removesuffix(".json")
    record_bytes = record_path.read_bytes()
    record = final_evidence_from_json(record_bytes)
    assert record.candidate_commit == match
    assert stable_evidence_json(record).encode() == record_bytes
    if state == "CANDIDATE READY FOR REVIEW":
        validate_evidence_record(record, EXPECTATIONS, phase="implementer")
        assert record.reviewer_decision is None
    else:
        validate_evidence_record(record, EXPECTATIONS, phase="reviewer")
        assert record.reviewer_decision in REVIEWER_DECISIONS

    assert set(record.evidence_bundles) == M2_EVIDENCE_BUNDLES
    assert set(record.scenarios) == M2_CONCURRENCY_SCENARIOS
    assert set(record.predicates) == set(M2_PREDICATE_TO_SCENARIOS)
    assert set(record.evidence_bundles.values()) == {"PASS"}
    assert set(record.scenarios.values()) == {"PASS"}
    assert set(record.predicates.values()) == {"PASS"}
    assert record.installed_t9 == "PASS"
    assert record.open_findings == ()

    acceptance = (ROOT / "docs/milestones/M2/acceptance.md").read_text()
    for expected in (
        "# M2 Final Acceptance Candidate",
        "Status: CANDIDATE READY FOR REVIEW",
        record.candidate_commit,
        record_path.relative_to(ROOT).as_posix(),
        record.wheel.sha256,
        record.runtime_lock.sha256,
        "32 / 32",
        "83 / 83",
        "21 / 21",
        "reviewer-owned",
        "M2-S09 is not COMPLETED",
        "M2 is not DELIVERED",
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
