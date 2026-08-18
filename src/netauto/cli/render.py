"""Exact non-interactive JSON rendering."""

import json

from netauto.cli.model import CliResult


def render_json(result: CliResult) -> str:
    return (
        json.dumps(result.as_json(), separators=(",", ":"), ensure_ascii=False) + "\n"
    )
