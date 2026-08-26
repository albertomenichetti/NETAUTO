"""Lifecycle and mapped-target harness for the M3-S07 final gate."""

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

from tests.support.m3_evidence import M3_EVIDENCE_TO_TARGETS

type S07State = Literal[
    "READY",
    "IN PROGRESS",
    "CANDIDATE READY FOR REVIEW",
    "REVIEW CHANGES REQUIRED",
    "COMPLETED",
]
type CaseState = Literal["PASS", "FAIL", "ERROR", "SKIP", "XFAIL", "RERUN"]
_CASE_STATES: tuple[CaseState, ...] = (
    "PASS",
    "FAIL",
    "ERROR",
    "SKIP",
    "XFAIL",
    "RERUN",
)

ROOT = Path(__file__).parents[2]
M3_ROOT = ROOT / "docs/milestones/M3"

EXPECTED_M3_EVIDENCE_BUNDLES = frozenset(
    f"M3-VER-{number:02d}" for number in range(1, 20)
)
M3_MAPPED_TARGETS = frozenset(
    target for targets in M3_EVIDENCE_TO_TARGETS.values() for target in targets
)

_S07_STATES = frozenset(
    {
        "READY",
        "IN PROGRESS",
        "CANDIDATE READY FOR REVIEW",
        "REVIEW CHANGES REQUIRED",
        "COMPLETED",
    }
)
_STATUS_STATE = re.compile(
    r"^\*\*Milestone status:\*\* ACTIVE — [^\n]+ — M3-S07 "
    r"(READY|IN PROGRESS|CANDIDATE READY FOR REVIEW|"
    r"REVIEW CHANGES REQUIRED|COMPLETED)$",
    re.MULTILINE,
)
_SUMMARY_COUNT = {
    name: re.compile(rf"(?<![\w-])(\d+) {name}s?(?![\w-])")
    for name in ("warning", "xfailed", "xpassed", "rerun")
}
_ORIGINAL_PROMPT = "M3-S07-codex-prompt.md"
_REVIEW_FIX_PROMPT = "M3-S07-review-fix-prompt.md"
_KNOWN_PROMPTS = frozenset({_ORIGINAL_PROMPT, _REVIEW_FIX_PROMPT})


@dataclass(frozen=True, slots=True)
class S07LifecycleDocuments:
    """Pure inputs for one operational final-acceptance lifecycle state."""

    status_text: str
    acceptance_text: str | None
    candidate_evidence_exists: bool
    active_prompt_names: frozenset[str]


@dataclass(frozen=True, slots=True)
class MappedTargetCensus:
    """Fail-closed census for one registry-derived pytest invocation."""

    bundles: int
    mapped_targets: int
    concrete_cases: int
    passed: int
    failed: int
    errors: int
    skipped: int
    xfailed: int
    xpassed: int
    rerun: int
    warnings: int
    missing_targets: int


@dataclass(frozen=True, slots=True)
class ParsedMappedTargetRun:
    """Deterministic result parsed from pytest JUnit and terminal output."""

    pytest_exit_status: int
    duration_seconds: float
    census: MappedTargetCensus
    target_states: dict[str, str]
    bundle_states: dict[str, str]
    output_tail: str


def s07_state(status_text: str) -> S07State:
    """Return the exact S07 state from the milestone status heading."""
    match = _STATUS_STATE.search(status_text)
    if match is None:
        raise ValueError("M3-S07 milestone status heading is missing or unsupported")
    state = match.group(1)
    if state not in _S07_STATES:
        raise ValueError(f"unsupported M3-S07 state: {state}")
    return cast(S07State, state)


def _normalized(text: str) -> str:
    return "\n".join(" ".join(line.split()) for line in text.splitlines())


def _require(text: str, marker: str, *, source: str) -> None:
    if marker not in text:
        raise ValueError(f"{source} marker missing: {marker}")


def _require_match(text: str, pattern: str, *, source: str) -> None:
    if re.search(pattern, text, re.IGNORECASE) is None:
        raise ValueError(f"{source} marker missing: {pattern}")


def _validate_not_delivered(status: str, acceptance: str | None) -> None:
    combined = status if acceptance is None else f"{status}\n{acceptance}"
    _require_match(
        combined,
        r"M3\s+(?:is\s+)?NOT (?:ACCEPTED\s*(?:/|or)\s*(?:NOT\s+)?)?DELIVERED",
        source="M3",
    )


def _validate_review_acceptance(acceptance: str | None) -> None:
    if acceptance is None:
        raise ValueError("review state requires acceptance.md")
    _require(acceptance, "**Status:** REVIEW CHANGES REQUIRED", source="acceptance")
    _require(
        acceptance, "reviewer decision REVIEW CHANGES REQUIRED", source="acceptance"
    )
    _require_match(
        acceptance,
        r"M3-S07\s+REVIEW CHANGES REQUIRED\s*/\s*NOT COMPLETED",
        source="acceptance",
    )
    for stale in (
        "# M3 Final Acceptance Candidate",
        "**Status:** CANDIDATE READY FOR REVIEW",
        "**Status:** ACCEPTED",
        "reviewer decision PENDING / reviewer-owned",
        "reviewer decision ACCEPTED",
    ):
        if stale in acceptance:
            raise ValueError(f"stale acceptance marker for review state: {stale}")


def _validate_candidate_acceptance(acceptance: str | None) -> None:
    if acceptance is None:
        raise ValueError("candidate state requires acceptance.md")
    _require(acceptance, "# M3 Final Acceptance Candidate", source="acceptance")
    _require(acceptance, "**Status:** CANDIDATE READY FOR REVIEW", source="acceptance")
    _require(
        acceptance, "reviewer decision PENDING / reviewer-owned", source="acceptance"
    )
    _require_match(
        acceptance,
        r"M3-S07\s+(?:is\s+)?not COMPLETED",
        source="acceptance",
    )
    _require_match(
        acceptance,
        r"M3\s+(?:is\s+)?not ACCEPTED\s*(?:/|or)\s*(?:not\s+)?DELIVERED",
        source="acceptance",
    )
    for stale in (
        "# M3 Final Acceptance Review",
        "**Status:** REVIEW CHANGES REQUIRED",
        "**Status:** ACCEPTED",
        "reviewer decision REVIEW CHANGES REQUIRED",
        "reviewer decision ACCEPTED",
    ):
        if stale in acceptance:
            raise ValueError(f"stale acceptance marker for candidate state: {stale}")


def _validate_completed_acceptance(acceptance: str | None) -> None:
    if acceptance is None:
        raise ValueError("completed state requires acceptance.md")
    _require(acceptance, "# M3 Final Acceptance Review", source="acceptance")
    _require(acceptance, "**Status:** ACCEPTED", source="acceptance")
    _require(acceptance, "reviewer decision ACCEPTED", source="acceptance")
    _require_match(acceptance, r"M3-S07\s+COMPLETED", source="acceptance")
    _require_match(acceptance, r"M3\s+NOT DELIVERED", source="acceptance")
    _require_match(
        acceptance,
        r"final delivery(?: approval| / consolidation|/consolidation)?\s+"
        r"(?:NOT GRANTED|NOT AUTHORIZED|SEPARATE)",
        source="acceptance",
    )
    for stale in (
        "# M3 Final Acceptance Candidate",
        "**Status:** CANDIDATE READY FOR REVIEW",
        "**Status:** REVIEW CHANGES REQUIRED",
        "reviewer decision PENDING / reviewer-owned",
        "reviewer decision REVIEW CHANGES REQUIRED",
    ):
        if stale in acceptance:
            raise ValueError(f"stale acceptance marker for completed state: {stale}")


def validate_s07_lifecycle_documents(documents: S07LifecycleDocuments) -> S07State:
    """Validate the coherent status/decision/evidence/prompt matrix for S07."""
    state = s07_state(documents.status_text)
    status = _normalized(documents.status_text)
    acceptance = (
        None
        if documents.acceptance_text is None
        else _normalized(documents.acceptance_text)
    )
    prompts = documents.active_prompt_names
    unknown_prompts = prompts - _KNOWN_PROMPTS
    if unknown_prompts:
        raise ValueError(
            f"unexpected active M3 execution aids: {sorted(unknown_prompts)}"
        )

    _validate_not_delivered(status, acceptance)
    if state == "READY":
        _require(
            status,
            "software implementation AUTHORIZED — M3-S07 ONLY",
            source="status",
        )
        if documents.candidate_evidence_exists or acceptance is not None:
            raise ValueError("READY state cannot contain S07 candidate/review evidence")
        if prompts != frozenset({_ORIGINAL_PROMPT}):
            raise ValueError("READY state requires exactly the original S07 aid")
    elif state == "IN PROGRESS":
        if acceptance is None:
            _require(
                status,
                "software implementation AUTHORIZED — M3-S07 ONLY",
                source="status",
            )
            if documents.candidate_evidence_exists:
                raise ValueError(
                    "initial IN PROGRESS state cannot contain S07 evidence"
                )
            if prompts != frozenset({_ORIGINAL_PROMPT}):
                raise ValueError(
                    "initial IN PROGRESS state requires exactly the original S07 aid"
                )
        else:
            _require(
                status,
                "software implementation AUTHORIZED — M3-S07 REVIEW FIX ONLY",
                source="status",
            )
            _validate_review_acceptance(acceptance)
            if not documents.candidate_evidence_exists:
                raise ValueError("review-fix IN PROGRESS requires rejected evidence")
            if prompts != _KNOWN_PROMPTS:
                raise ValueError("review-fix IN PROGRESS requires both S07 aids")
    elif state == "REVIEW CHANGES REQUIRED":
        _require(
            status,
            "software implementation AUTHORIZED — M3-S07 REVIEW FIX ONLY",
            source="status",
        )
        _validate_review_acceptance(acceptance)
        if not documents.candidate_evidence_exists:
            raise ValueError("review state requires rejected candidate evidence")
        if prompts != _KNOWN_PROMPTS:
            raise ValueError("review state requires both S07 execution aids")
    elif state == "CANDIDATE READY FOR REVIEW":
        _require(
            status,
            "software implementation AUTHORIZED — M3-S07 ONLY",
            source="status",
        )
        _validate_candidate_acceptance(acceptance)
        if not documents.candidate_evidence_exists:
            raise ValueError("candidate state requires S07 candidate evidence")
        if not prompts or not prompts <= _KNOWN_PROMPTS:
            raise ValueError("candidate state requires only active S07 execution aids")
    else:
        assert state == "COMPLETED"
        _require(status, "software implementation NOT AUTHORIZED", source="status")
        _require_match(status, r"M3-S07\s+COMPLETED", source="status")
        _validate_completed_acceptance(acceptance)
        if not documents.candidate_evidence_exists:
            raise ValueError("completed state requires accepted candidate evidence")
        if prompts:
            raise ValueError("completed state requires all M3 execution aids retired")
    return state


def active_m3_prompt_names(root: Path) -> frozenset[str]:
    """Return the finite active M3 implementation/review-fix prompt inventory."""
    wip = root / "docs/milestones/M3/wip"
    return frozenset(path.name for path in wip.glob("M3-S*-*prompt.md"))


def validate_repository_lifecycle(root: Path = ROOT) -> S07State:
    """Validate the live repository against the pure S07 lifecycle model."""
    milestone = root / "docs/milestones/M3"
    acceptance_path = milestone / "acceptance.md"
    documents = S07LifecycleDocuments(
        status_text=(milestone / "status.md").read_text(),
        acceptance_text=(
            acceptance_path.read_text() if acceptance_path.is_file() else None
        ),
        candidate_evidence_exists=(
            milestone / "evidence/M3-S07-candidate.md"
        ).is_file(),
        active_prompt_names=active_m3_prompt_names(root),
    )
    return validate_s07_lifecycle_documents(documents)


def _target_matches_node(target: str, node_id: str) -> bool:
    return node_id == target or (
        "[" not in target.rpartition("::")[2] and node_id.startswith(f"{target}[")
    )


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
    tags = {child.tag.rpartition("}")[2].lower() for child in children}
    if tags & {"rerun", "flakyfailure", "flakyerror"}:
        return "RERUN"
    if "error" in tags:
        return "ERROR"
    if "failure" in tags:
        return "FAIL"
    skipped = next(
        (
            child
            for child in children
            if child.tag.rpartition("}")[2].lower() == "skipped"
        ),
        None,
    )
    if skipped is None:
        return "PASS"
    marker = " ".join((*skipped.attrib.values(), skipped.text or "")).lower()
    return "XFAIL" if "xfail" in marker else "SKIP"


def _summary_count(output: str, name: str) -> int:
    return sum(int(match) for match in _SUMMARY_COUNT[name].findall(output))


def _bundle_states(target_states: Mapping[str, str]) -> dict[str, str]:
    return {
        bundle: (
            "PASS"
            if targets
            and all(target_states.get(target) == "PASS" for target in targets)
            else "FAIL"
        )
        for bundle, targets in M3_EVIDENCE_TO_TARGETS.items()
    }


def parse_mapped_target_junit(
    xml_bytes: bytes,
    *,
    requested_targets: frozenset[str],
    pytest_exit_status: int,
    duration_seconds: float,
    output: str,
) -> ParsedMappedTargetRun:
    """Parse pytest JUnit and fail closed for every requested target/case."""
    root = ET.fromstring(xml_bytes)
    observed = tuple(
        (_case_node_id(case), _case_state(case)) for case in root.iter("testcase")
    )
    target_states: dict[str, str] = {}
    for target in sorted(requested_targets):
        states = tuple(
            state
            for node_id, state in observed
            if _target_matches_node(target, node_id)
        )
        if not states:
            target_states[target] = "MISSING"
        elif all(state == "PASS" for state in states):
            target_states[target] = "PASS"
        else:
            target_states[target] = "FAIL"

    counts = {
        state: sum(value == state for _, value in observed) for state in _CASE_STATES
    }
    xpassed = _summary_count(output, "xpassed")
    rerun = max(counts["RERUN"], _summary_count(output, "rerun"))
    census = MappedTargetCensus(
        bundles=len(M3_EVIDENCE_TO_TARGETS),
        mapped_targets=len(requested_targets),
        concrete_cases=len(observed),
        passed=counts["PASS"],
        failed=counts["FAIL"],
        errors=counts["ERROR"],
        skipped=counts["SKIP"],
        xfailed=counts["XFAIL"],
        xpassed=xpassed,
        rerun=rerun,
        warnings=_summary_count(output, "warning"),
        missing_targets=sum(state == "MISSING" for state in target_states.values()),
    )
    return ParsedMappedTargetRun(
        pytest_exit_status=pytest_exit_status,
        duration_seconds=round(duration_seconds, 3),
        census=census,
        target_states=target_states,
        bundle_states=_bundle_states(target_states),
        output_tail=output[-2000:],
    )


def mapped_gate_exit_status(result: ParsedMappedTargetRun) -> int:
    """Return the effective fail-closed status for the mapped-target gate."""
    if result.pytest_exit_status != 0:
        return max(1, abs(result.pytest_exit_status))
    if any(state != "PASS" for state in result.target_states.values()):
        return 1
    if any(state != "PASS" for state in result.bundle_states.values()):
        return 1
    census = result.census
    if any(
        (
            census.failed,
            census.errors,
            census.skipped,
            census.xfailed,
            census.xpassed,
            census.rerun,
            census.missing_targets,
        )
    ):
        return 1
    return 0


def _git_output(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise ValueError(completed.stdout + completed.stderr)
    return completed.stdout.strip()


def _assert_clean_candidate(candidate_sha: str) -> None:
    if re.fullmatch(r"[0-9a-f]{40}", candidate_sha) is None:
        raise ValueError(
            "candidate SHA must be exactly 40 lowercase hexadecimal digits"
        )
    if _git_output("rev-parse", "HEAD") != candidate_sha:
        raise ValueError("HEAD does not equal the requested immutable candidate SHA")
    if _git_output("status", "--porcelain"):
        raise ValueError("working tree is not clean at the candidate SHA")


def run_mapped_bundles(candidate_sha: str) -> int:
    """Execute every registry-derived M3 bundle target on one clean candidate."""
    if frozenset(M3_EVIDENCE_TO_TARGETS) != EXPECTED_M3_EVIDENCE_BUNDLES:
        raise ValueError("M3 evidence bundle keys are not the exact frozen 19")
    empty = sorted(
        bundle for bundle, targets in M3_EVIDENCE_TO_TARGETS.items() if not targets
    )
    if empty:
        raise ValueError(f"M3 evidence bundles have empty target sets: {empty}")
    _assert_clean_candidate(candidate_sha)

    with tempfile.TemporaryDirectory(prefix="netauto-m3-s07-") as directory:
        junit_path = Path(directory) / "mapped-targets.xml"
        pytest_argv = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            *sorted(M3_MAPPED_TARGETS),
            "--junitxml",
            str(junit_path),
        ]
        started = time.monotonic()
        completed = subprocess.run(
            pytest_argv,
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        duration = time.monotonic() - started
        output = completed.stdout + completed.stderr
        if not junit_path.is_file():
            result = {
                "candidate_sha": candidate_sha,
                "exit_status": max(1, abs(completed.returncode)),
                "pytest_exit_status": completed.returncode,
                "error": "pytest did not create the required JUnit report",
                "output_tail": output[-2000:],
            }
            print(json.dumps(result, sort_keys=True))
            return cast(int, result["exit_status"])
        parsed = parse_mapped_target_junit(
            junit_path.read_bytes(),
            requested_targets=M3_MAPPED_TARGETS,
            pytest_exit_status=completed.returncode,
            duration_seconds=duration,
            output=output,
        )

    _assert_clean_candidate(candidate_sha)
    exit_status = mapped_gate_exit_status(parsed)
    result = {
        "candidate_sha": candidate_sha,
        "exit_status": exit_status,
        "pytest_exit_status": parsed.pytest_exit_status,
        "duration_seconds": parsed.duration_seconds,
        "census": asdict(parsed.census),
        "bundle_states": parsed.bundle_states,
        "failed_targets": sorted(
            target for target, state in parsed.target_states.items() if state != "PASS"
        ),
        "output_tail": parsed.output_tail if exit_status else "",
    }
    print(json.dumps(result, sort_keys=True))
    return exit_status


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    mapped = subparsers.add_parser("run-mapped-bundles")
    mapped.add_argument("--candidate-sha", required=True)
    args = parser.parse_args(argv)
    if args.command == "run-mapped-bundles":
        return run_mapped_bundles(cast(str, args.candidate_sha))
    raise AssertionError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(_main())
