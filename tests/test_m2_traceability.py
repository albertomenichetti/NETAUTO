"""Singular machine-checkable M2 census, evidence and concurrency registry."""

import ast
import inspect
import subprocess
import sys
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import cast

from netauto.application.relationshipdefinitions import RelationshipDefinitionService
from netauto.application.relationships import RelationshipService
from netauto.persistence.locking import AdvisoryGate, RowLockMode
from tests.test_m1_traceability import PGTEST_SCENARIOS
from tests.test_m2_s00_traceability import (
    DELIVERED_MUTATION_PLANS,
    PLAN_EVIDENCE_TARGETS,
    Mutation,
)

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


M2_MUTATION_TO_CALLABLE: dict[str, Mutation] = {
    **{
        mutation_id: owner
        for mutation_id, (owner, _) in DELIVERED_MUTATION_PLANS.items()
    },
    "RD.CN": RelationshipDefinitionService.create_next,
    "RD.R": RelationshipDefinitionService.revise,
    "RD.P": RelationshipDefinitionService.publish,
    "RD.SD": RelationshipDefinitionService.set_default,
    "RD.CD": RelationshipDefinitionService.clear_default,
    "RD.D": RelationshipDefinitionService.deprecate,
    "RD.DD": RelationshipDefinitionService.delete_draft,
    "REL.DC": RelationshipService.data_change,
    "REL.SC": cast(Mutation, RelationshipService.__dict__["_schema_change_attempt"]),
}
M2_MUTATIONS = frozenset(M2_MUTATION_TO_CALLABLE)
M2_MUTATION_TO_GATE: dict[str, AdvisoryGate | None] = {
    mutation_id: gate for mutation_id, (_, gate) in DELIVERED_MUTATION_PLANS.items()
} | {mutation_id: None for mutation_id in M2_MUTATIONS - set(DELIVERED_MUTATION_PLANS)}

_FAMILY_EXECUTION_TARGETS = {
    "DT": frozenset(
        {
            "tests/test_datatype_api.py::test_datatype_full_public_lifecycle",
            "tests/test_datatype_api.py::"
            "test_datatype_active_consumers_and_lineage_delete_authority",
        }
    ),
    "OT": frozenset(
        {
            "tests/test_objecttemplate_api.py::test_objecttemplate_full_lifecycle_and_effective_schema",
            "tests/test_objecttemplate_api.py::"
            "test_objecttemplate_binding_clone_and_publish_recertification",
        }
    ),
    "OBJ": frozenset(
        {
            "tests/test_object_api.py::test_object_create_mutations_reads_lists_and_lifecycle",
            "tests/test_object_api.py::test_s05_ownership_schema_change_reads_and_lifecycle",
        }
    ),
    "RD": frozenset(
        {
            "tests/test_relationshipdefinition_api.py::"
            "test_relationship_definition_complete_crud_and_capability_projection",
            "tests/test_relationshipdefinition_api.py::"
            "test_m2_s01_rdv_properties_versions_defaults_and_factual_pin",
        }
    ),
    "REL": frozenset(
        {
            "tests/test_relationship_api.py::"
            "test_create_conflict_read_navigate_lifecycle_delete_and_definition_unblock",
            "tests/test_relationship_api.py::"
            "test_m2_s02_data_schema_change_lifecycle_and_strict_contract",
        }
    ),
}
M2_MUTATION_TO_EVIDENCE = {
    mutation_id: _FAMILY_EXECUTION_TARGETS[mutation_id.partition(".")[0]]
    for mutation_id in M2_MUTATIONS
}


_S02_SEMANTIC_PATH = "tests/test_m2_s02_semantic_concurrency.py::"
S02_ROW_29_TARGETS = frozenset(
    _S02_SEMANTIC_PATH
    + "test_row_29_mutation_delete_both_winner_orders"
    + f"[{delete_first}-{mutation}]"
    for delete_first in (False, True)
    for mutation in ("data", "schema")
)
S02_ROW_27_TARGETS = frozenset(
    _S02_SEMANTIC_PATH
    + "test_row_27_data_and_schema_change_have_serial_factual_history"
    + f"[{winner}]"
    for winner in ("data-first", "schema-first")
)
S02_ROW_28_TARGETS = frozenset(
    _S02_SEMANTIC_PATH
    + "test_row_28_schema_changes_recheck_forward_target_after_wait"
    + f"[{winner}]"
    for winner in ("lower-first", "higher-first")
)
S02_ROW_30_TARGETS = frozenset(
    {
        _S02_SEMANTIC_PATH
        + "test_row_30_schema_change_first_blocks_target_deprecation",
        _S02_SEMANTIC_PATH
        + "test_row_30_target_deprecation_first_blocks_schema_change",
        _S02_SEMANTIC_PATH + "test_row_30_definition_default_change_is_independent",
    }
)
S02_REF_10_TARGETS = frozenset(
    {
        _S02_SEMANTIC_PATH + "test_ref_10_schema_change_first_blocks_definition_delete",
        _S02_SEMANTIC_PATH
        + "test_ref_10_definition_delete_first_rolls_back_then_schema_changes",
    }
)
S02_SNAP_05_TARGETS = frozenset(
    _S02_SEMANTIC_PATH
    + "test_snap_05_each_mutation_observes_each_independent_rename_cut"
    + f"[{rename_case}-{transition}]"
    for rename_case in ("from", "to", "both", "definition")
    for transition in ("data", "schema")
)
S02_FANOUT_TARGETS = frozenset(
    {
        _S02_SEMANTIC_PATH
        + "test_m2_s02_all_transition_families_use_distinct_semantic_fanout"
        + "[symmetric_distinct-False-False-2-2]",
        _S02_SEMANTIC_PATH
        + "test_m2_s02_all_transition_families_use_distinct_semantic_fanout"
        + "[symmetric_self-True-False-1-1]",
        _S02_SEMANTIC_PATH
        + "test_m2_s02_all_transition_families_use_distinct_semantic_fanout"
        + "[inheritance_overlap-False-True-4-2]",
    }
)
S02_READ_CUT_TARGETS = frozenset(
    {
        *(
            _S02_SEMANTIC_PATH
            + "test_relationship_read_cuts_expose_only_committed_before_or_after"
            + f"[{transition}]"
            for transition in ("data", "schema", "delete")
        ),
        *(
            _S02_SEMANTIC_PATH
            + "test_relationship_snapshot_cut_commits_between_physical_reads"
            + f"[{transition}-{read_shape}]"
            for transition in ("data", "schema", "delete")
            for read_shape in ("get", "page")
        ),
    }
)


S01_BUNDLE_TARGETS: dict[str, frozenset[str]] = {
    "M2-VER-01": frozenset(
        {
            "tests/test_relationshipdefinition_domain.py::"
            "test_rdv_declaration_shape_and_complete_history_rules",
            "tests/test_relationshipdefinition_api.py::"
            "test_relationship_definition_complete_crud_and_capability_projection",
            "tests/test_relationshipdefinition_api.py::"
            "test_m2_s01_rdv_properties_versions_defaults_and_factual_pin",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_24_explicit_create_delete_first_preserves_exact_selector",
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
            "tests/test_s08_delete_diagnostics.py::"
            "test_datatype_delete_reports_rdv_only_and_mixed_property_blockers",
            "tests/test_s08_delete_diagnostics.py::"
            "test_datatype_delete_final_ot_property_fk_is_bounded",
            "tests/test_s08_delete_diagnostics.py::"
            "test_datatype_delete_final_rdv_property_fk_is_bounded",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_24_explicit_create_delete_first_preserves_exact_selector",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_ref_09_explicit_revise_delete_first_preserves_exact_selector",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_24_implicit_create_delete_first_identifies_lineage",
        }
    ),
    "M2-VER-05": frozenset(
        {
            "tests/test_relationshipdefinition_api.py::"
            "test_relationship_definition_complete_crud_and_capability_projection",
            "tests/test_relationshipdefinition_api.py::"
            "test_m2_s01_rdv_properties_versions_defaults_and_factual_pin",
            "tests/test_s08_delete_diagnostics.py::"
            "test_datatype_delete_final_ot_property_fk_is_bounded",
            "tests/test_s08_delete_diagnostics.py::"
            "test_datatype_delete_final_rdv_property_fk_is_bounded",
        }
    ),
    "M2-VER-06": frozenset(
        {
            "tests/test_relationshipdefinition_api.py::"
            "test_m2_s01_rdv_properties_versions_defaults_and_factual_pin",
            "tests/test_relationship_domain.py::"
            "test_factual_relationship_constructors_require_an_exact_version_pin",
            "tests/test_relationship_domain.py::"
            "test_factual_relationship_rejects_non_positive_or_boolean_exact_pin",
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

S02_BUNDLE_TARGETS: dict[str, frozenset[str]] = {
    "M2-VER-08": frozenset(
        {
            "tests/test_m2_s02_relationship_domain.py::"
            "test_m2_s02_data_change_complete_state_and_noop",
            "tests/test_m2_s02_relationship_domain.py::"
            "test_m2_s02_unique_operation_order_is_nonsemantic",
            "tests/test_m2_s02_relationship_domain.py::"
            "test_m2_s02_application_rejects_empty_and_duplicate_operations",
            "tests/test_relationship_api.py::"
            "test_m2_s02_data_schema_change_lifecycle_and_strict_contract",
            "tests/test_m2_s02_semantic_concurrency.py::"
            "test_row_26_data_changes_reread_fresh_state_and_waiter_can_be_noop",
            "tests/test_m2_s02_semantic_concurrency.py::"
            "test_atomic_06_07_real_dml_rolls_back_when_shared_writer_fails",
        }
    ),
    "M2-VER-09": frozenset(
        {
            "tests/test_m2_s02_relationship_domain.py::"
            "test_m2_s02_scalar_to_list_migration_is_canonical",
            "tests/test_m2_s02_relationship_domain.py::"
            "test_m2_s02_schema_migration_preserves_removes_and_blocks_by_member",
            "tests/test_relationship_api.py::"
            "test_m2_s02_data_schema_change_lifecycle_and_strict_contract",
            *S02_ROW_27_TARGETS,
            *S02_ROW_28_TARGETS,
            *S02_ROW_30_TARGETS,
            *S02_REF_10_TARGETS,
            "tests/test_m2_s02_semantic_concurrency.py::"
            "test_atomic_06_07_real_dml_rolls_back_when_shared_writer_fails",
        }
    ),
    "M2-VER-11": frozenset(
        {
            *S02_READ_CUT_TARGETS,
            "tests/test_relationship_api.py::"
            "test_db_valid_incomplete_runtime_aggregate_maps_to_internal_error",
        }
    ),
    "M2-VER-12": frozenset(
        {
            "tests/test_m2_s02_relationship_domain.py::"
            "test_m2_s02_historical_property_codec_rejects_invalid_carriers",
            "tests/test_m2_s02_relationship_domain.py::"
            "test_m2_s02_historical_property_codec_accepts_exact_carriers",
            "tests/test_m2_s02_relationship_domain.py::"
            "test_m2_s02_relationship_factual_state_requires_exact_shape",
            "tests/test_m2_s02_relationship_domain.py::"
            "test_m2_s02_relationship_writer_rejects_invalid_transition_shapes",
            "tests/test_relationship_api.py::"
            "test_m2_s02_data_schema_change_lifecycle_and_strict_contract",
            "tests/test_relationship_api.py::"
            "test_m2_s02_corrupt_relationship_transition_fails_complete_page",
        }
    ),
    "M2-VER-13": frozenset(
        {
            "tests/test_relationship_domain.py::"
            "test_symmetric_disjoint_and_inheritance_overlap_closure_shapes",
            "tests/test_relationship_api.py::"
            "test_strict_operands_missing_resources_incompatibility_and_self_loop",
            "tests/test_relationship_api.py::"
            "test_m2_s02_data_schema_change_lifecycle_and_strict_contract",
            *S02_FANOUT_TARGETS,
        }
    ),
    "M2-VER-14": frozenset(
        {
            "tests/test_m2_s02_relationship_domain.py::"
            "test_m2_s02_lifecycle_store_is_the_sole_event_table_sql_owner",
            "tests/test_relationship_api.py::"
            "test_m2_s02_data_schema_change_lifecycle_and_strict_contract",
            "tests/test_relationship_api.py::"
            "test_create_conflict_read_navigate_lifecycle_delete_and_definition_unblock",
            "tests/test_m2_s02_semantic_concurrency.py::"
            "test_atomic_06_07_real_dml_rolls_back_when_shared_writer_fails",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_create_event_failure_rolls_back_header_and_complete_closure",
            "tests/test_relationship_semantic_concurrency.py::"
            "test_atomic_03_delete_event_failure_rolls_back_complete_fact",
        }
    ),
}

_S01_PRIMARY_SCENARIO_TARGETS = {
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

S01_SCENARIO_TARGETS = {
    scenario_id: frozenset({target})
    for scenario_id, target in _S01_PRIMARY_SCENARIO_TARGETS.items()
}
S01_SCENARIO_TARGETS["ROW-24"] |= frozenset(
    {
        "tests/test_m2_s01_semantic_concurrency.py::"
        "test_row_24_explicit_create_delete_first_preserves_exact_selector",
        "tests/test_m2_s01_semantic_concurrency.py::"
        "test_row_24_implicit_create_delete_first_identifies_lineage",
    }
)
S01_SCENARIO_TARGETS["REF-09"] |= frozenset(
    {
        "tests/test_m2_s01_semantic_concurrency.py::"
        "test_ref_09_explicit_revise_delete_first_preserves_exact_selector"
    }
)

S02_SCENARIO_TARGETS = {
    "ROW-26": frozenset(
        {
            "tests/test_m2_s02_semantic_concurrency.py::"
            "test_row_26_data_changes_reread_fresh_state_and_waiter_can_be_noop"
        }
    ),
    "ROW-27": S02_ROW_27_TARGETS,
    "ROW-28": S02_ROW_28_TARGETS,
    "ROW-29": frozenset(S02_ROW_29_TARGETS),
    "ROW-30": S02_ROW_30_TARGETS,
    "REF-10": S02_REF_10_TARGETS,
    "SNAP-05": frozenset(
        {
            "tests/test_m2_s02_semantic_concurrency.py::"
            "test_snap_05_relationship_mutations_capture_one_metadata_statement",
            *S02_SNAP_05_TARGETS,
        }
    ),
    "ATOMIC-06": frozenset(
        {
            "tests/test_m2_s02_semantic_concurrency.py::"
            "test_atomic_06_07_real_dml_rolls_back_when_shared_writer_fails"
        }
    ),
    "ATOMIC-07": frozenset(
        {
            "tests/test_m2_s02_semantic_concurrency.py::"
            "test_atomic_06_07_real_dml_rolls_back_when_shared_writer_fails"
        }
    ),
}

DELIVERED_SCENARIO_TARGETS = {
    scenario_id: frozenset(f"{target.module}::{target.function}" for target in targets)
    for scenario_id, targets in PGTEST_SCENARIOS.items()
}

_S03_SEMANTIC_PATH = "tests/test_m2_s03_semantic_concurrency.py::"
S03_SCENARIO_TARGETS: dict[str, frozenset[str]] = {
    "ROW-03": frozenset(
        {
            "tests/test_objecttemplate_semantic_concurrency.py::"
            "test_row_03_ot_revise_same_generation_has_one_stale_loser"
        }
    ),
    "ROW-04": frozenset(
        {
            "tests/test_objecttemplate_semantic_concurrency.py::"
            "test_row_04a_ot_revise_serializes_publish_and_forces_fresh_revision",
            "tests/test_objecttemplate_semantic_concurrency.py::"
            "test_row_04b_ot_publish_serializes_delete_draft",
        }
    ),
    "ROW-16": frozenset(
        {
            "tests/test_objecttemplate_semantic_concurrency.py::"
            "test_row_16_revise_serializes_whole_lineage_delete",
            *(
                _S03_SEMANTIC_PATH
                + "test_row_16_relationship_definition_internal_and_root_delete_"
                + "both_orders"
                + f"[{order}]"
                for order in ("internal-first", "delete-first")
            ),
        }
    ),
    "REF-08": frozenset(
        _S03_SEMANTIC_PATH
        + "test_ref_08_clone_reference_lifetimes"
        + f"[{order}-{shape}]"
        for order in ("clone-first", "delete-first")
        for shape in ("parent", "component", "property")
    ),
    "REF-09": frozenset(
        {
            *(
                _S03_SEMANTIC_PATH
                + "test_ref_09_differential_rebind_lifetimes"
                + f"[{order}-{family}]"
                for order in ("rebind-first", "delete-first")
                for family in ("object-template-component", "rdv-property")
            ),
            *(
                _S03_SEMANTIC_PATH
                + "test_ref_09_same_target_unchanged_and_removed_plan_variants"
                + f"[{family}]"
                for family in ("object-template", "rdv")
            ),
        }
    ),
    "REF-10": frozenset(
        _S03_SEMANTIC_PATH
        + "test_ref_10_direct_owner_rebinds_target_before_owner"
        + f"[{order}-{family}]"
        for order in ("rebind-first", "delete-first")
        for family in ("object-template-parent", "object-schema")
    ),
    "REF-11": frozenset(
        {
            _S03_SEMANTIC_PATH
            + "test_ref_11_mutual_roots_serialize_through_model_delete_gate"
        }
    ),
    "GATE-07": frozenset(
        {
            _S03_SEMANTIC_PATH
            + "test_gate_07_independent_root_deletes_wait_before_rows_and_reread"
        }
    ),
    "SNAP-01": frozenset(
        _S02_SEMANTIC_PATH
        + "test_snap_05_each_mutation_observes_each_independent_rename_cut"
        + f"[definition-{transition}]"
        for transition in ("data", "schema")
    ),
    "SNAP-02": frozenset(
        _S02_SEMANTIC_PATH
        + "test_snap_05_each_mutation_observes_each_independent_rename_cut"
        + f"[{rename_case}-{transition}]"
        for rename_case in ("from", "to", "both")
        for transition in ("data", "schema")
    ),
    "PAR-06": frozenset(
        {
            "tests/test_objecttemplate_semantic_concurrency.py::"
            "test_par_06_ot_deprecates_distinct_versions_without_lineage_contention"
        }
    ),
    "PAR-07": frozenset(
        {
            "tests/test_objecttemplate_semantic_concurrency.py::"
            "test_row_15_and_par_07_description_lock_topology"
        }
    ),
    "PAR-08": frozenset(
        _S03_SEMANTIC_PATH
        + "test_par_08_definition_rename_compatible_operations_progress"
        + f"[{operation}]"
        for operation in (
            "revise",
            "set-default",
            "deprecate",
            "relationship-create",
        )
    ),
    "PAR-09": frozenset(
        _S03_SEMANTIC_PATH
        + "test_par_09_distinct_rdv_operations_make_progress"
        + f"[{operation}]"
        for operation in ("deprecate", "revise")
    ),
}

PLAN_SCENARIO_TARGETS: dict[str, frozenset[str]] = {
    scenario_id: frozenset(
        target for targets in categories.values() for target in targets
    )
    for scenario_id, categories in PLAN_EVIDENCE_TARGETS.items()
}
M2_SCENARIO_TO_TARGETS: dict[str, frozenset[str]] = {
    scenario_id: DELIVERED_SCENARIO_TARGETS.get(scenario_id, frozenset())
    | S01_SCENARIO_TARGETS.get(scenario_id, frozenset())
    | S02_SCENARIO_TARGETS.get(scenario_id, frozenset())
    | S03_SCENARIO_TARGETS.get(scenario_id, frozenset())
    | PLAN_SCENARIO_TARGETS.get(scenario_id, frozenset())
    for scenario_id in M2_CONCURRENCY_SCENARIOS
}
M2_IMPLEMENTED_SCENARIO_TARGETS = M2_SCENARIO_TO_TARGETS


def _scenario_evidence(*scenario_ids: str) -> frozenset[str]:
    return frozenset(
        target
        for scenario_id in scenario_ids
        for target in M2_SCENARIO_TO_TARGETS[scenario_id]
    )


M2_MUTATION_TO_EVIDENCE.update(
    {
        "OT.C": M2_MUTATION_TO_EVIDENCE["OT.C"]
        | _scenario_evidence("ROW-07", "ROW-08", "REF-01"),
        "OT.CN": M2_MUTATION_TO_EVIDENCE["OT.CN"] | _scenario_evidence("REF-08"),
        "OT.R": M2_MUTATION_TO_EVIDENCE["OT.R"]
        | _scenario_evidence("REF-09", "REF-10"),
        "OT.P": M2_MUTATION_TO_EVIDENCE["OT.P"]
        | _scenario_evidence("ROW-09", "ROW-22"),
        "OBJ.C": M2_MUTATION_TO_EVIDENCE["OBJ.C"] | _scenario_evidence("ROW-24"),
        "OBJ.SC": M2_MUTATION_TO_EVIDENCE["OBJ.SC"]
        | _scenario_evidence("ROW-12", "REF-10"),
        "OBJ.A": M2_MUTATION_TO_EVIDENCE["OBJ.A"]
        | _scenario_evidence("GATE-01", "GATE-02", "GATE-03"),
        "RD.C": M2_MUTATION_TO_EVIDENCE["RD.C"]
        | _scenario_evidence("ROW-24", "GATE-04"),
        "RD.CN": M2_MUTATION_TO_EVIDENCE["RD.CN"] | _scenario_evidence("REF-07"),
        "RD.R": M2_MUTATION_TO_EVIDENCE["RD.R"]
        | _scenario_evidence("REF-09", "PAR-08", "PAR-09"),
        "RD.P": M2_MUTATION_TO_EVIDENCE["RD.P"]
        | _scenario_evidence("ROW-23", "ROW-25"),
        "REL.C": M2_MUTATION_TO_EVIDENCE["REL.C"]
        | _scenario_evidence("ROW-30", "ARB-05", "ARB-08", "PAR-08"),
        "REL.SC": M2_MUTATION_TO_EVIDENCE["REL.SC"]
        | _scenario_evidence("ROW-27", "ROW-28", "ROW-30", "REF-10"),
    }
)


@dataclass(frozen=True, slots=True)
class ScenarioRecipes:
    primary: str
    secondary: frozenset[str] = frozenset()


M2_RECIPES = frozenset(
    {
        "REC-LOCK",
        "REC-UNIQUE",
        "REC-FK",
        "REC-GATE",
        "REC-CUT",
        "REC-ROLLBACK",
        "REC-PROGRESS",
        "REC-ABA",
        "REC-PLAN",
        "REC-CLASSIFY",
        "REC-RESTART",
    }
)
M2_SCENARIO_TO_RECIPES = {
    scenario_id: ScenarioRecipes(
        {
            "ROW": "REC-LOCK",
            "ARB": "REC-UNIQUE",
            "REF": "REC-FK",
            "GATE": "REC-GATE",
            "SNAP": "REC-CUT",
            "ATOMIC": "REC-ROLLBACK",
            "PAR": "REC-PROGRESS",
        }[scenario_id.partition("-")[0]]
    )
    for scenario_id in M2_CONCURRENCY_SCENARIOS
    if not scenario_id.startswith("PLAN-")
}
M2_SCENARIO_TO_RECIPES.update(
    {
        "ARB-05": ScenarioRecipes("REC-UNIQUE", frozenset({"REC-ROLLBACK"})),
        "ARB-06": ScenarioRecipes("REC-ABA", frozenset({"REC-LOCK"})),
        "ARB-07": ScenarioRecipes("REC-ABA", frozenset({"REC-RESTART"})),
        "ARB-08": ScenarioRecipes("REC-UNIQUE", frozenset({"REC-ROLLBACK"})),
        "REF-11": ScenarioRecipes("REC-GATE", frozenset({"REC-FK"})),
        "PLAN-01": ScenarioRecipes("REC-PLAN"),
        "PLAN-02": ScenarioRecipes("REC-PLAN"),
        "PLAN-03": ScenarioRecipes("REC-RESTART"),
        "PLAN-04": ScenarioRecipes("REC-CLASSIFY"),
        "PLAN-05": ScenarioRecipes("REC-RESTART"),
        "PLAN-06": ScenarioRecipes("REC-PLAN"),
    }
)

M2_PREDICATE_TO_SCENARIOS: dict[str, frozenset[str]] = {
    "NU": frozenset({"ARB-01"}),
    "VS": frozenset({"ROW-01", "ROW-02", "ROW-18", "ROW-19"}),
    "DG": frozenset({"ROW-03", "ROW-04", "ROW-20", "ATOMIC-01", "ATOMIC-05"}),
    "LS": frozenset({"ROW-04", "ROW-06", "ROW-20", "ROW-21"}),
    "DV": frozenset(
        {"ROW-05", "ROW-06", "ROW-08", "ROW-21", "ROW-23", "ROW-24", "ROW-30"}
    ),
    "VH": frozenset({"ROW-22", "ROW-23"}),
    "BA": frozenset({"ROW-07", "ROW-08", "ROW-12", "ROW-24", "ROW-28", "ROW-30"}),
    "AM": frozenset({"ROW-09", "ROW-10", "ROW-25"}),
    "RL": frozenset(f"REF-{number:02d}" for number in range(1, 12)),
    "AL": frozenset({"ROW-16", "ROW-17"}),
    "ML": frozenset({"ROW-15"}),
    "OS": frozenset({"ROW-11", "ROW-12", "ATOMIC-04"}),
    "RS": frozenset({"ROW-26", "ROW-27", "ROW-28", "ROW-29", "ATOMIC-06", "ATOMIC-07"}),
    "PO": frozenset({"ROW-13", "ROW-14"}),
    "OF": frozenset({"ARB-03", "ARB-04", "ATOMIC-04"}),
    "SO": frozenset({"ARB-02"}),
    "OC": frozenset({"GATE-01", "GATE-02", "GATE-03", "PAR-04"}),
    "RC": frozenset({"GATE-04", "GATE-05", "GATE-06", "ATOMIC-04"}),
    "RF": frozenset({"ARB-05", "ARB-07", "ARB-08", "ATOMIC-02"}),
    "RA": frozenset({"ARB-06", "ARB-07", "ATOMIC-03"}),
    "ES": frozenset(
        {
            "SNAP-01",
            "SNAP-02",
            "SNAP-03",
            "SNAP-04",
            "SNAP-05",
            "PAR-01",
            "PAR-02",
            "PAR-08",
        }
    ),
}

S03_BUNDLE_SCENARIOS = {
    "M2-VER-15": frozenset({"ROW-03", "ROW-04", "ROW-20", "ATOMIC-01", "ATOMIC-05"}),
    "M2-VER-16": frozenset(
        {
            *(f"ROW-{number:02d}" for number in range(7, 11)),
            *(f"ROW-{number:02d}" for number in range(21, 26)),
            "ROW-30",
        }
    ),
    "M2-VER-17": frozenset({"ARB-05", "ARB-07", "ARB-08", "ATOMIC-02", "PLAN-05"}),
    "M2-VER-18": frozenset({"ROW-26", "ROW-27", "ROW-28", "ROW-29", "ARB-06"}),
    "M2-VER-19": frozenset(
        {
            *(f"SNAP-{number:02d}" for number in range(1, 6)),
            "PAR-01",
            "PAR-02",
            "PAR-08",
        }
    ),
}
S03_BUNDLE_TARGETS: dict[str, frozenset[str]] = {
    bundle_id: frozenset(
        target
        for scenario_id in scenario_ids
        for target in M2_SCENARIO_TO_TARGETS[scenario_id]
    )
    for bundle_id, scenario_ids in S03_BUNDLE_SCENARIOS.items()
}
M2_EVIDENCE_TO_TARGETS = {
    bundle_id: EvidenceBundle(
        "IMPLEMENTED"
        if bundle_id in S01_BUNDLE_TARGETS
        or bundle_id in S02_BUNDLE_TARGETS
        or bundle_id in S03_BUNDLE_TARGETS
        else "DESIGNED",
        S01_BUNDLE_TARGETS.get(bundle_id, frozenset())
        | S02_BUNDLE_TARGETS.get(bundle_id, frozenset())
        | S03_BUNDLE_TARGETS.get(bundle_id, frozenset()),
    )
    for bundle_id in M2_EVIDENCE_BUNDLES
}

S01_REVIEW_FIX_TARGETS = {
    "S01-RF-01": frozenset(
        {
            "tests/test_s08_delete_diagnostics.py::"
            "test_datatype_delete_reports_rdv_only_and_mixed_property_blockers",
            "tests/test_s08_delete_diagnostics.py::"
            "test_datatype_delete_final_ot_property_fk_is_bounded",
            "tests/test_s08_delete_diagnostics.py::"
            "test_datatype_delete_final_rdv_property_fk_is_bounded",
            "tests/test_s08_persistence_error_mapping.py::"
            "test_datatype_delete_maps_exact_property_reference_constraints",
        }
    ),
    "S01-RF-02": frozenset(
        {
            "tests/test_relationship_domain.py::"
            "test_factual_relationship_constructors_require_an_exact_version_pin",
            "tests/test_relationship_domain.py::"
            "test_factual_relationship_rejects_non_positive_or_boolean_exact_pin",
            "tests/test_relationshipdefinition_api.py::"
            "test_m2_s01_rdv_properties_versions_defaults_and_factual_pin",
        }
    ),
    "S01-RF-03": frozenset(
        {
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_24_explicit_create_delete_first_preserves_exact_selector",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_ref_09_explicit_revise_delete_first_preserves_exact_selector",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_24_implicit_create_delete_first_identifies_lineage",
            "tests/test_m2_s01_semantic_concurrency.py::"
            "test_row_24_implicit_dtv_binding_is_stable_through_commit",
        }
    ),
}

S02_REVIEW_FIX_TARGETS = {
    "S02-RF-01": frozenset(
        {
            *S02_SCENARIO_TARGETS["ROW-26"],
            *S02_ROW_27_TARGETS,
            *S02_ROW_28_TARGETS,
            *S02_ROW_30_TARGETS,
            *S02_REF_10_TARGETS,
        }
    ),
    "S02-RF-02": frozenset(
        {
            "tests/test_relationship_api.py::"
            "test_m2_s02_data_schema_change_lifecycle_and_strict_contract"
        }
    ),
    "S02-RF-03": frozenset(
        {
            "tests/test_m2_s02_semantic_concurrency.py::"
            "test_object_relationship_page_batches_only_represented_definitions",
            "tests/test_m2_s02_semantic_concurrency.py::"
            "test_published_relationship_history_is_set_based_and_schema_change_uses_it",
        }
    ),
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

S02_PUBLIC_ROUTE_DELTA = frozenset(
    {
        ("POST", "/api/v1/core/relationships/{relationship_id}/data-change"),
        ("POST", "/api/v1/core/relationships/{relationship_id}/schema-change"),
    }
)


def _assert_target_exists(target: str) -> None:
    path_text, separator, test_name = target.partition("::")
    assert separator and test_name.startswith("test_"), target
    function_name = test_name.partition("[")[0]
    path = Path(path_text)
    assert path.is_file(), target
    tree = ast.parse(path.read_text())
    collected_names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }
    assert function_name in collected_names, target
    collected = _collected_test_nodes()
    assert target in collected or any(
        node.startswith(f"{target}[") for node in collected
    ), target


@cache
def _collected_test_nodes() -> frozenset[str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return frozenset(
        line.strip()
        for line in result.stdout.splitlines()
        if line.startswith("tests/") and "::test_" in line
    )


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


def test_s02_bundle_states_and_targets_are_honest_and_resolvable() -> None:
    assert set(M2_EVIDENCE_TO_TARGETS) == M2_EVIDENCE_BUNDLES
    assert set(S01_BUNDLE_TARGETS) == {
        *(f"M2-VER-{number:02d}" for number in range(1, 8)),
        "M2-VER-10",
        "M2-VER-20",
        "M2-VER-21",
    }
    for bundle_id, evidence in M2_EVIDENCE_TO_TARGETS.items():
        if (
            bundle_id in S01_BUNDLE_TARGETS
            or bundle_id in S02_BUNDLE_TARGETS
            or bundle_id in S03_BUNDLE_TARGETS
        ):
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
    for targets in S01_SCENARIO_TARGETS.values():
        assert targets
        for target in targets:
            _assert_target_exists(target)


def test_s02_scenario_map_is_exact_and_every_target_resolves() -> None:
    assert set(S02_SCENARIO_TARGETS) == {
        *(f"ROW-{number:02d}" for number in range(26, 31)),
        "REF-10",
        "SNAP-05",
        "ATOMIC-06",
        "ATOMIC-07",
    }
    assert set(S02_SCENARIO_TARGETS) <= M2_CONCURRENCY_SCENARIOS
    for targets in S02_SCENARIO_TARGETS.values():
        assert targets
        for target in targets:
            _assert_target_exists(target)
    assert M2_IMPLEMENTED_SCENARIO_TARGETS["ROW-30"] == (
        S01_SCENARIO_TARGETS["ROW-30"] | S02_SCENARIO_TARGETS["ROW-30"]
    )
    assert len(S02_ROW_29_TARGETS) == 4
    assert len(S02_ROW_27_TARGETS) == 2
    assert len(S02_ROW_28_TARGETS) == 2
    assert len(S02_ROW_30_TARGETS) == 3
    assert len(S02_REF_10_TARGETS) == 2
    assert len(S02_SNAP_05_TARGETS) == 8


def test_s01_review_fix_registry_is_exact_resolvable_and_scenario_mapped() -> None:
    assert set(S01_REVIEW_FIX_TARGETS) == {"S01-RF-01", "S01-RF-02", "S01-RF-03"}
    for targets in S01_REVIEW_FIX_TARGETS.values():
        assert targets
        for target in targets:
            _assert_target_exists(target)
    assert S01_REVIEW_FIX_TARGETS["S01-RF-03"] <= (
        S01_SCENARIO_TARGETS["ROW-24"] | S01_SCENARIO_TARGETS["REF-09"]
    )


def test_s02_review_fix_registry_is_exact_resolvable_and_scenario_mapped() -> None:
    assert set(S02_REVIEW_FIX_TARGETS) == {"S02-RF-01", "S02-RF-02", "S02-RF-03"}
    for targets in S02_REVIEW_FIX_TARGETS.values():
        assert targets
        for target in targets:
            _assert_target_exists(target)
    assert S02_REVIEW_FIX_TARGETS["S02-RF-01"] == frozenset(
        {
            *S02_SCENARIO_TARGETS["ROW-26"],
            *S02_SCENARIO_TARGETS["ROW-27"],
            *S02_SCENARIO_TARGETS["ROW-28"],
            *S02_SCENARIO_TARGETS["ROW-30"],
            *S02_SCENARIO_TARGETS["REF-10"],
        }
    )


def test_s02_route_delta_and_preserved_registries_remain_exact() -> None:
    assert len(S01_PUBLIC_ROUTE_DELTA) == 9
    assert all(path.startswith("/api/v1/core/") for _, path in S01_PUBLIC_ROUTE_DELTA)
    assert S02_PUBLIC_ROUTE_DELTA.isdisjoint(S01_PUBLIC_ROUTE_DELTA)
    assert len(S02_PUBLIC_ROUTE_DELTA) == 2
    assert set(PLAN_EVIDENCE_TARGETS) == {
        *(f"PLAN-{number:02d}" for number in range(1, 7))
    }


def test_s03_mutation_registry_is_exact_central_and_executable() -> None:
    assert len(M2_MUTATIONS) == 41
    assert sum(item.startswith("DT.") for item in M2_MUTATIONS) == 10
    assert sum(item.startswith("OT.") for item in M2_MUTATIONS) == 10
    assert sum(item.startswith("OBJ.") for item in M2_MUTATIONS) == 7
    assert sum(item.startswith("RD.") for item in M2_MUTATIONS) == 10
    assert sum(item.startswith("REL.") for item in M2_MUTATIONS) == 4
    assert set(M2_MUTATION_TO_CALLABLE) == M2_MUTATIONS
    assert set(M2_MUTATION_TO_GATE) == M2_MUTATIONS
    assert set(M2_MUTATION_TO_EVIDENCE) == M2_MUTATIONS
    assert {
        mutation_id: gate
        for mutation_id, gate in M2_MUTATION_TO_GATE.items()
        if gate is not None
    } == {
        "OBJ.A": AdvisoryGate.OWNERSHIP_GRAPH_WRITE_GATE,
        "RD.C": AdvisoryGate.RELATIONSHIP_DEFINITION_CONFLICT_GATE,
        "RD.RN": AdvisoryGate.RELATIONSHIP_DEFINITION_CONFLICT_GATE,
        "DT.DL": AdvisoryGate.MODEL_ROOT_DELETE_GATE,
        "OT.DL": AdvisoryGate.MODEL_ROOT_DELETE_GATE,
        "RD.DL": AdvisoryGate.MODEL_ROOT_DELETE_GATE,
    }
    assert len(set(AdvisoryGate)) == 3
    assert set(RowLockMode) == {
        RowLockMode.KS,
        RowLockMode.S,
        RowLockMode.NKU,
        RowLockMode.U,
    }
    for mutation_id, owner in M2_MUTATION_TO_CALLABLE.items():
        source = inspect.getsource(owner)
        assert "_acquire(" in source or "prepare_lock_plan(" in source, mutation_id
        assert "begin_dml()" in source, mutation_id
        assert M2_MUTATION_TO_EVIDENCE[mutation_id]
        for target in M2_MUTATION_TO_EVIDENCE[mutation_id]:
            _assert_target_exists(target)


def test_s03_scenario_registry_targets_and_recipes_are_exact() -> None:
    assert set(M2_SCENARIO_TO_TARGETS) == M2_CONCURRENCY_SCENARIOS
    assert set(M2_SCENARIO_TO_RECIPES) == M2_CONCURRENCY_SCENARIOS
    assert set(M2_SCENARIO_TO_RECIPES.values())
    assert M2_RECIPES == {
        "REC-LOCK",
        "REC-UNIQUE",
        "REC-FK",
        "REC-GATE",
        "REC-CUT",
        "REC-ROLLBACK",
        "REC-PROGRESS",
        "REC-ABA",
        "REC-PLAN",
        "REC-CLASSIFY",
        "REC-RESTART",
    }
    for scenario_id, targets in M2_SCENARIO_TO_TARGETS.items():
        assert targets, scenario_id
        for target in targets:
            _assert_target_exists(target)
        recipes = M2_SCENARIO_TO_RECIPES[scenario_id]
        assert recipes.primary in M2_RECIPES
        assert recipes.primary not in recipes.secondary
        assert recipes.secondary <= M2_RECIPES


def test_s03_predicate_registry_is_the_exact_frozen_map() -> None:
    assert set(M2_PREDICATE_TO_SCENARIOS) == {
        "NU",
        "VS",
        "DG",
        "LS",
        "DV",
        "VH",
        "BA",
        "AM",
        "RL",
        "AL",
        "ML",
        "OS",
        "RS",
        "PO",
        "OF",
        "SO",
        "OC",
        "RC",
        "RF",
        "RA",
        "ES",
    }
    assert len(M2_PREDICATE_TO_SCENARIOS) == 21
    for predicate, scenario_ids in M2_PREDICATE_TO_SCENARIOS.items():
        assert scenario_ids, predicate
        assert scenario_ids <= M2_CONCURRENCY_SCENARIOS
        assert frozenset().union(
            *(M2_SCENARIO_TO_TARGETS[item] for item in scenario_ids)
        )


def test_s03_primary_bundles_are_implemented_with_exact_scenario_membership() -> None:
    assert set(S03_BUNDLE_SCENARIOS) == {
        "M2-VER-15",
        "M2-VER-16",
        "M2-VER-17",
        "M2-VER-18",
        "M2-VER-19",
    }
    for bundle_id, scenario_ids in S03_BUNDLE_SCENARIOS.items():
        evidence = M2_EVIDENCE_TO_TARGETS[bundle_id]
        assert evidence.state == "IMPLEMENTED"
        assert evidence.targets == frozenset().union(
            *(M2_SCENARIO_TO_TARGETS[item] for item in scenario_ids)
        )
        for target in evidence.targets:
            _assert_target_exists(target)
