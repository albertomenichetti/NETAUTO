"""Project-wide pytest fixtures."""

from collections import Counter
from collections.abc import Iterator
from typing import cast

import pytest
from _pytest.nodes import Item
from _pytest.terminal import TerminalReporter
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine

from tests.support.postgresql import (
    TestDatabaseConfigurationError,
    load_test_database_url,
)
from tests.support.s07_release import InstalledRelease, create_installed_release


@pytest.fixture(scope="session")
def s07_release(tmp_path_factory: pytest.TempPathFactory) -> InstalledRelease:
    """Build and install the exact M2-S07 candidate once for T9 targets."""
    return create_installed_release(tmp_path_factory.mktemp("m2-s07-target"))


@pytest.fixture
def test_database_url() -> str:
    """Return the externally supplied PostgreSQL target or fail explicitly."""
    try:
        return load_test_database_url()
    except TestDatabaseConfigurationError as error:
        failure_message = str(error)

    pytest.fail(failure_message, pytrace=False)


@pytest.fixture
def migrated_database_engine(test_database_url: str) -> Iterator[Engine]:
    """Upgrade the externally supplied target for one non-parallel PG test."""
    engine = create_engine(test_database_url)
    config = Config("alembic.ini")
    with engine.connect() as connection:
        config.attributes["connection"] = connection
        command.downgrade(config, "base")
        command.upgrade(config, "head")
    try:
        yield engine
    finally:
        with engine.connect() as connection:
            config.attributes["connection"] = connection
            command.downgrade(config, "base")
        engine.dispose()


@pytest.fixture(autouse=True)
def canonical_t3_workers_use_structured_outcomes(
    request: pytest.FixtureRequest,
) -> Iterator[None]:
    """Reject canonical T3 targets that bypass the structured worker ledger."""
    node = cast(Item, request.node)  # pyright: ignore[reportUnknownMemberType]
    if "postgresql" not in node.keywords or "concurrency" not in node.keywords:
        yield
        return

    from tests.support.semantic_concurrency import worker_outcomes_for_node
    from tests.test_m2_traceability import M2_SCENARIO_TO_TARGETS

    node_id = node.nodeid
    scenario_targets = M2_SCENARIO_TO_TARGETS
    mapped_scenarios = frozenset(
        scenario_id
        for scenario_id, targets in scenario_targets.items()
        if any(
            node_id == target or node_id.startswith(f"{target}[") for target in targets
        )
    )
    mapped = bool(mapped_scenarios)
    before = len(worker_outcomes_for_node(node_id))
    yield
    if mapped:
        captured = worker_outcomes_for_node(node_id)[before:]
        assert captured, (
            f"canonical T3 target bypassed worker outcome ledger: {node_id}"
        )
        assert all(outcome.role in {"B", "T1", "T2", "T3"} for outcome in captured)
        assert all(
            outcome.pytest_node_id == node_id
            and outcome.last_phase
            and outcome.transaction_outcome in {"COMMITTED", "ROLLED_BACK", "NO_UOW"}
            and outcome.sqlstate not in {"40P01", "40001"}
            for outcome in captured
        )
        represented = frozenset(
            scenario_id for outcome in captured for scenario_id in outcome.scenario_ids
        )
        assert mapped_scenarios <= represented, (
            f"canonical scenarios missing from worker ledger for {node_id}: "
            f"{sorted(mapped_scenarios - represented)}"
        )


def pytest_terminal_summary(
    terminalreporter: TerminalReporter,
    exitstatus: int,
    config: pytest.Config,
) -> None:
    del exitstatus, config
    from tests.support.semantic_concurrency import session_worker_outcomes
    from tests.test_m2_traceability import M2_SCENARIO_TO_TARGETS

    outcomes = session_worker_outcomes()
    if not outcomes:
        return
    canonical_targets = frozenset(
        target for targets in M2_SCENARIO_TO_TARGETS.values() for target in targets
    )
    canonical = tuple(
        item
        for item in outcomes
        if not item.negative_control
        and any(
            item.pytest_node_id == target
            or item.pytest_node_id.startswith(f"{target}[")
            for target in canonical_targets
        )
    )
    ancillary = tuple(
        item for item in outcomes if not item.negative_control and item not in canonical
    )
    negative = tuple(item for item in outcomes if item.negative_control)
    transaction_counts = Counter(item.transaction_outcome for item in canonical)
    sqlstates = Counter(
        item.sqlstate for item in canonical if item.sqlstate is not None
    )
    negative_sqlstates = Counter(
        item.sqlstate for item in negative if item.sqlstate is not None
    )
    represented_scenarios = frozenset(
        scenario_id for item in canonical for scenario_id in item.scenario_ids
    )
    canonical_sqlstate_details = Counter(
        (
            tuple(sorted(item.scenario_ids)),
            item.pytest_node_id,
            item.role,
            item.sqlstate,
        )
        for item in canonical
        if item.sqlstate is not None
    )
    negative_sqlstate_details = Counter(
        (item.pytest_node_id, item.role, item.sqlstate)
        for item in negative
        if item.sqlstate is not None
    )
    terminalreporter.write_sep("-", "M2 structured worker outcome census")
    terminalreporter.write_line(f"canonical semantic-worker outcomes: {len(canonical)}")
    terminalreporter.write_line(
        f"noncanonical focused/ancillary outcomes: {len(ancillary)}"
    )
    terminalreporter.write_line(
        f"canonical scenario IDs represented: {len(represented_scenarios)}"
    )
    terminalreporter.write_line(
        f"transaction outcomes: {dict(sorted(transaction_counts.items()))}"
    )
    terminalreporter.write_line(f"SQLSTATE values: {dict(sorted(sqlstates.items()))}")
    terminalreporter.write_line(
        "supported-path 40P01 count: "
        f"{sum(item.sqlstate == '40P01' for item in canonical)}; "
        "unexpected 40001 count: "
        f"{sum(item.sqlstate == '40001' for item in canonical)}"
    )
    for (scenarios, node_id, role, sqlstate), count in sorted(
        canonical_sqlstate_details.items()
    ):
        terminalreporter.write_line(
            "canonical SQLSTATE detail: "
            f"scenarios={','.join(scenarios) or '<none>'}; node={node_id}; "
            f"role={role}; state={sqlstate}; count={count}"
        )
    terminalreporter.write_line(
        f"negative-control outcomes: {len(negative)}; "
        f"SQLSTATE values: {dict(sorted(negative_sqlstates.items()))}"
    )
    for (node_id, role, sqlstate), count in sorted(negative_sqlstate_details.items()):
        terminalreporter.write_line(
            "negative-control SQLSTATE detail: "
            f"node={node_id}; role={role}; state={sqlstate}; count={count}"
        )
