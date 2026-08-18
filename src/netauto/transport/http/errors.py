"""Canonical public business-error wire DTO."""

from pydantic import BaseModel, ConfigDict

from netauto.domain.primitives import JsonValue

PUBLIC_STATUS_BY_CODE = {
    "invalid_request": 400,
    "invalid_cursor": 400,
    "resource_not_found": 404,
    "referenced_resource_not_found": 422,
    "semantic_validation_failed": 422,
    "stale_revision": 409,
    "lifecycle_state_conflict": 409,
    "version_source_conflict": 409,
    "default_version_unavailable": 409,
    "dependency_not_admissible": 409,
    "qualified_name_conflict": 409,
    "default_version_conflict": 409,
    "active_dependency_conflict": 409,
    "delete_blocked": 409,
    "ownership_slot_unavailable": 409,
    "ownership_conflict": 409,
    "ownership_mismatch": 409,
    "ownership_cycle": 409,
    "schema_change_blocked": 409,
    "relationship_definition_equivalent": 409,
    "relationship_definition_conflict": 409,
    "relationship_fact_conflict": 409,
    "internal_error": 500,
}


class BusinessErrorDTO(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    code: str
    message: str
    details: dict[str, JsonValue]
