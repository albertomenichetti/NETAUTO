from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-sqlite-legacy",
        action="store_true",
        default=False,
        help="run transitional SQLite legacy integration and characterization tests",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        if "sqlite_legacy" not in item.keywords:
            continue
        if config.getoption("--run-sqlite-legacy"):
            continue
        item.add_marker(
            pytest.mark.skip(
                reason=(
                    "sqlite_legacy tests are disabled by default; "
                    "use --run-sqlite-legacy"
                ),
            )
        )
