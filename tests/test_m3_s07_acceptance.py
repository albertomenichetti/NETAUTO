"""Permanent M3-S07 lifecycle and mapped-target harness evidence."""

from dataclasses import replace

import pytest

from tests.support.m3_evidence import (
    M3_EVIDENCE_BUNDLES,
    M3_EVIDENCE_TO_TARGETS,
)
from tests.support.m3_s07_acceptance import (
    EXPECTED_M3_EVIDENCE_BUNDLES,
    M3_MAPPED_TARGETS,
    MappedTargetCensus,
    ParsedMappedTargetRun,
    S07LifecycleDocuments,
    mapped_gate_exit_status,
    parse_mapped_target_junit,
    s07_state,
    validate_repository_lifecycle,
    validate_s07_lifecycle_documents,
)

ORIGINAL_PROMPT = "M3-S07-codex-prompt.md"
REVIEW_FIX_PROMPT = "M3-S07-review-fix-prompt.md"
REVIEW_PROMPTS = frozenset({ORIGINAL_PROMPT, REVIEW_FIX_PROMPT})


def _status(state: str, authorization: str) -> str:
    return f"""# M3 — Milestone Status

**Milestone status:** ACTIVE — FINAL ACCEPTANCE REVIEW — M3-S07 {state}

```text
software implementation  {authorization}
M3-S07                    {state}
M3                        NOT ACCEPTED / NOT DELIVERED
```
"""


REVIEW_ACCEPTANCE = """# M3 Final Acceptance Review

**Status:** REVIEW CHANGES REQUIRED

```text
reviewer decision       REVIEW CHANGES REQUIRED
M3-S07                  REVIEW CHANGES REQUIRED / NOT COMPLETED
M3                      NOT ACCEPTED / NOT DELIVERED
final delivery approval NOT GRANTED
```
"""

CANDIDATE_ACCEPTANCE = """# M3 Final Acceptance Candidate

**Status:** CANDIDATE READY FOR REVIEW

```text
reviewer decision       PENDING / reviewer-owned
M3-S07                  not COMPLETED
M3                      not ACCEPTED / not DELIVERED
final delivery approval not granted
```
"""

COMPLETED_ACCEPTANCE = """# M3 Final Acceptance Review

**Status:** ACCEPTED

```text
reviewer decision       ACCEPTED
M3-S07                  COMPLETED
M3                      NOT DELIVERED
final delivery approval NOT GRANTED — consolidation remains SEPARATE
```
"""


@pytest.mark.parametrize(
    "documents",
    [
        S07LifecycleDocuments(
            _status("READY", "AUTHORIZED — M3-S07 ONLY"),
            None,
            False,
            frozenset({ORIGINAL_PROMPT}),
        ),
        S07LifecycleDocuments(
            _status("IN PROGRESS", "AUTHORIZED — M3-S07 ONLY"),
            None,
            False,
            frozenset({ORIGINAL_PROMPT}),
        ),
        S07LifecycleDocuments(
            _status("IN PROGRESS", "AUTHORIZED — M3-S07 REVIEW FIX ONLY"),
            REVIEW_ACCEPTANCE,
            True,
            REVIEW_PROMPTS,
        ),
        S07LifecycleDocuments(
            _status(
                "REVIEW CHANGES REQUIRED",
                "AUTHORIZED — M3-S07 REVIEW FIX ONLY",
            ),
            REVIEW_ACCEPTANCE,
            True,
            REVIEW_PROMPTS,
        ),
        S07LifecycleDocuments(
            _status("CANDIDATE READY FOR REVIEW", "AUTHORIZED — M3-S07 ONLY"),
            CANDIDATE_ACCEPTANCE,
            True,
            REVIEW_PROMPTS,
        ),
        S07LifecycleDocuments(
            _status("COMPLETED", "NOT AUTHORIZED"),
            COMPLETED_ACCEPTANCE,
            True,
            frozenset(),
        ),
    ],
    ids=(
        "ready",
        "initial-in-progress",
        "review-fix-in-progress",
        "review-changes-required",
        "candidate-ready",
        "reviewer-completed",
    ),
)
def test_m3_s07_lifecycle_accepts_exact_state_matrix(
    documents: S07LifecycleDocuments,
) -> None:
    assert validate_s07_lifecycle_documents(documents) == s07_state(
        documents.status_text
    )


def test_m3_s07_lifecycle_state_vocabulary_is_closed() -> None:
    with pytest.raises(ValueError, match="missing or unsupported"):
        s07_state(
            "**Milestone status:** ACTIVE — FINAL ACCEPTANCE REVIEW — M3-S07 ACCEPTED"
        )


@pytest.mark.parametrize(
    ("documents", "message"),
    [
        (
            S07LifecycleDocuments(
                _status("CANDIDATE READY FOR REVIEW", "AUTHORIZED — M3-S07 ONLY"),
                REVIEW_ACCEPTANCE,
                True,
                REVIEW_PROMPTS,
            ),
            "Candidate",
        ),
        (
            S07LifecycleDocuments(
                _status("COMPLETED", "AUTHORIZED — M3-S07 ONLY"),
                COMPLETED_ACCEPTANCE,
                True,
                frozenset(),
            ),
            "NOT AUTHORIZED",
        ),
        (
            S07LifecycleDocuments(
                _status("COMPLETED", "NOT AUTHORIZED"),
                COMPLETED_ACCEPTANCE,
                True,
                frozenset({ORIGINAL_PROMPT}),
            ),
            "retired",
        ),
        (
            S07LifecycleDocuments(
                _status("COMPLETED", "NOT AUTHORIZED"),
                CANDIDATE_ACCEPTANCE,
                True,
                frozenset(),
            ),
            "Review",
        ),
    ],
    ids=(
        "stale-review-summary",
        "completed-still-authorized",
        "completed-stale-aid",
        "completed-stale-candidate-summary",
    ),
)
def test_m3_s07_lifecycle_rejects_incoherent_state_matrix(
    documents: S07LifecycleDocuments,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        validate_s07_lifecycle_documents(documents)


def test_m3_s07_repository_follows_current_lifecycle() -> None:
    assert validate_repository_lifecycle() in {
        "IN PROGRESS",
        "CANDIDATE READY FOR REVIEW",
        "REVIEW CHANGES REQUIRED",
        "COMPLETED",
    }


def test_m3_s07_mapped_targets_are_exactly_registry_derived() -> None:
    assert M3_EVIDENCE_BUNDLES == EXPECTED_M3_EVIDENCE_BUNDLES
    assert set(M3_EVIDENCE_TO_TARGETS) == EXPECTED_M3_EVIDENCE_BUNDLES
    assert all(M3_EVIDENCE_TO_TARGETS.values())
    assert M3_MAPPED_TARGETS == frozenset(
        target for targets in M3_EVIDENCE_TO_TARGETS.values() for target in targets
    )


def _junit_case(name: str, child: str = "") -> bytes:
    return (
        '<testsuite tests="1"><testcase classname="tests.test_example" '
        f'name="{name}">{child}</testcase></testsuite>'
    ).encode()


@pytest.mark.parametrize(
    ("child", "output", "field"),
    [
        ("<failure />", "1 failed", "failed"),
        ("<error />", "1 error", "errors"),
        ("<skipped />", "1 skipped", "skipped"),
        ('<skipped type="pytest.xfail" />', "1 xfailed", "xfailed"),
        ("<flakyFailure />", "1 rerun", "rerun"),
    ],
    ids=("failure", "error", "skip", "xfail", "rerun"),
)
def test_m3_s07_junit_parser_rejects_every_nonpass_case(
    child: str,
    output: str,
    field: str,
) -> None:
    target = "tests/test_example.py::test_case"
    parsed = parse_mapped_target_junit(
        _junit_case("test_case", child),
        requested_targets=frozenset({target}),
        pytest_exit_status=0,
        duration_seconds=1.0,
        output=output,
    )
    assert getattr(parsed.census, field) == 1
    assert parsed.target_states[target] == "FAIL"
    assert mapped_gate_exit_status(parsed) == 1


def test_m3_s07_junit_parser_handles_parametrized_nodes_and_missing_targets() -> None:
    target = "tests/test_example.py::test_case"
    parsed = parse_mapped_target_junit(
        _junit_case("test_case[value]"),
        requested_targets=frozenset({target}),
        pytest_exit_status=0,
        duration_seconds=1.0,
        output="1 passed",
    )
    assert parsed.census.concrete_cases == 1
    assert parsed.census.passed == 1
    assert parsed.census.missing_targets == 0
    assert parsed.target_states[target] == "PASS"

    missing = parse_mapped_target_junit(
        _junit_case("test_other"),
        requested_targets=frozenset({target}),
        pytest_exit_status=0,
        duration_seconds=1.0,
        output="1 passed",
    )
    assert missing.census.missing_targets == 1
    assert missing.target_states[target] == "MISSING"
    assert mapped_gate_exit_status(missing) == 1


def test_m3_s07_mapped_gate_rejects_pytest_exit_and_xpass() -> None:
    census = MappedTargetCensus(19, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0)
    passing = ParsedMappedTargetRun(
        0,
        1.0,
        census,
        {"target": "PASS"},
        {bundle: "PASS" for bundle in EXPECTED_M3_EVIDENCE_BUNDLES},
        "",
    )
    assert mapped_gate_exit_status(passing) == 0
    assert mapped_gate_exit_status(replace(passing, pytest_exit_status=2)) == 2
    assert (
        mapped_gate_exit_status(replace(passing, census=replace(census, xpassed=1)))
        == 1
    )
