"""Cheap S04 layer and hard-scope regressions."""

from dataclasses import fields
from pathlib import Path
from typing import cast

from netauto.domain.objects import Object
from netauto.entrypoints.http import build_app
from netauto.settings import Settings

ROOT = Path(__file__).parents[1]


def test_object_intrinsic_snapshot_has_only_frozen_fields() -> None:
    assert [field.name for field in fields(Object)] == [
        "id",
        "canonical_name",
        "template_id",
        "template_version",
        "properties",
    ]


def test_object_domain_and_application_preserve_layer_boundaries() -> None:
    for relative in (
        "src/netauto/domain/objects.py",
        "src/netauto/application/objects.py",
    ):
        source = (ROOT / relative).read_text()
        assert "sqlalchemy" not in source
        assert "fastapi" not in source
        assert "pydantic" not in source
        assert "Session" not in source
        assert "state_revision" not in source
        assert "JSON Schema" not in source


def test_s04_registers_only_intrinsic_object_capabilities() -> None:
    app = build_app(Settings(database_url="postgresql+psycopg://u:p@localhost/db"))
    schema = cast(dict[str, object], app.openapi())
    paths = cast(dict[str, object], schema["paths"])
    expected = {
        "/api/v1/core/objects",
        "/api/v1/core/objects/{object_id}",
        "/api/v1/core/objects/{object_id}/rename",
        "/api/v1/core/objects/{object_id}/data-change",
        "/api/v1/core/lifecycle-events",
        "/api/v1/core/objects/{object_id}/lifecycle-events",
    }
    assert expected <= set(paths)
    for suffix in (
        "/schema-change",
        "/attach",
        "/detach",
        "/components",
        "/owner",
        "/relationships",
    ):
        assert not any(path.endswith(suffix) for path in paths)
    object_methods = cast(dict[str, object], paths["/api/v1/core/objects/{object_id}"])
    assert "delete" not in object_methods
