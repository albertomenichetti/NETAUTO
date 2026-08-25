"""Finite M3 traceability and public-surface evidence registries."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetRouteEvidence:
    """One canonical M3 business GET and its public top-level shape."""

    method: str
    path: str
    fields: frozenset[str]


@dataclass(frozen=True, slots=True)
class CursorRouteEvidence:
    """One frozen ADP-04 cursor identity and complete keyset shape."""

    path: str
    codec_route: str
    filters: tuple[str, ...]
    position: tuple[str, ...]
    order: str


M3_OUTCOMES = frozenset(f"M3-OUT-{number:02d}" for number in range(1, 9))
M3_ACCEPTANCE_CRITERIA = frozenset(f"M3-AC-{number:02d}" for number in range(1, 20))
M3_EVIDENCE_BUNDLES = frozenset(f"M3-VER-{number:02d}" for number in range(1, 20))
M3_CONTRACT_QUALITY_GATES = frozenset(f"M3-CQG-{number:02d}" for number in range(1, 9))

M3_OUTCOME_TO_ACCEPTANCE = {
    "M3-OUT-01": frozenset({"M3-AC-01", "M3-AC-03"}),
    "M3-OUT-02": frozenset({"M3-AC-02"}),
    "M3-OUT-03": frozenset({"M3-AC-06", "M3-AC-07"}),
    "M3-OUT-04": frozenset({"M3-AC-04", "M3-AC-05", "M3-AC-19"}),
    "M3-OUT-05": frozenset({f"M3-AC-{number:02d}" for number in range(9, 14)}),
    "M3-OUT-06": frozenset({"M3-AC-08"}),
    "M3-OUT-07": frozenset({f"M3-AC-{number:02d}" for number in range(14, 17)}),
    "M3-OUT-08": frozenset({"M3-AC-17", "M3-AC-18"}),
}

M3_ACCEPTANCE_TO_EVIDENCE = {
    f"M3-AC-{number:02d}": f"M3-VER-{number:02d}" for number in range(1, 20)
}

_READ_OWNER = "docs/milestones/M3/architecture/read-projections.md"
_API_OWNER = "docs/milestones/M3/architecture/api.md"
_CLI_OWNER = "docs/milestones/M3/architecture/cli.md"
_VERIFICATION_OWNER = "docs/milestones/M3/architecture/verification.md"
_AS_IS_API_OWNER = "docs/architecture/api.md"
_AS_IS_PERSISTENCE_OWNER = "docs/architecture/persistence.md"
_AS_IS_VERIFICATION_OWNER = "docs/architecture/verification.md"

M3_EVIDENCE_TO_ARCHITECTURE_OWNER = {
    "M3-VER-01": frozenset({_CLI_OWNER}),
    "M3-VER-02": frozenset({_CLI_OWNER}),
    "M3-VER-03": frozenset({_CLI_OWNER}),
    "M3-VER-04": frozenset({_READ_OWNER, _AS_IS_API_OWNER}),
    "M3-VER-05": frozenset({_READ_OWNER, _AS_IS_API_OWNER}),
    "M3-VER-06": frozenset({_READ_OWNER}),
    "M3-VER-07": frozenset({_READ_OWNER}),
    "M3-VER-08": frozenset({_READ_OWNER}),
    "M3-VER-09": frozenset({_API_OWNER}),
    "M3-VER-10": frozenset({_API_OWNER}),
    "M3-VER-11": frozenset({_API_OWNER}),
    "M3-VER-12": frozenset({_API_OWNER, _READ_OWNER}),
    "M3-VER-13": frozenset({_API_OWNER}),
    "M3-VER-14": frozenset({_API_OWNER}),
    "M3-VER-15": frozenset({_CLI_OWNER}),
    "M3-VER-16": frozenset({_API_OWNER}),
    "M3-VER-17": frozenset(
        {_VERIFICATION_OWNER, _AS_IS_PERSISTENCE_OWNER, _AS_IS_VERIFICATION_OWNER}
    ),
    "M3-VER-18": frozenset({_VERIFICATION_OWNER}),
    "M3-VER-19": frozenset(
        {_READ_OWNER, _VERIFICATION_OWNER, _AS_IS_VERIFICATION_OWNER}
    ),
}

M3_GET_ROUTE_CENSUS = {
    "DT-GET-01": GetRouteEvidence(
        "GET", "/api/v1/core/datatypes", frozenset({"items", "next_cursor"})
    ),
    "DT-GET-02": GetRouteEvidence(
        "GET",
        "/api/v1/core/datatypes/{datatype_id}",
        frozenset({"id", "namespace", "name", "description", "default_version"}),
    ),
    "DT-GET-03": GetRouteEvidence(
        "GET",
        "/api/v1/core/datatypes/{datatype_id}/versions",
        frozenset({"items", "next_cursor"}),
    ),
    "DT-GET-04": GetRouteEvidence(
        "GET",
        "/api/v1/core/datatypes/{datatype_id}/versions/{version}",
        frozenset(
            {"datatype_id", "version", "revision", "status", "base_type", "constraints"}
        ),
    ),
    "OT-GET-01": GetRouteEvidence(
        "GET", "/api/v1/core/object-templates", frozenset({"items", "next_cursor"})
    ),
    "OT-GET-02": GetRouteEvidence(
        "GET",
        "/api/v1/core/object-templates/{template_id}",
        frozenset(
            {
                "id",
                "namespace",
                "name",
                "description",
                "abstract",
                "parent_template_id",
                "default_version",
            }
        ),
    ),
    "OT-GET-03": GetRouteEvidence(
        "GET",
        "/api/v1/core/object-templates/{template_id}/versions",
        frozenset({"items", "next_cursor"}),
    ),
    "OT-GET-04": GetRouteEvidence(
        "GET",
        "/api/v1/core/object-templates/{template_id}/versions/{version}",
        frozenset(
            {
                "template_id",
                "version",
                "revision",
                "status",
                "parent_template_id",
                "parent_version",
                "properties",
                "components",
            }
        ),
    ),
    "OT-GET-05": GetRouteEvidence(
        "GET",
        "/api/v1/core/object-templates/{template_id}/versions/{version}/effective-schema",
        frozenset({"template_id", "version", "properties", "components"}),
    ),
    "OT-GET-06": GetRouteEvidence(
        "GET",
        "/api/v1/core/object-templates/{template_id}/relationship-capabilities",
        frozenset({"items", "next_cursor"}),
    ),
    "OBJ-GET-01": GetRouteEvidence(
        "GET", "/api/v1/core/objects", frozenset({"items", "next_cursor"})
    ),
    "OBJ-GET-02": GetRouteEvidence(
        "GET",
        "/api/v1/core/objects/{object_id}",
        frozenset(
            {"id", "canonical_name", "template_id", "template_version", "properties"}
        ),
    ),
    "OBJ-GET-03": GetRouteEvidence(
        "GET",
        "/api/v1/core/objects/{parent_object_id}/components",
        frozenset({"items", "next_cursor"}),
    ),
    "OBJ-GET-04": GetRouteEvidence(
        "GET",
        "/api/v1/core/objects/{child_object_id}/owner",
        frozenset({"parent_object_id", "slot_declaring_template_id", "slot_name"}),
    ),
    "OBJ-GET-05": GetRouteEvidence(
        "GET",
        "/api/v1/core/objects/{object_id}/lifecycle-events",
        frozenset({"items", "next_cursor"}),
    ),
    "OBJ-GET-06": GetRouteEvidence(
        "GET",
        "/api/v1/core/objects/{object_id}/relationships",
        frozenset({"items", "next_cursor"}),
    ),
    "RD-GET-01": GetRouteEvidence(
        "GET",
        "/api/v1/core/relationship-definitions",
        frozenset({"items", "next_cursor"}),
    ),
    "RD-GET-02": GetRouteEvidence(
        "GET",
        "/api/v1/core/relationship-definitions/{relationship_definition_id}",
        frozenset({"id", "symmetric", "default_version", "resolutions"}),
    ),
    "RD-GET-03": GetRouteEvidence(
        "GET",
        "/api/v1/core/relationship-definitions/{relationship_definition_id}/versions",
        frozenset({"items", "next_cursor"}),
    ),
    "RD-GET-04": GetRouteEvidence(
        "GET",
        "/api/v1/core/relationship-definitions/{relationship_definition_id}/versions/{version}",
        frozenset(
            {
                "relationship_definition_id",
                "version",
                "revision",
                "status",
                "properties",
            }
        ),
    ),
    "REL-GET-01": GetRouteEvidence(
        "GET",
        "/api/v1/core/relationships/{relationship_id}",
        frozenset(
            {
                "id",
                "relationship_definition_id",
                "relationship_definition_version",
                "properties",
                "views",
            }
        ),
    ),
    "LC-GET-01": GetRouteEvidence(
        "GET", "/api/v1/core/lifecycle-events", frozenset({"items", "next_cursor"})
    ),
}

_LIFECYCLE_FILTERS = (
    "kind",
    "object_id",
    "destination_object_id",
    "relationship_id",
    "relationship_definition_id",
    "relationship_name",
    "occurred_from",
    "occurred_to",
    "involving_object_id",
)

M3_CURSOR_ROUTE_CENSUS = {
    "DT-GET-01": CursorRouteEvidence(
        "/api/v1/core/datatypes",
        "datatypes",
        ("namespace", "name"),
        ("namespace", "name"),
        "ASC",
    ),
    "DT-GET-03": CursorRouteEvidence(
        "/api/v1/core/datatypes/{datatype_id}/versions",
        "datatype_versions",
        ("datatype_id", "status"),
        ("version",),
        "ASC",
    ),
    "OT-GET-01": CursorRouteEvidence(
        "/api/v1/core/object-templates",
        "object_templates",
        (
            "namespace",
            "name",
            "abstract",
            "parent_template_id",
            "parent_filter_set",
        ),
        ("namespace", "name"),
        "ASC",
    ),
    "OT-GET-03": CursorRouteEvidence(
        "/api/v1/core/object-templates/{template_id}/versions",
        "object_template_versions",
        ("template_id", "status"),
        ("version",),
        "ASC",
    ),
    "OT-GET-06": CursorRouteEvidence(
        "/api/v1/core/object-templates/{template_id}/relationship-capabilities",
        "relationship_capabilities",
        ("template_id", "name"),
        ("resolution_id",),
        "ASC",
    ),
    "OBJ-GET-01": CursorRouteEvidence(
        "/api/v1/core/objects",
        "objects",
        ("template_id", "template_version", "canonical_name"),
        ("id",),
        "ASC",
    ),
    "OBJ-GET-03": CursorRouteEvidence(
        "/api/v1/core/objects/{parent_object_id}/components",
        "object_components",
        ("parent_object_id", "slot_name"),
        ("child_object_id",),
        "ASC",
    ),
    "OBJ-GET-06": CursorRouteEvidence(
        "/api/v1/core/objects/{object_id}/relationships",
        "object_relationships",
        ("object_id", "relationship_definition_id", "name"),
        ("relationship_id", "destination_object_id", "name"),
        "ASC",
    ),
    "OBJ-GET-05": CursorRouteEvidence(
        "/api/v1/core/objects/{object_id}/lifecycle-events",
        "lifecycle_events",
        _LIFECYCLE_FILTERS,
        ("occurred_at", "id"),
        "DESC",
    ),
    "RD-GET-01": CursorRouteEvidence(
        "/api/v1/core/relationship-definitions",
        "relationship_definitions",
        (),
        ("id",),
        "ASC",
    ),
    "RD-GET-03": CursorRouteEvidence(
        "/api/v1/core/relationship-definitions/{relationship_definition_id}/versions",
        "relationship_definition_versions",
        ("definition_id", "status"),
        ("version",),
        "ASC",
    ),
    "LC-GET-01": CursorRouteEvidence(
        "/api/v1/core/lifecycle-events",
        "lifecycle_events",
        _LIFECYCLE_FILTERS,
        ("occurred_at", "id"),
        "DESC",
    ),
}

M3_CLI_201_CENSUS = frozenset(
    {
        ("datatype", "create"),
        ("datatype", "create-next"),
        ("object-template", "create"),
        ("object-template", "create-next"),
        ("object", "create"),
        ("relationship-definition", "create"),
        ("relationship-definition", "create-next"),
        ("relationship", "create"),
    }
)

M3_CONTRACT_QUALITY_GATE_TO_OWNERS = {
    "M3-CQG-01": frozenset({"docs/milestones/M3/contract.md"}),
    "M3-CQG-02": frozenset({"docs/milestones/M3/contract.md"}),
    "M3-CQG-03": frozenset(
        {"docs/milestones/M3/contract.md", "docs/milestones/M3/architecture/README.md"}
    ),
    "M3-CQG-04": frozenset({_API_OWNER}),
    "M3-CQG-05": frozenset({_READ_OWNER}),
    "M3-CQG-06": frozenset({_API_OWNER, _CLI_OWNER}),
    "M3-CQG-07": frozenset(
        {"docs/milestones/M3/contract.md", "docs/milestones/M3/architecture/README.md"}
    ),
    "M3-CQG-08": frozenset(
        {"docs/milestones/M3/contract.md", "docs/milestones/M3/status.md"}
    ),
}

M3_EVIDENCE_TO_TARGETS = {
    "M3-VER-01": frozenset(
        {
            "tests/test_m3_s00_cli_location.py::test_m3_ver_01_registry_and_location_dsl_census_is_exact",
            "tests/test_m3_s00_cli_location.py::test_m3_ver_01_all_canonical_carriers_materialize_exact_locations",
            "tests/test_m3_s00_cli_location.py::test_m3_ver_01_all_canonical_201_responses_are_successes",
        }
    ),
    "M3-VER-02": frozenset(
        {
            "tests/test_m3_s00_cli_location.py::test_m3_ver_02_closed_location_dsl_rejects_malformed_classes",
            "tests/test_m3_s00_cli_location.py::test_m3_ver_02_request_presence_precedes_response_fallback",
            "tests/test_m3_s00_cli_location.py::test_m3_ver_02_actual_location_failures_are_protocol_errors",
        }
    ),
    "M3-VER-03": frozenset(
        {
            "tests/test_m3_s00_cli_location.py::test_m3_ver_03_noninteractive_nested_create_is_truthful_and_primary_only",
            "tests/test_m3_s00_cli_location.py::test_m3_ver_03_interactive_nested_create_is_truthful_and_primary_only",
        }
    ),
    "M3-VER-04": frozenset(
        {
            "tests/test_m3_s06_integration.py::test_m3_ver_04_05_integrated_success_and_failure_matrix",
            "tests/test_m3_s02_datatype_reads.py::test_m3_s02_trusted_reads_preserve_persisted_surprises_and_writes_reject",
            "tests/test_m3_s03_objecttemplate_reads.py::test_m3_s03_exact_aggregate_keeps_independent_ordered_child_sets",
            "tests/test_m3_s04_object_reads.py::test_m3_s04_object_list_and_exact_reads_trust_representable_state",
            "tests/test_m3_s05_relationship_reads.py::test_m3_s05_definition_root_pages_and_exact_reads_trust_aggregates",
        }
    ),
    "M3-VER-05": frozenset(
        {
            "tests/test_m3_s06_integration.py::test_m3_ver_04_05_integrated_success_and_failure_matrix",
            "tests/test_m3_s02_datatype_reads.py::test_m3_s02_request_and_path_target_failures_preserve_rp03_empty_page",
            "tests/test_m3_s04_object_reads.py::test_m3_s04_components_and_owner_context_cursor_and_failure_boundaries",
        }
    ),
    "M3-VER-06": frozenset(
        {
            "tests/test_m3_traceability.py::test_m3_ver_06_all_get_services_have_no_mutation_certification_dependencies",
            "tests/test_m3_s02_datatype_reads.py::test_m3_s02_trusted_reads_preserve_persisted_surprises_and_writes_reject",
            "tests/test_m3_s03_objecttemplate_reads.py::test_m3_s03_exact_pin_and_stable_ancestry_are_distinct_and_writes_stay_strong",
            "tests/test_m3_s04_object_reads.py::test_m3_s04_object_list_and_exact_reads_trust_representable_state",
            "tests/test_m3_s04_object_reads.py::test_m3_s04_components_and_owner_context_cursor_and_failure_boundaries",
            "tests/test_m3_s04_object_reads.py::test_m3_s04_object_relationship_page_deduplicates_and_binds_target",
            "tests/test_m3_s05_relationship_reads.py::test_m3_s05_definition_root_pages_and_exact_reads_trust_aggregates",
            "tests/test_m3_s05_relationship_reads.py::test_m3_s05_relationship_exact_trusts_facts_and_deduplicates_views",
            "tests/test_m3_s05_relationship_reads.py::test_m3_ver_07_08_13_lifecycle_boundaries_and_cursor_scope",
        }
    ),
    "M3-VER-07": frozenset(
        {
            "tests/test_m3_s04_object_reads.py::test_m3_s04_object_lifecycle_trusted_decoder_and_cursor_scope",
            "tests/test_m3_s05_relationship_reads.py::test_m3_ver_07_08_13_lifecycle_boundaries_and_cursor_scope",
        }
    ),
    "M3-VER-08": frozenset(
        {
            "tests/test_m3_s05_relationship_reads.py::test_m3_ver_07_08_13_lifecycle_boundaries_and_cursor_scope"
        }
    ),
    "M3-VER-09": frozenset(
        {
            "tests/test_m3_s06_integration.py::test_m3_ver_09_12_complete_cursor_matrix",
            "tests/test_m3_s01_parent_tristate.py::test_m3_ver_16_parent_cursor_identity_and_limit_compatibility",
            "tests/test_m3_s02_datatype_reads.py::test_m3_s02_datatype_cursors_traverse_and_bind_semantic_identity",
            "tests/test_m3_s03_objecttemplate_reads.py::test_m3_s03_three_cursor_routes_traverse_and_bind_query_identity",
            "tests/test_m3_s04_object_reads.py::test_m3_s04_components_and_owner_context_cursor_and_failure_boundaries",
            "tests/test_m3_s04_object_reads.py::test_m3_s04_object_relationship_page_deduplicates_and_binds_target",
            "tests/test_m3_s05_relationship_reads.py::test_m3_s05_definition_version_parent_cursor_and_trusted_history",
        }
    ),
    "M3-VER-10": frozenset(
        {
            "tests/test_m3_s04_object_reads.py::test_m3_s04_components_and_owner_context_cursor_and_failure_boundaries"
        }
    ),
    "M3-VER-11": frozenset(
        {
            "tests/test_m3_s04_object_reads.py::test_m3_s04_object_relationship_page_deduplicates_and_binds_target"
        }
    ),
    "M3-VER-12": frozenset(
        {"tests/test_m3_s06_integration.py::test_m3_ver_09_12_complete_cursor_matrix"}
    ),
    "M3-VER-13": frozenset(
        {
            "tests/test_m3_s05_relationship_reads.py::test_m3_ver_07_08_13_lifecycle_boundaries_and_cursor_scope"
        }
    ),
    "M3-VER-14": frozenset(
        {
            "tests/test_m3_s01_parent_tristate.py::test_m3_ver_14_http_parent_tristate_and_public_surface",
            "tests/test_m3_s01_parent_tristate.py::test_m3_ver_14_invalid_parent_carriers_are_invalid_request",
        }
    ),
    "M3-VER-15": frozenset(
        {
            "tests/test_m3_s01_parent_tristate.py::test_m3_ver_15_registry_and_parser_preserve_three_intent_states",
            "tests/test_m3_s01_parent_tristate.py::test_m3_ver_15_generic_nullable_direct_selector_rule",
            "tests/test_m3_s01_parent_tristate.py::test_m3_ver_15_noninteractive_omitted_uuid_and_null_carriers",
            "tests/test_m3_s01_parent_tristate.py::test_m3_ver_15_human_selector_uses_one_bounded_discovery",
            "tests/test_m3_s01_parent_tristate.py::test_m3_ver_15_nullable_body_and_path_none_are_location_aware",
            "tests/test_m3_s01_parent_tristate.py::test_m3_ver_15_interactive_null_is_one_primary_exchange",
        }
    ),
    "M3-VER-16": frozenset(
        {
            "tests/test_m3_s01_parent_tristate.py::test_m3_ver_16_parent_cursor_identity_and_limit_compatibility"
        }
    ),
    "M3-VER-17": frozenset(
        {
            "tests/test_m3_traceability.py::test_m3_ver_17_static_non_drift_baselines_are_exact",
            "tests/test_migrations.py::test_durable_root_structure_drift_repeatability_and_owned_downgrade",
            "tests/test_schema_metadata.py::test_metadata_contains_exactly_the_frozen_fifteen_tables",
        }
    ),
    "M3-VER-18": frozenset(
        {
            "tests/test_m3_traceability.py::test_m3_frozen_identifier_and_owner_registries_are_exact",
            "tests/test_m3_traceability.py::test_m3_route_cursor_and_cli_censuses_equal_live_authorities",
            "tests/test_m3_traceability.py::test_m3_evidence_targets_exist_and_are_collected",
            "tests/test_m3_traceability.py::test_m3_contract_quality_gates_and_normative_state_are_closed",
        }
    ),
    "M3-VER-19": frozenset(
        {
            "tests/test_m3_s06_integration.py::test_m3_ver_19_all_gets_execute_one_business_statement",
            "tests/test_m3_s06_integration.py::test_m3_ver_19_snapshot_is_complete_before_or_after",
        }
    ),
}
