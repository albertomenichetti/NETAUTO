"""Frozen M2 census with honest S01 evidence and future-bundle states."""

import ast
from dataclasses import dataclass
from pathlib import Path

from tests.test_m2_s00_traceability import PLAN_EVIDENCE_TARGETS

M2_OUTCOMES = frozenset(f"M2-OUT-{number:02d}" for number in range(1, 17))
M2_ACCEPTANCE_CRITERIA = frozenset(f"M2-AC-{number:02d}" for number in range(1, 33))
M2_EVIDENCE_BUNDLES = frozenset(f"M2-VER-{number:02d}" for number in range(1, 33))
M2_CONCURRENCY_SCENARIOS = frozenset(
    {
        *(f"ROW-{number:02d}" for number in range(1, 31)),
        *(f"ARB-{number:02d}" for number in range(1, 9)),
        *(f"REF-{number:02d}" for number in range(1, 12)),
        *(f"GATE-{number:02d}" for number in range(1, 8)),
        *(f"SNAP-{number:02d}" for number in range(1, 6)),
        *(f"ATOMIC-{number:02d}" for number in range(1, 8)),
        *(f"PAR-{number:02d}" for number in range(1, 10)),
        *(f"PLAN-{number:02d}" for number in range(1, 7)),
    }
)

M2_OUTCOME_TO_ACCEPTANCE = {
    "M2-OUT-01": frozenset(f"M2-AC-{number:02d}" for number in range(1, 6)),
    "M2-OUT-02": frozenset(
        {"M2-AC-02", "M2-AC-03", "M2-AC-04", "M2-AC-15", "M2-AC-16"}
    ),
    "M2-OUT-03": frozenset({"M2-AC-06", "M2-AC-08", "M2-AC-09", "M2-AC-11"}),
    "M2-OUT-04": frozenset(
        {
            *(f"M2-AC-{number:02d}" for number in range(6, 11)),
            "M2-AC-17",
            "M2-AC-18",
        }
    ),
    "M2-OUT-05": frozenset(
        {
            "M2-AC-06",
            "M2-AC-07",
            "M2-AC-09",
            "M2-AC-10",
            "M2-AC-13",
            "M2-AC-31",
        }
    ),
    "M2-OUT-06": frozenset({"M2-AC-05", "M2-AC-11", "M2-AC-12", "M2-AC-13"}),
    "M2-OUT-07": frozenset(f"M2-AC-{number:02d}" for number in range(8, 15))
    | {"M2-AC-19"},
    "M2-OUT-08": frozenset(f"M2-AC-{number:02d}" for number in range(15, 20)),
    "M2-OUT-09": frozenset({"M2-AC-20", "M2-AC-21"}),
    "M2-OUT-10": frozenset({"M2-AC-22"}),
    "M2-OUT-11": frozenset({"M2-AC-23"}),
    "M2-OUT-12": frozenset(f"M2-AC-{number:02d}" for number in range(25, 29)),
    "M2-OUT-13": frozenset({"M2-AC-24"}),
    "M2-OUT-14": frozenset({"M2-AC-29"}),
    "M2-OUT-15": frozenset({"M2-AC-30"}),
    "M2-OUT-16": frozenset({"M2-AC-31", "M2-AC-32"}),
}
M2_ACCEPTANCE_TO_EVIDENCE = {
    f"M2-AC-{number:02d}": f"M2-VER-{number:02d}" for number in range(1, 33)
}


@dataclass(frozen=True, slots=True)
class EvidenceBundle:
    state: str
    targets: frozenset[str]


S01_BUNDLE_TARGETS: dict[str, frozenset[str]] = {
    "M2-VER-01": frozenset(
        {
            "tests/test_relationshipdefinition_domain.py::"
            "test_rdv_declaration_shape_and_complete_history_rules",
            "tests/test_relationshipdefinition_api.py::"
            "test_relationship_definition_complete_crud_and_capability_projection",
            "tests/test_relationshipdefinition_api.py::"
            "test_m2_s01_rdv_properties_versions_defaults_and_factual_pin",
        }
    ),
    "M2-VER-02": frozenset(
        {
            "tests/test_relationshipdefinition_api.py::"
            "test_m2_s01_rdv_properties_versions_defaults_and_factual_pin",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_18_create_next_allocates_serial_distinct_versions",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_19_create_next_rereads_max_after_draft_delete",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_20_one_exact_generation_consumer_wins",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_atomic_05_differential_failure_rolls_back_revision_and_children",
        }
    ),
    "M2-VER-03": frozenset(
        {
            "tests/test_relationshipdefinition_api.py::"
            "test_m2_s01_rdv_properties_versions_defaults_and_factual_pin",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_21_default_change_serializes_target_deprecation",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_23_rdv_publish_recertifies_complete_history",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_25_published_rdv_blocks_dtv_deprecation_after_wait",
        }
    ),
    "M2-VER-04": frozenset(
        {
            "tests/test_relationshipdefinition_domain.py::"
            "test_rdv_declaration_shape_and_complete_history_rules",
            "tests/test_relationshipdefinition_domain.py::"
            "test_rdv_declaration_rejects_duplicate_and_noncanonical_identity",
            "tests/test_relationshipdefinition_api.py::"
            "test_m2_s01_rdv_properties_versions_defaults_and_factual_pin",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_22_object_template_publish_recertifies_member_history",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_23_rdv_publish_recertifies_complete_history",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_24_implicit_dtv_binding_is_stable_through_commit",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_ref_07_clone_reference_blocks_datatype_root_delete",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_ref_09_rebound_reference_blocks_target_delete",
        }
    ),
    "M2-VER-05": frozenset(
        {
            "tests/test_relationshipdefinition_api.py::"
            "test_relationship_definition_complete_crud_and_capability_projection",
            "tests/test_relationshipdefinition_api.py::"
            "test_m2_s01_rdv_properties_versions_defaults_and_factual_pin",
        }
    ),
    "M2-VER-06": frozenset(
        {
            "tests/test_relationshipdefinition_api.py::"
            "test_m2_s01_rdv_properties_versions_defaults_and_factual_pin",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_30_and_arb_08_factual_selection_and_partial_owner_conflict",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_ref_03_and_ref_05_relationship_object_lifetime_arbitration",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_ref_04_create_reference_first_blocks_definition_delete",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_ref_04_definition_delete_first_rejects_relationship_create",
        }
    ),
    "M2-VER-07": frozenset(
        {
            "tests/test_relationship_api.py::"
            "test_create_conflict_read_navigate_lifecycle_delete_and_definition_unblock",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_arb_05_reciprocal_create_uses_pk_and_rejects_loser",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_arb_07b_winner_disappears_before_fresh_convergence_read",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_30_and_arb_08_factual_selection_and_partial_owner_conflict",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_atomic_02_later_closure_pk_collision_rolls_back_candidate",
        }
    ),
    "M2-VER-10": frozenset(
        {
            "tests/test_relationship_api.py::"
            "test_create_conflict_read_navigate_lifecycle_delete_and_definition_unblock",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_arb_06_same_id_delete_locks_and_emits_one_event_set",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_arb_07a_late_delete_cannot_remove_recreated_fact",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_atomic_03_delete_event_failure_rolls_back_complete_fact",
        }
    ),
    "M2-VER-20": frozenset(
        {
            "tests/test_schema_metadata.py::"
            "test_metadata_contains_exactly_the_frozen_fifteen_tables",
            "tests/test_migrations.py::"
            "test_durable_root_structure_drift_repeatability_and_owned_downgrade",
        }
    ),
    "M2-VER-21": frozenset(
        {
            "tests/test_migrations.py::"
            "test_durable_root_structure_drift_repeatability_and_owned_downgrade",
            "tests/test_migrations.py::"
            "test_durable_root_failure_rolls_back_and_corrected_rerun_succeeds",
        }
    ),
}

M2_EVIDENCE_TO_TARGETS = {
    bundle_id: EvidenceBundle(
        "IMPLEMENTED" if bundle_id in S01_BUNDLE_TARGETS else "DESIGNED",
        S01_BUNDLE_TARGETS.get(bundle_id, frozenset()),
    )
    for bundle_id in M2_EVIDENCE_BUNDLES
}

S01_SCENARIO_TARGETS = {
    "ROW-18": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_row_18_create_next_allocates_serial_distinct_versions",
    "ROW-19": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_row_19_create_next_rereads_max_after_draft_delete",
    "ROW-20": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_row_20_one_exact_generation_consumer_wins",
    "ROW-21": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_row_21_default_change_serializes_target_deprecation",
    "ROW-22": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_row_22_object_template_publish_recertifies_member_history",
    "ROW-23": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_row_23_rdv_publish_recertifies_complete_history",
    "ROW-24": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_row_24_implicit_dtv_binding_is_stable_through_commit",
    "ROW-25": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_row_25_published_rdv_blocks_dtv_deprecation_after_wait",
    "ROW-30": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_row_30_and_arb_08_factual_selection_and_partial_owner_conflict",
    "ARB-05": "tests/test_relationship_semantic_concurrency.py::"
    "test_arb_05_reciprocal_create_uses_pk_and_rejects_loser",
    "ARB-06": "tests/test_relationship_semantic_concurrency.py::"
    "test_arb_06_same_id_delete_locks_and_emits_one_event_set",
    "ARB-07": "tests/test_relationship_semantic_concurrency.py::"
    "test_arb_07b_winner_disappears_before_fresh_convergence_read",
    "ARB-08": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_row_30_and_arb_08_factual_selection_and_partial_owner_conflict",
    "REF-03": "tests/test_relationship_semantic_concurrency.py::"
    "test_ref_03_and_ref_05_relationship_object_lifetime_arbitration",
    "REF-04": "tests/test_relationship_semantic_concurrency.py::"
    "test_ref_04_create_reference_first_blocks_definition_delete",
    "REF-07": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_ref_07_clone_reference_blocks_datatype_root_delete",
    "REF-09": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_ref_09_rebound_reference_blocks_target_delete",
    "ATOMIC-02": "tests/test_relationship_semantic_concurrency.py::"
    "test_atomic_02_later_closure_pk_collision_rolls_back_candidate",
    "ATOMIC-03": "tests/test_relationship_semantic_concurrency.py::"
    "test_atomic_03_delete_event_failure_rolls_back_complete_fact",
    "ATOMIC-05": "tests/test_m2_s01_semantic_concurrency.py::"
    "test_atomic_05_differential_failure_rolls_back_revision_and_children",
}

S01_PUBLIC_ROUTE_DELTA = frozenset(
    {
        ("POST", "/api/v1/core/relationship-definitions/{id}/create-next"),
        ("POST", "/api/v1/core/relationship-definitions/{id}/set-default"),
        ("POST", "/api/v1/core/relationship-definitions/{id}/clear-default"),
        ("GET", "/api/v1/core/relationship-definitions/{id}/versions"),
        ("GET", "/api/v1/core/relationship-definitions/{id}/versions/{version}"),
        (
            "POST",
            "/api/v1/core/relationship-definitions/{id}/versions/{version}/revise",
        ),
        (
            "POST",
            "/api/v1/core/relationship-definitions/{id}/versions/{version}/publish",
        ),
        (
            "POST",
            "/api/v1/core/relationship-definitions/{id}/versions/{version}/deprecate",
        ),
        ("DELETE", "/api/v1/core/relationship-definitions/{id}/versions/{version}"),
    }
)


def _assert_target_exists(target: str) -> None:
    path_text, separator, test_name = target.partition("::")
    assert separator and test_name.startswith("test_"), target
    path = Path(path_text)
    assert path.is_file(), target
    tree = ast.parse(path.read_text())
    collected_names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }
    assert test_name in collected_names, target


def test_m2_frozen_identifier_census_is_exact() -> None:
    assert len(M2_OUTCOMES) == 16
    assert len(M2_ACCEPTANCE_CRITERIA) == 32
    assert len(M2_EVIDENCE_BUNDLES) == 32
    assert len(M2_CONCURRENCY_SCENARIOS) == 83
    assert {key.split("-")[0] for key in M2_CONCURRENCY_SCENARIOS} == {
        "ROW",
        "ARB",
        "REF",
        "GATE",
        "SNAP",
        "ATOMIC",
        "PAR",
        "PLAN",
    }
    assert set(M2_OUTCOME_TO_ACCEPTANCE) == M2_OUTCOMES
    assert set(M2_ACCEPTANCE_TO_EVIDENCE) == M2_ACCEPTANCE_CRITERIA
    assert set(M2_ACCEPTANCE_TO_EVIDENCE.values()) == M2_EVIDENCE_BUNDLES


def test_s01_bundle_states_and_targets_are_honest_and_resolvable() -> None:
    assert set(M2_EVIDENCE_TO_TARGETS) == M2_EVIDENCE_BUNDLES
    assert set(S01_BUNDLE_TARGETS) == {
        *(f"M2-VER-{number:02d}" for number in range(1, 8)),
        "M2-VER-10",
        "M2-VER-20",
        "M2-VER-21",
    }
    for bundle_id, evidence in M2_EVIDENCE_TO_TARGETS.items():
        if bundle_id in S01_BUNDLE_TARGETS:
            assert evidence.state == "IMPLEMENTED"
            assert evidence.targets
        else:
            assert evidence == EvidenceBundle("DESIGNED", frozenset())
        for target in evidence.targets:
            _assert_target_exists(target)


def test_s01_scenario_map_is_exact_and_every_target_resolves() -> None:
    assert set(S01_SCENARIO_TARGETS) == {
        *(f"ROW-{number:02d}" for number in range(18, 26)),
        "ROW-30",
        *(f"ARB-{number:02d}" for number in range(5, 9)),
        "REF-03",
        "REF-04",
        "REF-07",
        "REF-09",
        "ATOMIC-02",
        "ATOMIC-03",
        "ATOMIC-05",
    }
    assert set(S01_SCENARIO_TARGETS) <= M2_CONCURRENCY_SCENARIOS
    for target in S01_SCENARIO_TARGETS.values():
        _assert_target_exists(target)


def test_s01_route_delta_and_s00_plan_registry_remain_exact() -> None:
    assert len(S01_PUBLIC_ROUTE_DELTA) == 9
    assert all(path.startswith("/api/v1/core/") for _, path in S01_PUBLIC_ROUTE_DELTA)
    assert {
        ("POST", "/api/v1/core/relationships/{relationship_id}/data-change"),
        ("POST", "/api/v1/core/relationships/{relationship_id}/schema-change"),
    }.isdisjoint(S01_PUBLIC_ROUTE_DELTA)
    assert set(PLAN_EVIDENCE_TARGETS) == {
        *(f"PLAN-{number:02d}" for number in range(1, 7))
    }
