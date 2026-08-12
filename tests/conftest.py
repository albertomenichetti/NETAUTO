from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-postgresql",
        action="store_true",
        default=False,
        help="run tests that require a real PostgreSQL instance via TEST_DATABASE_URL",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-postgresql"):
        return

    skip_postgresql = pytest.mark.skip(
        reason="postgresql tests are disabled by default; use --run-postgresql",
    )
    for item in items:
        if "postgresql" in item.keywords:
            item.add_marker(skip_postgresql)
