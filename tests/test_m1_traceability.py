"""Cheap, machine-checkable traceability for the frozen M1 PGTEST census."""

import ast
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).parents[1]


@dataclass(frozen=True)
class ScenarioTarget:
    """One concrete pytest function that supplies evidence for a scenario."""

    module: str
    function: str


def _node(module: str, *functions: str) -> tuple[ScenarioTarget, ...]:
    return tuple(ScenarioTarget(module, function) for function in functions)


# Variants remain values beneath their one canonical scenario ID. A target may be
# shared when one test deliberately exercises a composed scenario/mechanism.
PGTEST_SCENARIOS: dict[str, tuple[ScenarioTarget, ...]] = {
    "ROW-01": _node(
        "tests/test_datatype_semantic_concurrency.py",
        "test_row_01_create_next_allocates_distinct_serial_versions",
    ),
    "ROW-02": _node(
        "tests/test_datatype_semantic_concurrency.py",
        "test_row_02_create_next_reuses_deleted_max_after_wait",
    ),
    "ROW-03": _node(
        "tests/test_datatype_semantic_concurrency.py",
        "test_row_03_only_one_revise_applies_to_generation",
    ),
    "ROW-04": _node(
        "tests/test_datatype_semantic_concurrency.py",
        "test_row_04a_revise_publish_same_generation_is_serial",
        "test_row_04b_publish_delete_draft_same_generation_is_serial",
    ),
    "ROW-05": _node(
        "tests/test_datatype_semantic_concurrency.py",
        "test_row_05_first_serial_publish_sets_stable_default",
    ),
    "ROW-06": _node(
        "tests/test_datatype_semantic_concurrency.py",
        "test_row_06_default_never_points_to_deprecated_version",
    ),
    "ROW-07": _node(
        "tests/test_objecttemplate_semantic_concurrency.py",
        "test_row_07_explicit_binding_stabilizes_dtv_until_consumer_commit",
    ),
    "ROW-08": _node(
        "tests/test_objecttemplate_semantic_concurrency.py",
        "test_row_08_implicit_binding_materializes_one_serial_default",
    ),
    "ROW-09": _node(
        "tests/test_objecttemplate_semantic_concurrency.py",
        "test_row_09_publish_property_rendezvous_with_dependency_deprecate",
        "test_row_09_publish_child_rendezvous_with_parent_deprecate",
    ),
    "ROW-10": _node(
        "tests/test_objecttemplate_semantic_concurrency.py",
        "test_row_10_active_removal_is_conservative_during_dependency_deprecate",
    ),
    "ROW-11": _node(
        "tests/test_object_semantic_concurrency.py",
        "test_row_11_data_change_serializes_and_rereads_fresh_state",
    ),
    "ROW-12": _node(
        "tests/test_object_semantic_concurrency.py",
        "test_row_12_data_change_and_schema_change_share_object_owner",
        "test_row_12_schema_change_rechecks_source_after_wait",
        "test_row_12_schema_target_admission_lives_through_commit",
    ),
    "ROW-13": _node(
        "tests/test_object_semantic_concurrency.py",
        "test_row_13_attach_then_schema_change_observes_edge",
        "test_row_13_schema_change_then_attach_observes_removed_slot",
    ),
    "ROW-14": _node(
        "tests/test_object_semantic_concurrency.py",
        "test_row_14_detach_then_schema_change_observes_removal",
        "test_row_14_schema_change_then_detach_removes_exact_edge",
    ),
    "ROW-15": _node(
        "tests/test_datatype_semantic_concurrency.py",
        "test_row_15_description_writers_commit_complete_lww_values",
    ),
    "ROW-16": _node(
        "tests/test_datatype_semantic_concurrency.py",
        "test_row_16_revise_then_delete_has_no_partial_aggregate",
    ),
    "ROW-17": _node(
        "tests/test_relationshipdefinition_semantic_concurrency.py",
        "test_row_17_rename_then_delete_share_definition_lifetime_owner",
        "test_row_17_delete_then_rename_observes_absent_definition",
    ),
    "ARB-01": _node(
        "tests/test_datatype_semantic_concurrency.py",
        "test_arb_01_one_semantic_create_wins_without_orphans",
    ),
    "ARB-02": (
        *_node(
            "tests/test_object_semantic_concurrency.py",
            "test_arb_02_and_gate_03_same_child_reread_after_gate",
        ),
        *_node(
            "tests/test_persistence_constraints.py",
            "test_runtime_authorities_and_historical_lifecycle_defaults",
        ),
    ),
    "ARB-03": _node(
        "tests/test_object_semantic_concurrency.py",
        "test_arb_03_identical_attach_converges_with_one_event",
        "test_arb_03b_identical_detach_converges_with_one_event",
    ),
    "ARB-04": _node(
        "tests/test_object_semantic_concurrency.py",
        "test_arb_04_attach_then_detach_is_serially_explainable",
    ),
    "ARB-05": _node(
        "tests/test_relationship_semantic_concurrency.py",
        "test_arb_05_reciprocal_create_uses_pk_and_converges",
        "test_arb_05_symmetric_inverse_and_overlap_create_converge",
    ),
    "ARB-06": _node(
        "tests/test_relationship_semantic_concurrency.py",
        "test_arb_06_same_id_delete_locks_and_emits_one_event_set",
    ),
    "ARB-07": _node(
        "tests/test_relationship_semantic_concurrency.py",
        "test_arb_07a_late_delete_cannot_remove_recreated_fact",
        "test_arb_07b_winner_disappears_before_fresh_convergence_read",
    ),
    "REF-01": (
        *_node(
            "tests/test_object_semantic_concurrency.py",
            "test_ref_01_object_exact_otv_fk_both_directions",
        ),
        *_node(
            "tests/test_objecttemplate_semantic_concurrency.py",
            "test_ref_01_property_reference_creation_blocks_datatype_delete",
            "test_ref_01_component_reference_creation_blocks_target_delete",
            "test_ref_01_target_delete_winner_rejects_component_reference",
        ),
        *_node(
            "tests/test_relationshipdefinition_semantic_concurrency.py",
            "test_ref_01_definition_create_then_lineage_delete_uses_fk_lifetime",
            "test_ref_01_lineage_delete_then_definition_create_fails_reference",
        ),
    ),
    "REF-02": _node(
        "tests/test_object_semantic_concurrency.py",
        "test_ref_02_attach_and_object_delete_arbitrate_both_lifetime_orders",
    ),
    "REF-03": _node(
        "tests/test_relationship_semantic_concurrency.py",
        "test_ref_03_and_ref_05_relationship_object_lifetime_arbitration",
    ),
    "REF-04": _node(
        "tests/test_relationship_semantic_concurrency.py",
        "test_ref_04_create_reference_first_blocks_definition_delete",
        "test_ref_04_definition_delete_first_rejects_relationship_create",
    ),
    "REF-05": (
        *_node(
            "tests/test_object_semantic_concurrency.py",
            "test_ref_05_detach_removes_final_object_delete_blocker",
        ),
        *_node(
            "tests/test_relationship_semantic_concurrency.py",
            "test_ref_03_and_ref_05_relationship_object_lifetime_arbitration",
        ),
    ),
    "REF-06": (
        *_node(
            "tests/test_datatype_semantic_concurrency.py",
            "test_ref_06a_datatype_cascade_loses_to_external_property_restrict",
        ),
        *_node(
            "tests/test_objecttemplate_semantic_concurrency.py",
            "test_ref_06b_object_template_cascade_loses_to_object_restrict",
        ),
        *_node(
            "tests/test_relationship_semantic_concurrency.py",
            "test_ref_06c_definition_cascade_loses_to_relationship_restrict",
        ),
    ),
    "GATE-01": _node(
        "tests/test_object_semantic_concurrency.py",
        "test_gate_01_opposite_attach_uses_fresh_protected_graph",
    ),
    "GATE-02": _node(
        "tests/test_object_semantic_concurrency.py",
        "test_gate_02a_rejects_longer_cycle_without_mutating_graph",
        "test_gate_02b_attach_sees_concurrent_detach_before_cycle_check",
    ),
    "GATE-03": _node(
        "tests/test_object_semantic_concurrency.py",
        "test_gate_01_opposite_attach_uses_fresh_protected_graph",
        "test_arb_02_and_gate_03_same_child_reread_after_gate",
    ),
    "GATE-04": _node(
        "tests/test_relationshipdefinition_semantic_concurrency.py",
        "test_gate_04a_and_gate_06a_equivalent_create_reads_fresh_set",
        "test_gate_04b_conflicting_create_commits_only_one_candidate",
    ),
    "GATE-05": _node(
        "tests/test_relationshipdefinition_semantic_concurrency.py",
        "test_gate_05a_create_and_rename_preserve_conflict_free_set",
        "test_gate_05b_different_definition_renames_serialize_globally",
    ),
    "GATE-06": _node(
        "tests/test_relationshipdefinition_semantic_concurrency.py",
        "test_gate_04a_and_gate_06a_equivalent_create_reads_fresh_set",
        "test_gate_06b_delete_commits_while_candidate_waits_then_unblocks_it",
    ),
    "SNAP-01": _node(
        "tests/test_relationship_semantic_concurrency.py",
        "test_snap_01_delete_event_keeps_one_pre_rename_name_snapshot",
        "test_par_02_and_snap_01_create_progresses_during_definition_rename",
    ),
    "SNAP-02": _node(
        "tests/test_relationship_semantic_concurrency.py",
        "test_snap_02_delete_event_keeps_one_pre_rename_object_snapshot",
        "test_par_01_and_snap_02_create_progresses_during_object_rename",
    ),
    "SNAP-03": _node(
        "tests/test_relationship_semantic_concurrency.py",
        "test_snap_03_create_observes_one_real_two_endpoint_name_generation",
    ),
    "SNAP-04": _node(
        "tests/test_object_semantic_concurrency.py",
        "test_snap_04_child_rename_progresses_during_attach_parent_hold",
    ),
    "ATOMIC-01": _node(
        "tests/test_objecttemplate_semantic_concurrency.py",
        "test_atomic_01_failed_multirow_revise_rolls_back_complete_generation",
    ),
    "ATOMIC-02": _node(
        "tests/test_relationship_semantic_concurrency.py",
        "test_atomic_02_later_closure_pk_collision_rolls_back_candidate",
    ),
    "ATOMIC-03": _node(
        "tests/test_relationship_semantic_concurrency.py",
        "test_atomic_03_delete_event_failure_rolls_back_complete_fact",
    ),
    "ATOMIC-04": (
        *_node(
            "tests/test_object_api.py",
            "test_intrinsic_state_event_atomic_rollback",
            "test_s05_ownership_failures_cycle_and_atomic_event",
        ),
        *_node(
            "tests/test_relationshipdefinition_semantic_concurrency.py",
            "test_atomic_04c_rename_rollback_and_symmetric_two_row_update",
        ),
    ),
    "PAR-01": _node(
        "tests/test_relationship_semantic_concurrency.py",
        "test_par_01_and_snap_02_create_progresses_during_object_rename",
    ),
    "PAR-02": _node(
        "tests/test_relationship_semantic_concurrency.py",
        "test_par_02_and_snap_01_create_progresses_during_definition_rename",
    ),
    "PAR-03": _node(
        "tests/test_object_semantic_concurrency.py",
        "test_par_03_parent_rename_and_attach_share_non_key_owner",
    ),
    "PAR-04": _node(
        "tests/test_object_semantic_concurrency.py",
        "test_par_04_unrelated_real_attaches_share_global_gate",
    ),
    "PAR-05": _node(
        "tests/test_relationship_semantic_concurrency.py",
        "test_par_05_unrelated_relationship_creates_have_no_global_gate",
    ),
    "PAR-06": _node(
        "tests/test_datatype_semantic_concurrency.py",
        "test_par_06_distinct_deprecations_make_semantic_progress",
    ),
    "PAR-07": _node(
        "tests/test_datatype_semantic_concurrency.py",
        "test_par_07a_description_and_set_default_intentionally_contend",
        "test_par_07b_description_and_revise_make_independent_progress",
    ),
}


SAFETY_PREDICATES: dict[str, frozenset[str]] = {
    "NU": frozenset({"ARB-01"}),
    "VS": frozenset({"ROW-01", "ROW-02"}),
    "DG": frozenset({"ROW-03", "ROW-04", "ATOMIC-01"}),
    "LS": frozenset({"ROW-04", "ROW-06"}),
    "DV": frozenset({"ROW-05", "ROW-06", "ROW-08"}),
    "BA": frozenset({"ROW-07", "ROW-08", "ROW-12"}),
    "AM": frozenset({"ROW-09", "ROW-10"}),
    "RL": frozenset({f"REF-{number:02d}" for number in range(1, 7)}),
    "AL": frozenset({"ROW-16", "ROW-17"}),
    "ML": frozenset({"ROW-15"}),
    "OS": frozenset({"ROW-11", "ROW-12", "ATOMIC-04"}),
    "PO": frozenset({"ROW-13", "ROW-14"}),
    "OF": frozenset({"ARB-03", "ARB-04", "ATOMIC-04"}),
    "SO": frozenset({"ARB-02"}),
    "OC": frozenset({"GATE-01", "GATE-02", "GATE-03", "PAR-04"}),
    "RC": frozenset({"GATE-04", "GATE-05", "GATE-06", "ATOMIC-04"}),
    "RF": frozenset({"ARB-05", "ARB-07", "ATOMIC-02"}),
    "RA": frozenset({"ARB-06", "ARB-07", "ATOMIC-03"}),
    "ES": frozenset({"SNAP-01", "SNAP-02", "SNAP-03", "PAR-01", "PAR-02"}),
}


def _expected_scenarios() -> set[str]:
    families = {
        "ROW": 17,
        "ARB": 7,
        "REF": 6,
        "GATE": 6,
        "SNAP": 4,
        "ATOMIC": 4,
        "PAR": 7,
    }
    return {
        f"{family}-{number:02d}"
        for family, count in families.items()
        for number in range(1, count + 1)
    }


def _dotted_name(expression: ast.expr) -> str | None:
    if isinstance(expression, ast.Name):
        return expression.id
    if isinstance(expression, ast.Attribute):
        parent = _dotted_name(expression.value)
        return f"{parent}.{expression.attr}" if parent is not None else None
    if isinstance(expression, ast.Call):
        return _dotted_name(expression.func)
    return None


def _pytest_functions(module: Path) -> dict[str, set[str]]:
    tree = ast.parse(module.read_text(), filename=str(module))
    functions: dict[str, set[str]] = {}
    for statement in tree.body:
        if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef):
            functions[statement.name] = {
                name
                for decorator in statement.decorator_list
                if (name := _dotted_name(decorator)) is not None
            }
    return functions


def test_canonical_pgtest_registry_is_exact() -> None:
    expected = _expected_scenarios()
    assert len(expected) == 51
    assert set(PGTEST_SCENARIOS) == expected
    assert all(PGTEST_SCENARIOS[scenario] for scenario in expected)


def test_canonical_pgtest_targets_exist_and_require_real_postgresql() -> None:
    discovered: dict[str, dict[str, set[str]]] = {}
    for targets in PGTEST_SCENARIOS.values():
        for target in targets:
            functions = discovered.setdefault(
                target.module, _pytest_functions(ROOT / target.module)
            )
            assert target.function in functions, target
            assert "pytest.mark.postgresql" in functions[target.function], target


def test_non_i_safety_predicate_registry_is_exact_and_closed() -> None:
    expected_predicates = {
        "NU",
        "VS",
        "DG",
        "LS",
        "DV",
        "BA",
        "AM",
        "RL",
        "AL",
        "ML",
        "OS",
        "PO",
        "OF",
        "SO",
        "OC",
        "RC",
        "RF",
        "RA",
        "ES",
    }
    assert len(expected_predicates) == 19
    assert set(SAFETY_PREDICATES) == expected_predicates
    assert all(SAFETY_PREDICATES[predicate] for predicate in expected_predicates)
    assert set().union(*SAFETY_PREDICATES.values()) <= set(PGTEST_SCENARIOS)
