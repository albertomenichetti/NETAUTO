"""Pure strict grammar, codec, endpoint, and local-error evidence."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from netauto.cli.model import CommandKey
from netauto.cli.parser import ParseFailure, normalize_endpoint_root, parse_process


@pytest.mark.parametrize(
    ("raw", "normalized"),
    [
        ("HTTP://Example.TEST/", "http://example.test"),
        ("http://example.test", "http://example.test"),
        ("http://example.test:1", "http://example.test:1"),
        ("https://example.test:65535/", "https://example.test:65535"),
        ("https://[2001:db8::10]", "https://[2001:db8::10]"),
        ("https://example.test:8443", "https://example.test:8443"),
        ("https://[2001:db8::10]:8443/", "https://[2001:db8::10]:8443"),
    ],
)
def test_endpoint_root_normalization(raw: str, normalized: str) -> None:
    assert normalize_endpoint_root(raw) == normalized


@pytest.mark.parametrize(
    "raw",
    [
        "example.test",
        "ftp://example.test",
        "https://user:secret@example.test",
        "https://example.test/api/v1/core",
        "https://example.test?profile=x",
        "https://example.test#fragment",
    ],
)
def test_endpoint_root_rejects_non_root_or_credential_surface(raw: str) -> None:
    with pytest.raises(ParseFailure) as caught:
        normalize_endpoint_root(raw)
    assert caught.value.error.code == "cli_invalid_invocation"
    assert "secret" not in str(caught.value.error.as_json())


@pytest.mark.parametrize(
    "raw",
    [
        "http://example.test:",
        "http://example.test:/",
        "https://[2001:db8::10]:",
        "https://[2001:db8::10]:/",
        "http://example.test:0",
        "http://example.test:65536",
        "http://example.test:+80",
        "http://example.test:-1",
        "http://example.test:abc",
        "https://[2001:db8::10]:0",
        "https://[2001:db8::10]:65536",
        "https://[2001:db8::10]:+443",
        "https://[2001:db8::10]:abc",
    ],
)
def test_endpoint_root_rejects_every_malformed_explicit_port(raw: str) -> None:
    with pytest.raises(ParseFailure) as caught:
        normalize_endpoint_root(raw)
    result = caught.value.error.as_json()
    assert result["code"] == "cli_invalid_invocation"
    assert raw not in str(result)


def test_parser_preserves_original_typed_human_intent() -> None:
    endpoint, command, spec = parse_process(
        [
            "-n",
            "http://example.test/",
            "object",
            "create",
            "template_id=infra.vm",
            "template_version=2",
            "canonical_name=server 01",
            'properties={"cpu":4}',
        ]
    )
    assert endpoint == "http://example.test"
    assert command.key == CommandKey("object", "create")
    assert command.selector is None
    assert command.parameters == {
        "template_id": "infra.vm",
        "template_version": 2,
        "canonical_name": "server 01",
        "properties": {"cpu": 4},
    }
    assert spec is not None


def test_json_file_is_read_as_utf8_once(tmp_path: Path) -> None:
    path = tmp_path / "properties.json"
    path.write_text(json.dumps({"cpu": 4}), encoding="utf-8")
    _, command, _ = parse_process(
        [
            "-n",
            "http://example.test",
            "object",
            "create",
            "template_id=infra.vm",
            f"properties=@{path}",
        ]
    )
    assert command.parameters["properties"] == {"cpu": 4}

    with (
        patch("netauto.cli.parser.Path.is_file", return_value=True),
        patch("netauto.cli.parser.Path.read_text", return_value='{"memory":8}') as read,
    ):
        _, reread_command, _ = parse_process(
            [
                "-n",
                "http://example.test",
                "object",
                "create",
                "template_id=infra.vm",
                "properties=@logical.json",
            ]
        )
    read.assert_called_once_with(encoding="utf-8")
    assert reread_command.parameters["properties"] == {"memory": 8}


def test_simple_carrier_and_closed_enum_matrix() -> None:
    _, created, _ = parse_process(
        [
            "-n",
            "http://example.test",
            "datatype",
            "create",
            "namespace=core",
            "name=custom",
            "base_type=core.string",
            "description=example",
            "constraints={}",
        ]
    )
    assert created.parameters == {
        "namespace": "core",
        "name": "custom",
        "base_type": "core.string",
        "description": "example",
        "constraints": {},
    }

    _, template, _ = parse_process(
        [
            "-n",
            "http://example.test",
            "object-template",
            "create",
            "namespace=infra",
            "name=vm",
            "abstract=true",
            "properties=[]",
            "components=[]",
        ]
    )
    assert template.parameters["abstract"] is True
    assert template.parameters["properties"] == []

    _, lifecycle, _ = parse_process(
        [
            "-n",
            "http://example.test",
            "lifecycle-event",
            "list",
            "kind=CREATED",
            "occurred_from=2026-08-18T00:00:00Z",
        ]
    )
    assert lifecycle.parameters == {
        "kind": "CREATED",
        "occurred_from": "2026-08-18T00:00:00Z",
    }


@pytest.mark.parametrize(
    ("value", "code"),
    [
        ("properties={invalid", "cli_json_error"),
        ("properties=@missing.json", "cli_file_error"),
    ],
)
def test_structured_parameter_failures_are_finite(value: str, code: str) -> None:
    with pytest.raises(ParseFailure) as caught:
        parse_process(
            [
                "-n",
                "http://example.test",
                "object",
                "create",
                "template_id=infra.vm",
                value,
            ]
        )
    assert caught.value.error.code == code


@pytest.mark.parametrize(
    ("argv", "code"),
    [
        ([], "cli_invalid_invocation"),
        (["--non-interactive", "x", "datatype", "list"], "cli_invalid_invocation"),
        (["-n", "http://x", "datatypes", "list"], "cli_invalid_command"),
        (["-n", "http://x", "datatype", "get"], "cli_missing_selector"),
        (
            ["-n", "http://x", "datatype", "list", "unexpected"],
            "cli_unexpected_selector",
        ),
        (
            ["-n", "http://x", "datatype", "list", "unknown=x"],
            "cli_unexpected_parameter",
        ),
        (
            ["-n", "http://x", "datatype", "list", "limit=1", "limit=2"],
            "cli_duplicate_parameter",
        ),
        (
            ["-n", "http://x", "datatype", "list", "limit=true"],
            "cli_invalid_parameter",
        ),
        (
            ["-n", "http://x", "datatype", "create", "namespace=x"],
            "cli_missing_parameter",
        ),
        (
            [
                "-n",
                "http://x",
                "relationship-definition",
                "create",
                "symmetric=false",
                "endpoint_template_ids=[]",
            ],
            "cli_invalid_parameter",
        ),
        (
            ["-n", "http://x", "lifecycle-event", "list", "kind=UNKNOWN"],
            "cli_invalid_parameter",
        ),
        (
            [
                "-n",
                "http://x",
                "lifecycle-event",
                "list",
                "occurred_from=not-a-datetime",
            ],
            "cli_invalid_parameter",
        ),
        (
            [
                "-n",
                "http://x",
                "object-template",
                "create",
                "namespace=infra",
                "name=vm",
                "abstract=1",
            ],
            "cli_invalid_parameter",
        ),
    ],
)
def test_finite_local_parse_failures(argv: list[str], code: str) -> None:
    with pytest.raises(ParseFailure) as caught:
        parse_process(argv)
    assert caught.value.error.code == code
    assert caught.value.error.source in {"local", "selector"}


def test_nullable_string_distinguishes_null_from_literal_null() -> None:
    _, null_command, _ = parse_process(
        [
            "-n",
            "http://x",
            "datatype",
            "set-description",
            "11111111-1111-1111-1111-111111111111",
            "description=null",
        ]
    )
    _, string_command, _ = parse_process(
        [
            "-n",
            "http://x",
            "datatype",
            "set-description",
            "11111111-1111-1111-1111-111111111111",
            'description="null"',
        ]
    )
    assert null_command.parameters["description"] is None
    assert string_command.parameters["description"] == "null"
