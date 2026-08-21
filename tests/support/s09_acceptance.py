"""Derived, test-only harness for the M2-S09 final acceptance gate."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, cast

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
    TestCensus,
    validate_evidence_record,
)
from tests.test_m2_traceability import (
    CLI_REMOTE_OPERATION_COVERAGE,
    M2_ACCEPTANCE_CRITERIA,
    M2_ACCEPTANCE_TO_EVIDENCE,
    M2_AS_IS_GUARANTEE_TO_TARGETS,
    M2_CONCURRENCY_SCENARIOS,
    M2_CONTRACT_QUALITY_GATE_TO_TARGETS,
    M2_CONTRACT_QUALITY_GATES,
    M2_EVIDENCE_BUNDLES,
    M2_EVIDENCE_TO_TARGETS,
    M2_NEGATIVE_SURFACE_TO_TARGETS,
    M2_OUTCOME_TO_ACCEPTANCE,
    M2_OUTCOMES,
    M2_PREDICATE_TO_SCENARIOS,
    M2_SCENARIO_TO_RECIPES,
    M2_SCENARIO_TO_TARGETS,
    PUBLIC_HTTP_OPERATIONS,
)

type S09State = Literal[
    "READY",
    "IN PROGRESS",
    "CANDIDATE READY FOR REVIEW",
    "REVIEW CHANGES REQUIRED",
    "COMPLETED",
]
type CaseState = Literal["PASS", "FAIL", "SKIP", "XFAIL", "RERUN"]

S09_PREDICATE_ASSERTION_TARGET = (
    "tests/test_m2_traceability.py::test_s03_predicate_registry_is_the_exact_frozen_map"
)
S09_BUNDLE_TARGETS: dict[str, frozenset[str]] = {
    bundle: evidence.targets for bundle, evidence in M2_EVIDENCE_TO_TARGETS.items()
}
S09_BUNDLE_TARGET_UNION = frozenset(
    target for targets in S09_BUNDLE_TARGETS.values() for target in targets
)
S09_SCENARIO_TARGETS: dict[str, frozenset[str]] = {
    scenario: targets for scenario, targets in M2_SCENARIO_TO_TARGETS.items()
}
S09_SCENARIO_TARGET_UNION = frozenset(
    target for targets in S09_SCENARIO_TARGETS.values() for target in targets
)
S09_PREDICATE_TARGET_UNION = frozenset(
    {
        S09_PREDICATE_ASSERTION_TARGET,
        *(
            target
            for scenarios in M2_PREDICATE_TO_SCENARIOS.values()
            for scenario in scenarios
            for target in S09_SCENARIO_TARGETS[scenario]
        ),
    }
)
S09_CONTRACT_QUALITY_TARGET_UNION = frozenset(
    target
    for targets in M2_CONTRACT_QUALITY_GATE_TO_TARGETS.values()
    for target in targets
)
S09_SCENARIO_RECIPES = {
    scenario: recipe for scenario, recipe in M2_SCENARIO_TO_RECIPES.items()
}
S09_IDENTIFIER_CENSUS = {
    "outcomes": len(M2_OUTCOMES),
    "acceptance_criteria": len(M2_ACCEPTANCE_CRITERIA),
    "evidence_bundles": len(M2_EVIDENCE_BUNDLES),
    "scenarios": len(M2_CONCURRENCY_SCENARIOS),
    "predicates": len(M2_PREDICATE_TO_SCENARIOS),
    "negative_surfaces": len(M2_NEGATIVE_SURFACE_TO_TARGETS),
    "contract_quality_gates": len(M2_CONTRACT_QUALITY_GATES),
}
S09_OPERATION_CENSUS = {
    "business_http": len(PUBLIC_HTTP_OPERATIONS) - 1,
    "health_http": 1,
    "cli_remote": len(CLI_REMOTE_OPERATION_COVERAGE),
}
S09_FINAL_GATE_TARGETS: dict[str, frozenset[str]] = {
    "evidence_bundles": S09_BUNDLE_TARGET_UNION,
    "canonical_scenarios": S09_SCENARIO_TARGET_UNION,
    "safety_predicates": S09_PREDICATE_TARGET_UNION,
    "contract_quality": S09_CONTRACT_QUALITY_TARGET_UNION,
    "as_is_regression": frozenset(
        target
        for targets in M2_AS_IS_GUARANTEE_TO_TARGETS.values()
        for target in targets
    ),
    "negative_surface": frozenset(
        target
        for targets in M2_NEGATIVE_SURFACE_TO_TARGETS.values()
        for target in targets
    ),
}

_STATE_ROW = re.compile(r"^\| `M2-S09` \| ([^|]+?) \|", re.MULTILINE)
_CANDIDATE_NAME = re.compile(r"^candidate-([0-9a-f]{40})\.json$")
_SUMMARY_COUNT = {
    name: re.compile(rf"(?<![\w-])(\d+) {name}s?(?![\w-])")
    for name in ("warning", "xfailed", "xpassed", "rerun")
}
_S09_STATES = frozenset(
    {
        "READY",
        "IN PROGRESS",
        "CANDIDATE READY FOR REVIEW",
        "REVIEW CHANGES REQUIRED",
        "COMPLETED",
    }
)


@dataclass(frozen=True, slots=True)
class ParsedPytestRun:
    """Bounded concrete pytest result used to derive final ledgers."""

    argv: tuple[str, ...]
    exit_status: int
    duration_seconds: float
    census: TestCensus
    target_states: dict[str, EvidenceState]
    output_tail: str


def s09_state(status_text: str) -> S09State:
    """Return the exact S09 state from the normative status table."""
    match = _STATE_ROW.search(status_text)
    if match is None:
        raise ValueError("M2-S09 status row is missing")
    state = match.group(1).strip()
    if state not in _S09_STATES:
        raise ValueError(f"unsupported M2-S09 state: {state}")
    return cast(S09State, state)


def candidate_evidence_paths(root: Path) -> tuple[Path, ...]:
    """Return the finite candidate-record inventory in stable order."""
    evidence = root / "docs/milestones/M2/evidence"
    return tuple(
        path
        for path in sorted(evidence.iterdir())
        if path.is_file() and _CANDIDATE_NAME.fullmatch(path.name)
    )


def validate_evidence_lifecycle(root: Path, state: S09State) -> Path | None:
    """Validate the finite pre-candidate, candidate, or reviewer evidence inventory."""
    evidence = root / "docs/milestones/M2/evidence"
    readme = evidence / "README.md"
    acceptance = root / "docs/milestones/M2/acceptance.md"
    if not readme.is_file():
        raise ValueError("evidence README is missing")
    candidates = candidate_evidence_paths(root)
    allowed = {readme, *candidates}
    extra = {path for path in evidence.iterdir() if path.is_file()} - allowed
    if extra:
        raise ValueError(
            f"unclassified evidence files: {sorted(path.name for path in extra)}"
        )
    if state in {"READY", "IN PROGRESS"}:
        if candidates or acceptance.exists():
            raise ValueError("pre-candidate state contains candidate evidence")
        return None
    if len(candidates) != 1 or not acceptance.is_file():
        raise ValueError("candidate state requires one record and acceptance.md")
    return candidates[0]


def _normalized_lines(text: str) -> frozenset[str]:
    return frozenset(" ".join(line.split()) for line in text.splitlines())


def _validate_acceptance_summary(text: str, state: S09State) -> None:
    lines = _normalized_lines(text)
    if state == "CANDIDATE READY FOR REVIEW":
        required = {
            "# M2 Final Acceptance Candidate",
            "Status: CANDIDATE READY FOR REVIEW",
            "reviewer decision PENDING / reviewer-owned",
            "M2-S09 is not COMPLETED",
            "M2 is not DELIVERED",
        }
        forbidden = {
            "Status: REVIEW CHANGES REQUIRED",
            "Status: ACCEPTED",
            "reviewer decision REVIEW CHANGES REQUIRED",
            "reviewer decision ACCEPTED",
            "M2-S09 REVIEW CHANGES REQUIRED",
            "M2-S09 COMPLETED",
        }
    elif state == "REVIEW CHANGES REQUIRED":
        required = {
            "# M2 Final Acceptance Review",
            "Status: REVIEW CHANGES REQUIRED",
            "reviewer decision REVIEW CHANGES REQUIRED",
            "M2-S09 REVIEW CHANGES REQUIRED",
            "M2 NOT DELIVERED",
        }
        forbidden = {
            "# M2 Final Acceptance Candidate",
            "Status: CANDIDATE READY FOR REVIEW",
            "Status: ACCEPTED",
            "reviewer decision PENDING / reviewer-owned",
            "reviewer decision ACCEPTED",
            "M2-S09 is not COMPLETED",
            "M2-S09 COMPLETED",
        }
    elif state == "COMPLETED":
        required = {
            "# M2 Final Acceptance Review",
            "Status: ACCEPTED",
            "reviewer decision ACCEPTED",
            "M2-S09 COMPLETED",
            "M2 NOT DELIVERED",
        }
        forbidden = {
            "# M2 Final Acceptance Candidate",
            "Status: CANDIDATE READY FOR REVIEW",
            "Status: REVIEW CHANGES REQUIRED",
            "reviewer decision PENDING / reviewer-owned",
            "reviewer decision REVIEW CHANGES REQUIRED",
            "M2-S09 is not COMPLETED",
            "M2-S09 REVIEW CHANGES REQUIRED",
        }
    else:
        raise ValueError(f"acceptance summary is not valid for {state}")
    missing = required - lines
    if missing:
        raise ValueError(f"acceptance summary markers missing: {sorted(missing)}")
    stale = forbidden & lines
    if stale:
        raise ValueError(f"stale acceptance summary markers: {sorted(stale)}")


def _require_all_pass_candidate(record: FinalEvidenceRecord) -> None:
    for ledger_name, ledger in (
        ("evidence_bundles", record.evidence_bundles),
        ("scenarios", record.scenarios),
        ("predicates", record.predicates),
    ):
        if not all(state == "PASS" for state in ledger.values()):
            raise ValueError(
                f"candidate state requires every {ledger_name} entry to PASS"
            )
    if record.installed_t9 != "PASS":
        raise ValueError("candidate state requires installed_t9 to PASS")
    if record.open_findings:
        raise ValueError("candidate state requires open_findings to be empty")


def validate_s09_lifecycle(
    root: Path,
    state: S09State,
    expectations: EvidenceExpectations,
) -> FinalEvidenceRecord | None:
    """Validate the exact S09 state, decision, summary, evidence, and aid matrix."""
    record_path = validate_evidence_lifecycle(root, state)
    aid = root / "docs" / "milestones" / "M2" / "wip" / "M2-S09-codex-prompt.md"
    if (state == "COMPLETED") == aid.exists():
        raise ValueError(f"active S09 aid lifecycle is incoherent for {state}")
    if record_path is None:
        return None

    record = final_evidence_from_json(record_path.read_bytes())
    candidate_sha = record_path.name.removeprefix("candidate-").removesuffix(".json")
    if record.candidate_commit != candidate_sha:
        raise ValueError("candidate filename does not match candidate_commit")
    acceptance = (root / "docs/milestones/M2/acceptance.md").read_text()
    _validate_acceptance_summary(acceptance, state)

    if state == "CANDIDATE READY FOR REVIEW":
        validate_evidence_record(record, expectations, phase="implementer")
        if record.reviewer_decision is not None:
            raise ValueError("candidate state requires a null reviewer decision")
        _require_all_pass_candidate(record)
    elif state == "REVIEW CHANGES REQUIRED":
        validate_evidence_record(record, expectations, phase="reviewer")
        if record.reviewer_decision != "REVIEW CHANGES REQUIRED":
            raise ValueError("review-changes state requires its matching decision")
    elif state == "COMPLETED":
        validate_evidence_record(record, expectations, phase="reviewer")
        if record.reviewer_decision != "ACCEPTED":
            raise ValueError("completed state requires an ACCEPTED decision")
        _require_all_pass_candidate(record)
    else:
        raise ValueError(f"candidate evidence is not valid for {state}")
    return record


def _target_matches_node(target: str, node_id: str) -> bool:
    return node_id == target or (
        "[" not in target.rpartition("::")[2] and node_id.startswith(f"{target}[")
    )


def target_is_collected(target: str, collected: frozenset[str]) -> bool:
    """Return whether an exact or parametrized registry target was collected."""
    return any(_target_matches_node(target, node_id) for node_id in collected)


def _case_node_id(testcase: ET.Element) -> str:
    classname = testcase.attrib.get("classname", "")
    name = testcase.attrib.get("name", "")
    if not classname or not name:
        raise ValueError("JUnit testcase lacks classname or name")
    parts = classname.split(".")
    module_parts: list[str] = []
    for part in parts:
        if module_parts and part[:1].isupper():
            break
        module_parts.append(part)
    return f"{'/'.join(module_parts)}.py::{name}"


def _case_state(testcase: ET.Element) -> CaseState:
    children = tuple(testcase)
    if any(child.tag in {"failure", "error"} for child in children):
        return "FAIL"
    if any(child.tag.lower() in {"rerun", "flakyfailure"} for child in children):
        return "RERUN"
    skipped = next((child for child in children if child.tag == "skipped"), None)
    if skipped is None:
        return "PASS"
    marker = " ".join(skipped.attrib.values()).lower()
    return "XFAIL" if "xfail" in marker else "SKIP"


def _summary_count(output: str, name: str) -> int:
    return sum(int(match) for match in _SUMMARY_COUNT[name].findall(output))


def parse_pytest_junit(
    xml_bytes: bytes,
    *,
    requested_targets: frozenset[str],
    argv: Sequence[str],
    exit_status: int,
    duration_seconds: float,
    output: str,
) -> ParsedPytestRun:
    """Parse one pytest JUnit document and derive every requested target state."""
    root = ET.fromstring(xml_bytes)
    cases = tuple(root.iter("testcase"))
    observed = tuple((_case_node_id(case), _case_state(case)) for case in cases)
    target_states: dict[str, EvidenceState] = {}
    for target in sorted(requested_targets):
        states = tuple(
            state
            for node_id, state in observed
            if _target_matches_node(target, node_id)
        )
        if not states:
            target_states[target] = "BLOCKED"
        elif all(state == "PASS" for state in states):
            target_states[target] = "PASS"
        else:
            target_states[target] = "FAIL"

    passed = sum(state == "PASS" for _, state in observed)
    skipped = sum(state == "SKIP" for _, state in observed)
    xfailed = sum(state == "XFAIL" for _, state in observed)
    rerun = sum(state == "RERUN" for _, state in observed)
    xfailed += _summary_count(output, "xpassed")
    rerun = max(rerun, _summary_count(output, "rerun"))
    warnings = _summary_count(output, "warning")
    return ParsedPytestRun(
        argv=tuple(argv),
        exit_status=exit_status,
        duration_seconds=round(duration_seconds, 3),
        census=TestCensus(
            selected=len(cases),
            passed=passed,
            skipped=skipped,
            xfailed=xfailed,
            rerun=rerun,
            warnings=warnings,
        ),
        target_states=target_states,
        output_tail=output[-2000:],
    )


def gate_exit_status(parsed: ParsedPytestRun) -> int:
    """Return the fail-closed public status for one final-gate pytest run."""
    if parsed.exit_status != 0:
        return max(1, abs(parsed.exit_status))
    if any(state != "PASS" for state in parsed.target_states.values()):
        return 1
    if parsed.census.skipped or parsed.census.xfailed or parsed.census.rerun:
        return 1
    return 0


def derive_ledger(
    registry: Mapping[str, frozenset[str]],
    target_states: Mapping[str, EvidenceState],
) -> dict[str, EvidenceState]:
    """Derive a finite ledger from concrete target results."""
    ledger: dict[str, EvidenceState] = {}
    for identifier, targets in registry.items():
        states = tuple(target_states.get(target, "BLOCKED") for target in targets)
        if states and all(state == "PASS" for state in states):
            ledger[identifier] = "PASS"
        elif any(state == "FAIL" for state in states):
            ledger[identifier] = "FAIL"
        else:
            ledger[identifier] = "BLOCKED"
    return ledger


def derive_predicate_ledger(
    scenario_ledger: Mapping[str, EvidenceState],
    *,
    predicate_assertion_passed: bool,
) -> dict[str, EvidenceState]:
    """Require both scenario coverage and the permanent predicate assertion."""
    return {
        predicate: (
            "PASS"
            if predicate_assertion_passed
            and all(scenario_ledger.get(scenario) == "PASS" for scenario in scenarios)
            else "FAIL"
        )
        for predicate, scenarios in M2_PREDICATE_TO_SCENARIOS.items()
    }


def derive_acceptance_ledger(
    bundle_ledger: Mapping[str, EvidenceState],
) -> dict[str, EvidenceState]:
    """Derive M2-AC states through the frozen AC-to-VER mapping."""
    return {
        criterion: bundle_ledger.get(bundle, "BLOCKED")
        for criterion, bundle in M2_ACCEPTANCE_TO_EVIDENCE.items()
    }


def derive_outcome_ledger(
    acceptance_ledger: Mapping[str, EvidenceState],
) -> dict[str, EvidenceState]:
    """Derive M2-OUT coverage through the frozen OUT-to-AC mapping."""
    return {
        outcome: (
            "PASS"
            if all(acceptance_ledger.get(item) == "PASS" for item in criteria)
            else "FAIL"
        )
        for outcome, criteria in M2_OUTCOME_TO_ACCEPTANCE.items()
    }


def _mapping(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return cast(dict[str, object], value)


def _items(value: object, name: str) -> tuple[object, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be an array")
    return tuple(cast(list[object], value))


def _string(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    return value


def _integer(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")
    return value


def _number(value: object, name: str) -> float:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    return float(value)


def _boolean(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be boolean")
    return value


def _string_tuple(value: object, name: str) -> tuple[str, ...]:
    return tuple(_string(item, name) for item in _items(value, name))


def _state_ledger(value: object, name: str) -> dict[str, EvidenceState]:
    return {
        key: cast(EvidenceState, _string(item, f"{name}.{key}"))
        for key, item in _mapping(value, name).items()
    }


def final_evidence_from_json(data: bytes) -> FinalEvidenceRecord:
    """Decode the committed stable JSON into the tested evidence dataclasses."""
    raw = cast(object, json.loads(data))
    value = _mapping(raw, "record")
    wheel = _mapping(value.get("wheel"), "wheel")
    runtime_lock = _mapping(value.get("runtime_lock"), "runtime_lock")
    environment = _mapping(value.get("environment"), "environment")
    schema = _mapping(value.get("schema"), "schema")
    operations = _mapping(value.get("operations"), "operations")
    runtime = _mapping(value.get("runtime_census"), "runtime_census")
    commands: list[CommandEvidence] = []
    for index, item in enumerate(_items(value.get("commands"), "commands")):
        command = _mapping(item, f"commands[{index}]")
        census = _mapping(command.get("census"), f"commands[{index}].census")
        commands.append(
            CommandEvidence(
                argv=_string_tuple(command.get("argv"), "argv"),
                exit_status=_integer(command.get("exit_status"), "exit_status"),
                duration_seconds=_number(
                    command.get("duration_seconds"), "duration_seconds"
                ),
                census=TestCensus(
                    *(
                        _integer(census.get(field), field)
                        for field in (
                            "selected",
                            "passed",
                            "skipped",
                            "xfailed",
                            "rerun",
                            "warnings",
                        )
                    )
                ),
            )
        )
    decision = value.get("reviewer_decision")
    return FinalEvidenceRecord(
        schema_version=_integer(value.get("schema_version"), "schema_version"),
        candidate_commit=_string(value.get("candidate_commit"), "candidate_commit"),
        branch=_string(value.get("branch"), "branch"),
        release_version=_string(value.get("release_version"), "release_version"),
        wheel=ArtifactEvidence(
            path=_string(wheel.get("path"), "wheel.path"),
            byte_size=_integer(wheel.get("byte_size"), "wheel.byte_size"),
            member_count=_integer(wheel.get("member_count"), "wheel.member_count"),
            sha256=_string(wheel.get("sha256"), "wheel.sha256"),
        ),
        runtime_lock=RuntimeLockEvidence(
            path=_string(runtime_lock.get("path"), "runtime_lock.path"),
            byte_size=_integer(runtime_lock.get("byte_size"), "runtime_lock.byte_size"),
            package_count=_integer(
                runtime_lock.get("package_count"), "runtime_lock.package_count"
            ),
            sha256=_string(runtime_lock.get("sha256"), "runtime_lock.sha256"),
        ),
        environment=EnvironmentEvidence(
            python=_string(environment.get("python"), "environment.python"),
            uv=_string(environment.get("uv"), "environment.uv"),
            hatchling=_string(environment.get("hatchling"), "environment.hatchling"),
            postgresql=_string(environment.get("postgresql"), "environment.postgresql"),
            linux=_string(environment.get("linux"), "environment.linux"),
        ),
        locked_environment_confirmed=_boolean(
            value.get("locked_environment_confirmed"), "locked_environment_confirmed"
        ),
        build_confirmed=_boolean(value.get("build_confirmed"), "build_confirmed"),
        commands=tuple(commands),
        evidence_bundles=_state_ledger(
            value.get("evidence_bundles"), "evidence_bundles"
        ),
        scenarios=_state_ledger(value.get("scenarios"), "scenarios"),
        predicates=_state_ledger(value.get("predicates"), "predicates"),
        schema=SchemaEvidence(
            table_count=_integer(schema.get("table_count"), "schema.table_count"),
            alembic_bases=_string_tuple(
                schema.get("alembic_bases"), "schema.alembic_bases"
            ),
            alembic_heads=_string_tuple(
                schema.get("alembic_heads"), "schema.alembic_heads"
            ),
            database_revisions=_string_tuple(
                schema.get("database_revisions"), "schema.database_revisions"
            ),
            compare_metadata=_string_tuple(
                schema.get("compare_metadata"), "schema.compare_metadata"
            ),
        ),
        operations=OperationCensus(
            *(
                _integer(operations.get(field), f"operations.{field}")
                for field in (
                    "business_http",
                    "health_http",
                    "cli_remote",
                    "cli_local",
                    "cli_examples",
                )
            )
        ),
        installed_t9=cast(
            EvidenceState, _string(value.get("installed_t9"), "installed_t9")
        ),
        runtime_census=RuntimeCensus(
            *(
                _integer(runtime.get(field), f"runtime_census.{field}")
                for field in (
                    "skipped",
                    "xfailed",
                    "rerun",
                    "warnings",
                    "supported_40p01",
                    "unexpected_40001",
                )
            )
        ),
        open_findings=_string_tuple(value.get("open_findings"), "open_findings"),
        reviewer_decision=(
            None
            if decision is None
            else cast(ReviewerDecision, _string(decision, "reviewer_decision"))
        ),
    )


def _group_targets(group: str) -> frozenset[str]:
    if group == "bundles":
        return S09_BUNDLE_TARGET_UNION
    if group == "scenarios":
        return S09_SCENARIO_TARGET_UNION | {S09_PREDICATE_ASSERTION_TARGET}
    raise ValueError(f"unknown gate group: {group}")


def blocked_pytest_run(
    targets: frozenset[str],
    *,
    argv: Sequence[str],
    exit_status: int,
    duration_seconds: float,
    output: str,
) -> ParsedPytestRun:
    """Represent a missing JUnit document as bounded BLOCKED evidence."""
    return ParsedPytestRun(
        argv=tuple(argv),
        exit_status=exit_status,
        duration_seconds=round(duration_seconds, 3),
        census=TestCensus(0, 0, 0, 0, 0, 0),
        target_states={target: "BLOCKED" for target in targets},
        output_tail=(output + "\npytest did not produce JUnit XML")[-2000:],
    )


def execute_group(group: str, targets: frozenset[str]) -> ParsedPytestRun:
    public_argv = (
        "uv",
        "run",
        "python",
        "-m",
        "tests.support.s09_acceptance",
        "run",
        group,
    )
    with tempfile.TemporaryDirectory(prefix="netauto-s09-") as directory:
        junit = Path(directory) / "pytest.xml"
        pytest_argv = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            *sorted(targets),
            "--junitxml",
            str(junit),
        ]
        started = time.monotonic()
        completed = subprocess.run(
            pytest_argv,
            check=False,
            capture_output=True,
            text=True,
        )
        duration = time.monotonic() - started
        output = completed.stdout + completed.stderr
        if junit.exists():
            parsed = parse_pytest_junit(
                junit.read_bytes(),
                requested_targets=targets,
                argv=public_argv,
                exit_status=completed.returncode,
                duration_seconds=duration,
                output=output,
            )
        else:
            parsed = blocked_pytest_run(
                targets,
                argv=public_argv,
                exit_status=completed.returncode,
                duration_seconds=duration,
                output=output,
            )
    return parsed


def gate_result(
    group: str,
    parsed: ParsedPytestRun,
    targets: frozenset[str],
) -> dict[str, object]:
    """Build the public bounded JSON result using the effective gate status."""
    effective_status = gate_exit_status(parsed)

    result: dict[str, object] = {
        "argv": parsed.argv,
        "exit_status": effective_status,
        "pytest_exit_status": parsed.exit_status,
        "duration_seconds": parsed.duration_seconds,
        "census": asdict(parsed.census),
        "unique_targets": len(targets),
        "failed_targets": sorted(
            target for target, state in parsed.target_states.items() if state != "PASS"
        ),
        "output_tail": (
            parsed.output_tail[-2000:] or "final gate rejected non-PASS evidence"
            if effective_status
            else ""
        ),
    }
    if group == "bundles":
        result["evidence_bundles"] = derive_ledger(
            S09_BUNDLE_TARGETS, parsed.target_states
        )
    else:
        scenario_ledger = derive_ledger(S09_SCENARIO_TARGETS, parsed.target_states)
        result["scenarios"] = scenario_ledger
        result["predicates"] = derive_predicate_ledger(
            scenario_ledger,
            predicate_assertion_passed=(
                parsed.target_states.get(S09_PREDICATE_ASSERTION_TARGET) == "PASS"
            ),
        )
    return result


def run_group(group: str) -> int:
    targets = _group_targets(group)
    parsed = execute_group(group, targets)
    result = gate_result(group, parsed, targets)
    print(json.dumps(result, sort_keys=True))
    return cast(int, result["exit_status"])


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run")
    run.add_argument("group", choices=("bundles", "scenarios"))
    arguments = parser.parse_args(argv)
    if arguments.command != "run":
        parser.error("unsupported command")
    return run_group(cast(str, arguments.group))


if __name__ == "__main__":
    raise SystemExit(_main())
